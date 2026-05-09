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

# ── Config ────────────────────────────────────────────────────────────

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


def safe_key(key: str | None) -> str:
    return _KEY_PATTERN.sub("_", key or "untitled")[:80]


# ── App lifecycle ─────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    pool = psycopg_pool.AsyncConnectionPool(DB_DSN, open=False, max_size=10)
    await pool.open()
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


# ── Helpers ───────────────────────────────────────────────────────────


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


# ── Books ─────────────────────────────────────────────────────────────


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


# ── Templates ─────────────────────────────────────────────────────────


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


# ── Generation attempts (training data) ───────────────────────────────


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


# ── Page layout versions (training data) ──────────────────────────────


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


# ── Lulu Print-on-Demand proxy ────────────────────────────────────────


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
        raise HTTPException(500, {"error": f"export script returned invalid JSON: {exc}"}) from exc
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


# ── Error mapping ─────────────────────────────────────────────────────


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, str):
        detail = {"error": detail}
    return JSONResponse(status_code=exc.status_code, content=detail)


# ── Helpers ───────────────────────────────────────────────────────────


def _now_iso() -> str:
    from datetime import datetime, UTC
    return datetime.now(UTC).isoformat()


def _isoize(row: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


# ── Entrypoint ────────────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=PORT, reload=False)
