"""Canvas Studio API server — FastAPI replacement for server.js.

Same routes, same wire shape, same Postgres on :5440. Drop-in
behaviour: the Vite proxy at /api → :5174 keeps working.

Endpoints

  Books            POST/GET/DELETE /api/books, /api/books/{key}
  Templates        GET/POST/DELETE /api/templates, /api/templates/{key}
  Characters       GET/POST/DELETE /api/characters, /api/characters/{key}
  Generation       POST/GET /api/generation-attempts,
                   PATCH    /api/generation-attempts/{id}/verdict
  Layout versions  POST/GET /api/layout-versions
  Image gen        POST     /api/generate/image
  Image edit       POST     /api/generate/edit
  LLM chat         POST     /api/llm/chat   (OpenAI-compat, backed by Anthropic)

  Assets           GET/POST /api/assets
                   GET/PUT/DELETE /api/assets/{asset_id}
                   POST     /api/assets/{asset_id}/generate-sheet
  Page templates   GET/POST /api/page-templates
                   GET/PUT/DELETE /api/page-templates/{template_id}
  Page layers      GET/POST /api/page-templates/{template_id}/layers
                   PUT/DELETE /api/page-templates/{template_id}/layers/{layer_id}
                   POST     /api/page-templates/{template_id}/layers/{layer_id}/generate
  Preview          GET      /api/page-templates/{template_id}/preview
  Personalize      POST     /api/page-templates/{template_id}/personalize
  Finalize         POST     /api/finalize

  Lulu print       Proxy:    /api/print/* → LULU_SERVICE_URL
  Export           POST     /api/export → export_book.py (subprocess)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import httpx
import psycopg
import psycopg_pool
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

# ── Config ──────────────────────────────────────────────────────

DB_DSN = (
    f"host={os.environ.get('DB_HOST', '127.0.0.1')} "
    f"port={os.environ.get('DB_PORT', '5440')} "
    f"user={os.environ.get('DB_USER', 'coinswarm')} "
    f"password={os.environ.get('DB_PASSWORD', 'coinswarm_dev_2024')} "
    f"dbname={os.environ.get('DB_NAME', 'canvas_studio')}"
)
LULU_SERVICE_URL = os.environ.get("LULU_SERVICE_URL", "http://localhost:8260")
PORT = int(os.environ.get("PORT", "5174"))
EXPORT_SCRIPT = Path(__file__).parent / "export_book.py"

_KEY_PATTERN = re.compile(r"[^a-zA-Z0-9_-]")

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS books (
    key TEXT PRIMARY KEY,
    data JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS characters (
    key TEXT PRIMARY KEY,
    data JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS templates (
    key TEXT PRIMARY KEY,
    data JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS generation_attempts (
    id SERIAL PRIMARY KEY,
    book_key TEXT NOT NULL,
    scene_id TEXT NOT NULL,
    layer_id TEXT NOT NULL,
    attempt_type TEXT NOT NULL,
    prompt TEXT NOT NULL DEFAULT '',
    model_id TEXT,
    quality TEXT NOT NULL DEFAULT 'draft',
    verdict TEXT NOT NULL DEFAULT 'pending',
    data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS page_layout_versions (
    id SERIAL PRIMARY KEY,
    book_key TEXT NOT NULL,
    scene_id TEXT NOT NULL,
    version INT NOT NULL,
    layout JSONB NOT NULL DEFAULT '{}',
    diff JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS asset_sheets (
    id SERIAL PRIMARY KEY,
    book_key TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('character', 'setting', 'prop')),
    name TEXT NOT NULL DEFAULT '',
    reference_photos JSONB NOT NULL DEFAULT '[]',
    sheet_image TEXT,
    lora_name TEXT,
    ip_adapter_weight REAL NOT NULL DEFAULT 0.8,
    prompt_description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (book_key, asset_id)
);
CREATE TABLE IF NOT EXISTS page_templates (
    id SERIAL PRIMARY KEY,
    book_key TEXT NOT NULL,
    page_number INT NOT NULL,
    scene_id TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    layout JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (book_key, page_number)
);
CREATE TABLE IF NOT EXISTS page_layers (
    id SERIAL PRIMARY KEY,
    template_id INT NOT NULL REFERENCES page_templates(id) ON DELETE CASCADE,
    book_key TEXT NOT NULL,
    page_number INT NOT NULL,
    layer_kind TEXT NOT NULL CHECK (layer_kind IN ('background', 'character', 'text')),
    z_index INT NOT NULL DEFAULT 0,
    asset_id TEXT,
    prompt TEXT NOT NULL DEFAULT '',
    negative_prompt TEXT NOT NULL DEFAULT '',
    ip_adapter_refs JSONB NOT NULL DEFAULT '[]',
    loras JSONB NOT NULL DEFAULT '[]',
    controlnet_pose JSONB,
    size TEXT NOT NULL DEFAULT '1024x1024',
    quality TEXT NOT NULL DEFAULT 'draft',
    seed INT,
    image_url TEXT,
    history JSONB NOT NULL DEFAULT '[]',
    slot JSONB,
    text_config JSONB,
    is_personalizable BOOLEAN NOT NULL DEFAULT FALSE,
    personalization_slot TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS finalized_pages (
    id SERIAL PRIMARY KEY,
    book_key TEXT NOT NULL,
    page_number INT NOT NULL,
    customer_id TEXT NOT NULL DEFAULT '',
    template_id INT,
    composite_url TEXT NOT NULL,
    pdf_ready BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (book_key, page_number, customer_id)
);
"""


def safe_key(key: str | None) -> str:
    return _KEY_PATTERN.sub("_", key or "untitled")[:80]


# ── App lifecycle ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    pool = psycopg_pool.AsyncConnectionPool(DB_DSN, open=False, max_size=10)
    await pool.open()
    async with pool.connection() as conn:
        await conn.execute(_INIT_SQL)
    app.state.pool = pool
    app.state.http = httpx.AsyncClient(timeout=30.0)
    try:
        yield
    finally:
        await pool.close()
        await app.state.http.aclose()


app = FastAPI(title="Canvas Studio API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────


async def db_execute(app: FastAPI, query: str, params: tuple = ()) -> None:
    async with app.state.pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(query, params)


async def db_fetchall(
    app: FastAPI, query: str, params: tuple = ()
) -> list[dict[str, Any]]:
    async with app.state.pool.connection() as conn, conn.cursor(
        row_factory=psycopg.rows.dict_row
    ) as cur:
        await cur.execute(query, params)
        return await cur.fetchall()


async def db_fetchone(
    app: FastAPI, query: str, params: tuple = ()
) -> dict[str, Any] | None:
    async with app.state.pool.connection() as conn, conn.cursor(
        row_factory=psycopg.rows.dict_row
    ) as cur:
        await cur.execute(query, params)
        return await cur.fetchone()


# ── Books ──────────────────────────────────────────────────────────


@app.post("/api/books/{key}")
async def save_book(key: str, request: Request) -> dict[str, Any]:
    payload = await request.json()
    saved_at = _now_iso()
    payload = {**payload, "savedAt": saved_at}
    safe = safe_key(key)
    await db_execute(
        app,
        """
        INSERT INTO books (key, data, updated_at)
        VALUES (%s, %s, now())
        ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, updated_at = now()
        """,
        (safe, json.dumps(payload)),
    )
    return {"ok": True, "savedAt": saved_at}


@app.get("/api/books/{key}")
async def get_book(key: str) -> Any:
    row = await db_fetchone(
        app, "SELECT data FROM books WHERE key = %s", (safe_key(key),)
    )
    if row is None:
        raise HTTPException(404, {"error": "not found"})
    return row["data"]


@app.get("/api/books")
async def list_books() -> list[dict[str, Any]]:
    rows = await db_fetchall(
        app,
        """
        SELECT key,
               data->>'savedAt' AS saved_at,
               data->>'step'    AS step,
               data->'bookSpec'->>'title'   AS title,
               data->'bookSpec'->>'premise' AS premise
        FROM books
        ORDER BY updated_at DESC
        """,
    )
    return [
        {
            "key": r["key"],
            "title": r["title"] or (r["premise"] or "")[:40] or r["key"],
            "step": r["step"],
            "bookSpec": {"title": r["title"], "premise": r["premise"]},
            "savedAt": r["saved_at"],
        }
        for r in rows
    ]


@app.delete("/api/books/{key}")
async def delete_book(key: str) -> dict[str, bool]:
    await db_execute(app, "DELETE FROM books WHERE key = %s", (safe_key(key),))
    return {"ok": True}


@app.delete("/api/books")
async def truncate_books() -> dict[str, bool]:
    await db_execute(app, "TRUNCATE books")
    return {"ok": True}


# ── Templates ────────────────────────────────────────────────────────


@app.get("/api/templates")
async def list_templates() -> list[dict[str, Any]]:
    rows = await db_fetchall(
        app, "SELECT key, data FROM templates ORDER BY updated_at DESC"
    )
    return [{"key": r["key"], **(r["data"] or {})} for r in rows]


@app.post("/api/templates/{key}")
async def save_template(key: str, request: Request) -> dict[str, bool]:
    payload = await request.json()
    await db_execute(
        app,
        """
        INSERT INTO templates (key, data, updated_at)
        VALUES (%s, %s, now())
        ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, updated_at = now()
        """,
        (safe_key(key), json.dumps(payload)),
    )
    return {"ok": True}


@app.delete("/api/templates/{key}")
async def delete_template(key: str) -> dict[str, bool]:
    await db_execute(
        app, "DELETE FROM templates WHERE key = %s", (safe_key(key),)
    )
    return {"ok": True}


# ── Characters ────────────────────────────────────────────────────────


@app.get("/api/characters")
async def list_characters() -> list[dict[str, Any]]:
    rows = await db_fetchall(
        app, "SELECT key, data FROM characters ORDER BY updated_at DESC"
    )
    return [{"key": r["key"], **(r["data"] or {})} for r in rows]


@app.get("/api/characters/{key}")
async def get_character(key: str) -> Any:
    row = await db_fetchone(
        app, "SELECT data FROM characters WHERE key = %s", (safe_key(key),)
    )
    if row is None:
        raise HTTPException(404, {"error": "not found"})
    return row["data"]


@app.post("/api/characters/{key}")
async def save_character(key: str, request: Request) -> dict[str, bool]:
    body = await request.json()
    payload = {**body, "savedAt": _now_iso()}
    await db_execute(
        app,
        """
        INSERT INTO characters (key, data, updated_at)
        VALUES (%s, %s, now())
        ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, updated_at = now()
        """,
        (safe_key(key), json.dumps(payload)),
    )
    return {"ok": True}


@app.delete("/api/characters/{key}")
async def delete_character(key: str) -> dict[str, bool]:
    await db_execute(
        app, "DELETE FROM characters WHERE key = %s", (safe_key(key),)
    )
    return {"ok": True}


# ── Generation attempts (training data) ─────────────────────────────────


@app.post("/api/generation-attempts")
async def create_generation_attempt(request: Request) -> dict[str, Any]:
    body = await request.json()
    required = ("book_key", "scene_id", "layer_id", "attempt_type")
    if not all(body.get(k) for k in required):
        raise HTTPException(
            400, {"error": "book_key, scene_id, layer_id, attempt_type required"}
        )
    row = await db_fetchone(
        app,
        """
        INSERT INTO generation_attempts (
            book_key, scene_id, layer_id, attempt_type,
            prompt, model_id, quality, verdict, data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
        """,
        (
            body["book_key"],
            body["scene_id"],
            body["layer_id"],
            body["attempt_type"],
            body.get("prompt", ""),
            body.get("model_id"),
            body.get("quality", "draft"),
            body.get("verdict", "pending"),
            json.dumps(body.get("data", {})),
        ),
    )
    assert row is not None
    return {
        "ok": True,
        "id": row["id"],
        "created_at": row["created_at"].isoformat()
        if hasattr(row["created_at"], "isoformat")
        else row["created_at"],
    }


@app.patch("/api/generation-attempts/{attempt_id}/verdict")
async def update_attempt_verdict(attempt_id: int, request: Request) -> dict[str, Any]:
    body = await request.json()
    verdict = body.get("verdict")
    if not verdict:
        raise HTTPException(400, {"error": "verdict required"})
    async with app.state.pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "UPDATE generation_attempts SET verdict = %s WHERE id = %s",
            (verdict, attempt_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, {"error": "not found"})
    return {"ok": True}


@app.get("/api/generation-attempts")
async def list_generation_attempts(
    book_key: str | None = Query(None),
    scene_id: str | None = Query(None),
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if book_key:
        params.append(book_key)
        clauses.append("book_key = %s")
    if scene_id:
        params.append(scene_id)
        clauses.append("scene_id = %s")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = await db_fetchall(
        app,
        f"""
        SELECT id, book_key, scene_id, layer_id, attempt_type,
               prompt, model_id, quality, verdict, created_at
        FROM generation_attempts {where}
        ORDER BY id DESC LIMIT 500
        """,
        tuple(params),
    )
    return [_isoize(r) for r in rows]


# ── Page layout versions (training data) ────────────────────────────────


@app.post("/api/layout-versions")
async def create_layout_version(request: Request) -> dict[str, Any]:
    body = await request.json()
    if not all(body.get(k) for k in ("book_key", "scene_id", "layout")):
        raise HTTPException(400, {"error": "book_key, scene_id, layout required"})
    prev = await db_fetchone(
        app,
        """
        SELECT version FROM page_layout_versions
        WHERE book_key = %s AND scene_id = %s
        ORDER BY version DESC LIMIT 1
        """,
        (body["book_key"], body["scene_id"]),
    )
    version = (prev["version"] + 1) if prev else 1
    row = await db_fetchone(
        app,
        """
        INSERT INTO page_layout_versions
            (book_key, scene_id, version, layout, diff)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, version, created_at
        """,
        (
            body["book_key"],
            body["scene_id"],
            version,
            json.dumps(body["layout"]),
            json.dumps(body["diff"]) if body.get("diff") is not None else None,
        ),
    )
    assert row is not None
    return {
        "ok": True,
        "id": row["id"],
        "version": row["version"],
        "created_at": row["created_at"].isoformat()
        if hasattr(row["created_at"], "isoformat")
        else row["created_at"],
    }


@app.get("/api/layout-versions")
async def list_layout_versions(
    book_key: str | None = Query(None),
    scene_id: str | None = Query(None),
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if book_key:
        params.append(book_key)
        clauses.append("book_key = %s")
    if scene_id:
        params.append(scene_id)
        clauses.append("scene_id = %s")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = await db_fetchall(
        app,
        f"""
        SELECT id, book_key, scene_id, version, layout, diff, created_at
        FROM page_layout_versions {where}
        ORDER BY id DESC LIMIT 200
        """,
        tuple(params),
    )
    return [_isoize(r) for r in rows]


# ── Image generation (ComfyUI + Diffusers backend) ────────────────────


@app.post("/api/generate/image")
async def api_generate_image(request: Request) -> dict[str, Any]:
    body = await request.json()
    prompt = body.get("prompt", "")
    if not prompt:
        raise HTTPException(400, {"error": "prompt required"})
    from engine.image_provider import generate_image as _gen
    data_url = await _gen(
        prompt,
        size=body.get("size", "1024x1024"),
        quality=body.get("quality", "low"),
    )
    return {"data_url": data_url}


@app.post("/api/generate/edit")
async def api_generate_edit(request: Request) -> dict[str, Any]:
    body = await request.json()
    prompt = body.get("prompt", "")
    if not prompt:
        raise HTTPException(400, {"error": "prompt required"})
    image_data_urls = body.get("image_data_urls", [])
    from engine.image_provider import image_edit as _edit
    data_url = await _edit(
        image_data_urls,
        prompt,
        size=body.get("size", "1024x1024"),
        quality=body.get("quality", "medium"),
        input_fidelity=body.get("input_fidelity", "high"),
    )
    return {"data_url": data_url}


# ── LLM chat (OpenAI-compat, backed by Anthropic) ───────────────────────

_MODEL_MAP: dict[str, str] = {
    "gemini-flash": "claude-haiku-4-5-20251001",
    "gemini-2.0-flash": "claude-haiku-4-5-20251001",
    "gemini-pro": "claude-sonnet-4-6",
    "gpt-4o-mini": "claude-haiku-4-5-20251001",
    "gpt-4o": "claude-sonnet-4-6",
}


@app.post("/api/llm/chat")
async def llm_chat(request: Request) -> dict[str, Any]:
    """OpenAI-compatible chat endpoint backed by Anthropic."""
    body = await request.json()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(500, {"error": "ANTHROPIC_API_KEY not configured"})

    raw_model = body.get("model", "gemini-flash")
    model = _MODEL_MAP.get(
        raw_model,
        raw_model if raw_model.startswith("claude") else "claude-haiku-4-5-20251001",
    )

    messages: list[dict[str, Any]] = body.get("messages", [])
    system_texts = [m["content"] for m in messages if m.get("role") == "system"]
    chat_messages = [m for m in messages if m.get("role") != "system"]

    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": min(int(body.get("max_tokens", 16000)), 16000),
        "messages": chat_messages,
    }
    if system_texts:
        payload["system"] = "\n\n".join(system_texts)

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )

    if resp.status_code != 200:
        try:
            err = resp.json().get("error", {})
        except Exception:
            err = {}
        raise HTTPException(
            502,
            {"error": err.get("message") or f"Anthropic returned {resp.status_code}"},
        )

    data = resp.json()
    text = next(
        (c["text"] for c in data.get("content", []) if c.get("type") == "text"), ""
    )
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


# ── Asset sheets ──────────────────────────────────────────────────────


@app.get("/api/assets")
async def list_assets(book_key: str = Query(...)) -> list[dict[str, Any]]:
    rows = await db_fetchall(
        app,
        "SELECT * FROM asset_sheets WHERE book_key = %s ORDER BY id",
        (book_key,),
    )
    return [_isoize(r) for r in rows]


@app.post("/api/assets")
async def create_asset(request: Request) -> dict[str, Any]:
    body = await request.json()
    if not all(body.get(k) for k in ("book_key", "asset_id", "kind", "name")):
        raise HTTPException(400, {"error": "book_key, asset_id, kind, name required"})
    row = await db_fetchone(
        app,
        """
        INSERT INTO asset_sheets
            (book_key, asset_id, kind, name, reference_photos,
             lora_name, ip_adapter_weight, prompt_description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (book_key, asset_id) DO UPDATE
            SET name               = EXCLUDED.name,
                kind               = EXCLUDED.kind,
                reference_photos   = EXCLUDED.reference_photos,
                lora_name          = EXCLUDED.lora_name,
                ip_adapter_weight  = EXCLUDED.ip_adapter_weight,
                prompt_description = EXCLUDED.prompt_description,
                updated_at         = now()
        RETURNING *
        """,
        (
            body["book_key"],
            body["asset_id"],
            body["kind"],
            body["name"],
            json.dumps(body.get("reference_photos", [])),
            body.get("lora_name"),
            body.get("ip_adapter_weight", 0.8),
            body.get("prompt_description"),
        ),
    )
    assert row is not None
    return _isoize(row)


@app.get("/api/assets/{asset_id}")
async def get_asset(asset_id: str, book_key: str = Query(...)) -> dict[str, Any]:
    row = await db_fetchone(
        app,
        "SELECT * FROM asset_sheets WHERE book_key = %s AND asset_id = %s",
        (book_key, asset_id),
    )
    if row is None:
        raise HTTPException(404, {"error": "asset not found"})
    return _isoize(row)


@app.put("/api/assets/{asset_id}")
async def update_asset(asset_id: str, request: Request) -> dict[str, Any]:
    body = await request.json()
    book_key = body.get("book_key")
    if not book_key:
        raise HTTPException(400, {"error": "book_key required"})
    row = await db_fetchone(
        app,
        """
        UPDATE asset_sheets
        SET name               = COALESCE(%s, name),
            reference_photos   = COALESCE(%s::jsonb, reference_photos),
            lora_name          = COALESCE(%s, lora_name),
            ip_adapter_weight  = COALESCE(%s, ip_adapter_weight),
            prompt_description = COALESCE(%s, prompt_description),
            sheet_image        = COALESCE(%s, sheet_image),
            updated_at         = now()
        WHERE book_key = %s AND asset_id = %s
        RETURNING *
        """,
        (
            body.get("name"),
            json.dumps(body["reference_photos"]) if "reference_photos" in body else None,
            body.get("lora_name"),
            body.get("ip_adapter_weight"),
            body.get("prompt_description"),
            body.get("sheet_image"),
            book_key,
            asset_id,
        ),
    )
    if row is None:
        raise HTTPException(404, {"error": "asset not found"})
    return _isoize(row)


@app.delete("/api/assets/{asset_id}")
async def delete_asset(
    asset_id: str, book_key: str = Query(...)
) -> dict[str, bool]:
    await db_execute(
        app,
        "DELETE FROM asset_sheets WHERE book_key = %s AND asset_id = %s",
        (book_key, asset_id),
    )
    return {"ok": True}


@app.post("/api/assets/{asset_id}/generate-sheet")
async def generate_asset_sheet(asset_id: str, request: Request) -> dict[str, Any]:
    """Generate (or regenerate) the reference sheet image for an asset."""
    body = await request.json()
    book_key = body.get("book_key")
    if not book_key:
        raise HTTPException(400, {"error": "book_key required"})

    asset = await db_fetchone(
        app,
        "SELECT * FROM asset_sheets WHERE book_key = %s AND asset_id = %s",
        (book_key, asset_id),
    )
    if asset is None:
        raise HTTPException(404, {"error": "asset not found"})

    from engine.generation import LayerGenerationRequest, generate_layer

    is_setting = asset["kind"] == "setting"
    req = LayerGenerationRequest(
        layer_kind="background" if is_setting else "character",
        prompt=asset.get("prompt_description") or f"Reference sheet for {asset['name']}",
        remove_background=not is_setting,
        size=body.get("size", "1024x1024"),
        quality=body.get("quality", "standard"),
    )

    ref_photos = asset.get("reference_photos") or []
    if ref_photos:
        from engine.image_provider import image_edit
        data_url = await image_edit(
            ref_photos,
            req.prompt,
            size=req.size,
            quality=req.quality,
            input_fidelity="high",
        )
    else:
        result = await generate_layer(req)
        data_url = result.data_url

    updated = await db_fetchone(
        app,
        """
        UPDATE asset_sheets SET sheet_image = %s, updated_at = now()
        WHERE book_key = %s AND asset_id = %s RETURNING *
        """,
        (data_url, book_key, asset_id),
    )
    assert updated is not None
    return _isoize(updated)


# ── Page templates ─────────────────────────────────────────────────────


@app.get("/api/page-templates")
async def list_page_templates(book_key: str = Query(...)) -> list[dict[str, Any]]:
    rows = await db_fetchall(
        app,
        "SELECT * FROM page_templates WHERE book_key = %s ORDER BY page_number",
        (book_key,),
    )
    return [_isoize(r) for r in rows]


@app.post("/api/page-templates")
async def create_page_template(request: Request) -> dict[str, Any]:
    body = await request.json()
    if not all(body.get(k) for k in ("book_key", "page_number")):
        raise HTTPException(400, {"error": "book_key, page_number required"})
    row = await db_fetchone(
        app,
        """
        INSERT INTO page_templates (book_key, page_number, scene_id, status, layout)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (book_key, page_number) DO UPDATE
            SET scene_id   = EXCLUDED.scene_id,
                status     = EXCLUDED.status,
                layout     = EXCLUDED.layout,
                updated_at = now()
        RETURNING *
        """,
        (
            body["book_key"],
            int(body["page_number"]),
            body.get("scene_id"),
            body.get("status", "draft"),
            json.dumps(body.get("layout", {})),
        ),
    )
    assert row is not None
    return _isoize(row)


@app.get("/api/page-templates/{template_id}")
async def get_page_template(template_id: int) -> dict[str, Any]:
    row = await db_fetchone(
        app, "SELECT * FROM page_templates WHERE id = %s", (template_id,)
    )
    if row is None:
        raise HTTPException(404, {"error": "template not found"})
    return _isoize(row)


@app.put("/api/page-templates/{template_id}")
async def update_page_template(
    template_id: int, request: Request
) -> dict[str, Any]:
    body = await request.json()
    row = await db_fetchone(
        app,
        """
        UPDATE page_templates
        SET scene_id   = COALESCE(%s, scene_id),
            status     = COALESCE(%s, status),
            layout     = COALESCE(%s::jsonb, layout),
            updated_at = now()
        WHERE id = %s
        RETURNING *
        """,
        (
            body.get("scene_id"),
            body.get("status"),
            json.dumps(body["layout"]) if "layout" in body else None,
            template_id,
        ),
    )
    if row is None:
        raise HTTPException(404, {"error": "template not found"})
    return _isoize(row)


@app.delete("/api/page-templates/{template_id}")
async def delete_page_template(template_id: int) -> dict[str, bool]:
    await db_execute(
        app, "DELETE FROM page_templates WHERE id = %s", (template_id,)
    )
    return {"ok": True}


# ── Page layers ────────────────────────────────────────────────────────


@app.get("/api/page-templates/{template_id}/layers")
async def list_page_layers(template_id: int) -> list[dict[str, Any]]:
    rows = await db_fetchall(
        app,
        "SELECT * FROM page_layers WHERE template_id = %s ORDER BY z_index",
        (template_id,),
    )
    return [_isoize(r) for r in rows]


@app.post("/api/page-templates/{template_id}/layers")
async def create_page_layer(
    template_id: int, request: Request
) -> dict[str, Any]:
    tmpl = await db_fetchone(
        app, "SELECT * FROM page_templates WHERE id = %s", (template_id,)
    )
    if tmpl is None:
        raise HTTPException(404, {"error": "template not found"})
    body = await request.json()
    if not body.get("layer_kind"):
        raise HTTPException(400, {"error": "layer_kind required"})
    row = await db_fetchone(
        app,
        """
        INSERT INTO page_layers
            (template_id, book_key, page_number, layer_kind, z_index,
             asset_id, prompt, negative_prompt, ip_adapter_refs, loras,
             controlnet_pose, size, quality, seed, slot, text_config,
             is_personalizable, personalization_slot)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING *
        """,
        (
            template_id,
            tmpl["book_key"],
            tmpl["page_number"],
            body["layer_kind"],
            body.get("z_index", 0),
            body.get("asset_id"),
            body.get("prompt", ""),
            body.get("negative_prompt", ""),
            json.dumps(body.get("ip_adapter_refs", [])),
            json.dumps(body.get("loras", [])),
            json.dumps(body["controlnet_pose"]) if body.get("controlnet_pose") else None,
            body.get("size", "1024x1024"),
            body.get("quality", "draft"),
            body.get("seed"),
            json.dumps(body["slot"]) if body.get("slot") is not None else None,
            json.dumps(body["text_config"]) if body.get("text_config") else None,
            bool(body.get("is_personalizable", False)),
            body.get("personalization_slot"),
        ),
    )
    assert row is not None
    return _isoize(row)


@app.put("/api/page-templates/{template_id}/layers/{layer_id}")
async def update_page_layer(
    template_id: int, layer_id: int, request: Request
) -> dict[str, Any]:
    body = await request.json()
    row = await db_fetchone(
        app,
        """
        UPDATE page_layers
        SET z_index              = COALESCE(%s, z_index),
            prompt               = COALESCE(%s, prompt),
            negative_prompt      = COALESCE(%s, negative_prompt),
            ip_adapter_refs      = COALESCE(%s::jsonb, ip_adapter_refs),
            loras                = COALESCE(%s::jsonb, loras),
            controlnet_pose      = COALESCE(%s::jsonb, controlnet_pose),
            size                 = COALESCE(%s, size),
            quality              = COALESCE(%s, quality),
            seed                 = COALESCE(%s, seed),
            image_url            = COALESCE(%s, image_url),
            slot                 = COALESCE(%s::jsonb, slot),
            text_config          = COALESCE(%s::jsonb, text_config),
            is_personalizable    = COALESCE(%s, is_personalizable),
            personalization_slot = COALESCE(%s, personalization_slot),
            updated_at           = now()
        WHERE id = %s AND template_id = %s
        RETURNING *
        """,
        (
            body.get("z_index"),
            body.get("prompt"),
            body.get("negative_prompt"),
            json.dumps(body["ip_adapter_refs"]) if "ip_adapter_refs" in body else None,
            json.dumps(body["loras"]) if "loras" in body else None,
            json.dumps(body["controlnet_pose"]) if "controlnet_pose" in body else None,
            body.get("size"),
            body.get("quality"),
            body.get("seed"),
            body.get("image_url"),
            json.dumps(body["slot"]) if "slot" in body else None,
            json.dumps(body["text_config"]) if "text_config" in body else None,
            body.get("is_personalizable"),
            body.get("personalization_slot"),
            layer_id,
            template_id,
        ),
    )
    if row is None:
        raise HTTPException(404, {"error": "layer not found"})
    return _isoize(row)


@app.delete("/api/page-templates/{template_id}/layers/{layer_id}")
async def delete_page_layer(template_id: int, layer_id: int) -> dict[str, bool]:
    await db_execute(
        app,
        "DELETE FROM page_layers WHERE id = %s AND template_id = %s",
        (layer_id, template_id),
    )
    return {"ok": True}


@app.post("/api/page-templates/{template_id}/layers/{layer_id}/generate")
async def generate_page_layer(
    template_id: int, layer_id: int, request: Request
) -> dict[str, Any]:
    """Run image generation for a single layer and persist the result."""
    body = await request.json()
    layer = await db_fetchone(
        app,
        "SELECT * FROM page_layers WHERE id = %s AND template_id = %s",
        (layer_id, template_id),
    )
    if layer is None:
        raise HTTPException(404, {"error": "layer not found"})

    from engine.generation import (
        ControlNetInput,
        IPAdapterRef,
        LayerGenerationRequest,
        LoRARef,
        TextLayerConfig,
        generate_layer,
    )

    raw_refs = layer.get("ip_adapter_refs") or []
    resolved_refs: list[IPAdapterRef] = []
    for r in raw_refs:
        asset = await db_fetchone(
            app,
            "SELECT sheet_image FROM asset_sheets WHERE book_key = %s AND asset_id = %s",
            (layer["book_key"], r["asset_id"]),
        )
        if asset and asset.get("sheet_image"):
            resolved_refs.append(
                IPAdapterRef(
                    asset_id=r["asset_id"],
                    sheet_image=asset["sheet_image"],
                    weight=r.get("weight", 0.8),
                )
            )

    loras = [LoRARef(name=r["name"], weight=r.get("weight", 0.8)) for r in (layer.get("loras") or [])]

    cn = None
    if layer.get("controlnet_pose"):
        cp = layer["controlnet_pose"]
        cn = ControlNetInput(
            image=cp["image"],
            strength=cp.get("strength", 0.8),
            type=cp.get("type", "openpose"),
        )

    tc = None
    if layer.get("text_config"):
        t = layer["text_config"]
        tc = TextLayerConfig(
            text=t["text"],
            font_size=t.get("font_size", 48),
            font_color=tuple(t.get("font_color", [0, 0, 0, 255])),
            align=t.get("align", "center"),
            font_path=t.get("font_path"),
            padding=t.get("padding", 20),
        )

    req = LayerGenerationRequest(
        layer_kind=layer["layer_kind"],
        prompt=body.get("prompt") or layer.get("prompt") or "",
        negative_prompt=body.get("negative_prompt") or layer.get("negative_prompt") or "",
        ip_adapter_refs=resolved_refs,
        loras=loras,
        controlnet=cn,
        size=layer.get("size") or "1024x1024",
        quality=body.get("quality") or layer.get("quality") or "draft",
        remove_background=layer["layer_kind"] == "character",
        text_config=tc,
        seed=body.get("seed"),
    )

    result = await generate_layer(req)

    old_image = layer.get("image_url")
    history = list(layer.get("history") or [])
    if old_image:
        history.append(old_image)

    updated = await db_fetchone(
        app,
        """
        UPDATE page_layers
        SET image_url = %s, seed = %s, history = %s::jsonb, updated_at = now()
        WHERE id = %s
        RETURNING *
        """,
        (result.data_url, result.seed, json.dumps(history), layer_id),
    )
    return {
        **_isoize(updated or {}),
        "elapsed_s": result.elapsed_s,
        "backend": result.backend,
    }


# ── Page preview ──────────────────────────────────────────────────────


@app.get("/api/page-templates/{template_id}/preview")
async def preview_page_template(template_id: int) -> dict[str, Any]:
    """Composite all layers server-side and return a preview data URL."""
    tmpl = await db_fetchone(
        app, "SELECT * FROM page_templates WHERE id = %s", (template_id,)
    )
    if tmpl is None:
        raise HTTPException(404, {"error": "template not found"})

    layers = await db_fetchall(
        app,
        "SELECT * FROM page_layers WHERE template_id = %s ORDER BY z_index",
        (template_id,),
    )

    from engine.compositor import composite_scene

    layer_dicts = [
        {**dict(l), "type": l["layer_kind"]}
        for l in layers
        if l.get("image_url")
    ]

    if not layer_dicts:
        import base64, io
        from PIL import Image
        img = Image.new("RGB", (1024, 1024), (200, 200, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    else:
        data_url = composite_scene(layer_dicts)

    return {"template_id": template_id, "preview": data_url}


# ── Personalization swap ───────────────────────────────────────────────


@app.post("/api/page-templates/{template_id}/personalize")
async def personalize_template(
    template_id: int, request: Request
) -> dict[str, Any]:
    """Replace personalizable layers with buyer-specific character art."""
    body = await request.json()
    customer_id = body.get("customer_id")
    reference_photos: list[str] = body.get("reference_photos", [])
    if not customer_id:
        raise HTTPException(400, {"error": "customer_id required"})

    tmpl = await db_fetchone(
        app, "SELECT * FROM page_templates WHERE id = %s", (template_id,)
    )
    if tmpl is None:
        raise HTTPException(404, {"error": "template not found"})

    personalizable = await db_fetchall(
        app,
        "SELECT * FROM page_layers WHERE template_id = %s AND is_personalizable = TRUE",
        (template_id,),
    )
    if not personalizable:
        return {"swapped": 0, "customer_id": customer_id}

    swapped = 0
    for layer in personalizable:
        prompt = body.get("prompt") or layer.get("prompt") or "personalized character"
        size = layer.get("size") or "1024x1024"
        quality = body.get("quality", "standard")

        if reference_photos:
            from engine.image_provider import image_edit
            data_url = await image_edit(
                reference_photos, prompt, size=size, quality=quality,
                input_fidelity="high",
            )
        else:
            from engine.generation import LayerGenerationRequest, generate_layer
            result = await generate_layer(
                LayerGenerationRequest(
                    layer_kind="character",
                    prompt=prompt,
                    remove_background=True,
                    size=size,
                    quality=quality,
                )
            )
            data_url = result.data_url

        old_image = layer.get("image_url")
        history = list(layer.get("history") or [])
        if old_image:
            history.append(old_image)

        await db_execute(
            app,
            """
            UPDATE page_layers
            SET image_url = %s, history = %s::jsonb, updated_at = now()
            WHERE id = %s
            """,
            (data_url, json.dumps(history), layer["id"]),
        )
        swapped += 1

    return {"swapped": swapped, "customer_id": customer_id, "template_id": template_id}


# ── Finalize page ───────────────────────────────────────────────────────


@app.post("/api/finalize")
async def finalize_page(request: Request) -> dict[str, Any]:
    """Composite all layers and write a finalized_pages record."""
    body = await request.json()
    if not all(body.get(k) for k in ("book_key", "page_number")):
        raise HTTPException(400, {"error": "book_key, page_number required"})

    book_key: str = body["book_key"]
    page_number = int(body["page_number"])
    customer_id: str = body.get("customer_id") or ""

    tmpl = await db_fetchone(
        app,
        "SELECT * FROM page_templates WHERE book_key = %s AND page_number = %s",
        (book_key, page_number),
    )
    if tmpl is None:
        raise HTTPException(404, {"error": "page template not found"})

    layers = await db_fetchall(
        app,
        "SELECT * FROM page_layers WHERE template_id = %s ORDER BY z_index",
        (tmpl["id"],),
    )

    from engine.compositor import composite_scene

    layer_dicts = [
        {**dict(l), "type": l["layer_kind"]}
        for l in layers
        if l.get("image_url")
    ]
    if not layer_dicts:
        raise HTTPException(422, {"error": "no layers with images to finalize"})

    composite_url = composite_scene(layer_dicts)

    row = await db_fetchone(
        app,
        """
        INSERT INTO finalized_pages
            (book_key, page_number, customer_id, template_id, composite_url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (book_key, page_number, customer_id) DO UPDATE
            SET composite_url = EXCLUDED.composite_url,
                pdf_ready     = FALSE,
                created_at    = now()
        RETURNING *
        """,
        (book_key, page_number, customer_id, tmpl["id"], composite_url),
    )
    assert row is not None
    return _isoize(row)


# ── Lulu Print-on-Demand proxy ──────────────────────────────────────────


async def _proxy_lulu(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{LULU_SERVICE_URL}{path}"
    try:
        r = await app.state.http.request(method, url, **kwargs)
    except Exception as exc:
        raise HTTPException(502, {"error": str(exc)}) from exc
    if r.status_code >= 400:
        try:
            err = r.json()
        except Exception:
            err = {}
        msg = err.get("detail") or f"Lulu service {r.status_code}"
        raise HTTPException(502, {"error": msg})
    return r.json()


@app.get("/api/print/packages")
async def lulu_packages() -> Any:
    return await _proxy_lulu("GET", "/packages")


@app.get("/api/print/shipping-cost")
async def lulu_shipping_cost(request: Request) -> Any:
    return await _proxy_lulu("GET", "/shipping-cost", params=dict(request.query_params))


@app.post("/api/print/order")
async def lulu_order(request: Request) -> Any:
    body = await request.json()
    return await _proxy_lulu("POST", "/order", json=body)


@app.get("/api/print/orders")
async def lulu_orders() -> Any:
    return await _proxy_lulu("GET", "/orders")


@app.get("/api/print/orders/{order_id}")
async def lulu_order_get(order_id: str) -> Any:
    return await _proxy_lulu("GET", f"/orders/{order_id}")


@app.post("/api/print/orders/{order_id}/cancel")
async def lulu_order_cancel(order_id: str) -> Any:
    return await _proxy_lulu("POST", f"/orders/{order_id}/cancel")


@app.get("/api/print/health")
async def lulu_health() -> dict[str, bool]:
    try:
        r = await app.state.http.get(f"{LULU_SERVICE_URL}/health", timeout=3.0)
        return r.json()
    except Exception:
        return {"configured": False, "healthy": False}


# ── PDF export ────────────────────────────────────────────────────────


@app.post("/api/export")
async def export_pdf(request: Request) -> Any:
    body = await request.json()
    pages = body.get("pages") or []
    if not pages:
        raise HTTPException(400, {"error": "pages required"})

    mode = body.get("mode") or "interior"
    title = body.get("title") or "book"
    pdf_name = "cover.pdf" if mode == "cover" else "interior.pdf"

    tmp_dir = tempfile.mkdtemp(prefix="canvas-export-")
    payload = {
        "mode": mode,
        "title": body.get("title"),
        "author": body.get("author"),
        "product_id": body.get("product_id"),
        "pages": pages,
        "front_cover": body.get("front_cover"),
        "back_cover": body.get("back_cover"),
        "output_dir": tmp_dir,
    }

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(EXPORT_SCRIPT),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(json.dumps(payload).encode())
    if proc.returncode != 0:
        raise HTTPException(500, {"error": stderr.decode() or "export failed"})
    try:
        result = json.loads(stdout.decode().strip())
    except json.JSONDecodeError as exc:
        raise HTTPException(
            500, {"error": f"export script returned invalid JSON: {exc}"}
        ) from exc
    if not result.get("ok"):
        raise HTTPException(500, {"error": result.get("error", "export failed")})

    pdf_path = Path(tmp_dir) / pdf_name
    if not pdf_path.exists():
        raise HTTPException(500, {"error": f"export script did not produce {pdf_name}"})

    safe_title = _KEY_PATTERN.sub("_", title)
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{safe_title}_{pdf_name}",
        background=None,
    )


# ── Error mapping ───────────────────────────────────────────────────────


@app.exception_handler(HTTPException)
async def http_exception_handler(
    _request: Request, exc: HTTPException
) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, str):
        detail = {"error": detail}
    return JSONResponse(status_code=exc.status_code, content=detail)


# ── Helpers ────────────────────────────────────────────────────────


def _now_iso() -> str:
    from datetime import UTC, datetime
    return datetime.now(UTC).isoformat()


def _isoize(row: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


# ── Entrypoint ───────────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=PORT, reload=False)
