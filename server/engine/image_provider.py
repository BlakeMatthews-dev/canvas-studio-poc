"""SPEC-compliant image provider — Azure / Gemini / placeholder fallback chain.

Per SPEC.md §Azure deployment chain:
    Deployments tried in order:
        1. gpt-image-1-5   api-version=2025-04-01-preview  (primary)
        2. gpt-image-2-1   api-version=2025-03-01-preview  (fallback)
    404 / 400 on a deployment → skip to the next.
    429 on a deployment → skip, accumulate error.
    Timeout or 5xx → raise immediately.

Per SPEC.md §input_fidelity:
    input_fidelity is ALWAYS sent as 'high' or 'low', never a float.
    float >= 0.7 → 'high'; float < 0.7 → 'low'.

Per SPEC.md §Invariants:
    generate_image always returns a string (data URL or placeholder),
    never None, never raises to callers.

    No base64 image data is ever written to logs.

All generation calls have a 180-second timeout.
"""

from __future__ import annotations

import base64
import colorsys
import hashlib
import io
import logging
import os
from typing import Literal

import httpx

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────

AZURE_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

# Deployment chain per SPEC: (deployment_name, api_version)
AZURE_DEPLOYMENTS: list[tuple[str, str]] = [
    ("gpt-image-1-5", "2025-04-01-preview"),
    ("gpt-image-2-1", "2025-03-01-preview"),
]

TIMEOUT = 180.0  # seconds — all generation calls per SPEC

InputFidelity = Literal["high", "low"]


def _fidelity_string(input_fidelity: float) -> InputFidelity:
    """Map float fidelity to the string Azure accepts. Per SPEC: >= 0.7 → 'high'."""
    return "high" if input_fidelity >= 0.7 else "low"


def _data_url_to_bytes(data_url: str) -> tuple[bytes, str] | None:
    """Extract (raw_bytes, mime_type) from a data URL. None if invalid or non-image."""
    if not data_url.startswith("data:"):
        return None
    try:
        header, b64 = data_url.split(",", 1)
        mime = header.split(";")[0].removeprefix("data:")
        if not mime.startswith("image/"):
            return None
        return base64.b64decode(b64), mime
    except Exception:
        return None


def _make_placeholder(label: str) -> str:
    """Return a gradient PNG data URL. Deterministic by label hash."""
    label = label[:40]
    try:
        from PIL import Image, ImageDraw

        w, h = 512, 512
        hue = int(hashlib.md5(label.encode()).hexdigest()[:4], 16) % 360
        img = Image.new("RGB", (w, h))
        pixels = img.load()
        h1 = hue / 360.0
        h2 = ((hue + 60) % 360) / 360.0
        r1, g1, b1 = colorsys.hls_to_rgb(h1, 0.20, 0.50)
        r2, g2, b2 = colorsys.hls_to_rgb(h2, 0.35, 0.60)
        for y in range(h):
            for x in range(w):
                t = (x + y) / (w + h)
                r = int((r1 * (1 - t) + r2 * t) * 255)
                g = int((g1 * (1 - t) + g2 * t) * 255)
                b_val = int((b1 * (1 - t) + b2 * t) * 255)
                pixels[x, y] = (r, g, b_val)  # type: ignore[index]
        draw = ImageDraw.Draw(img)
        draw.text((w // 2, h // 2), label, fill=(255, 255, 255, 153), anchor="mm")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        # Minimal 1x1 transparent PNG fallback
        return (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAA"
            "AAYAAjCB0C8AAAAASUVORK5CYII="
        )


# ─────────────────────────────────────────────────────────────────────
# Azure image generation
# ─────────────────────────────────────────────────────────────────────


async def azure_image_gen(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
) -> str:
    """Try each Azure deployment in order. Returns data URL on first success.

    Per SPEC: skips on 404/400, raises on timeout, raises if all fail.
    """
    if not (AZURE_KEY and AZURE_ENDPOINT):
        raise RuntimeError("Azure not configured")

    errors: list[str] = []
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for deployment, api_version in AZURE_DEPLOYMENTS:
            url = (
                f"{AZURE_ENDPOINT}/openai/deployments/{deployment}"
                f"/images/generations?api-version={api_version}"
            )
            try:
                resp = await client.post(
                    url,
                    headers={"Content-Type": "application/json", "api-key": AZURE_KEY},
                    json={"prompt": prompt, "n": 1, "size": size, "quality": quality},
                )
                if resp.status_code in (404, 400):
                    errors.append(f"{deployment}: HTTP {resp.status_code} (skip)")
                    continue
                resp.raise_for_status()
                data = resp.json()
                img = (data.get("data") or [{}])[0]
                if img.get("b64_json"):
                    return f"data:image/png;base64,{img['b64_json']}"
                if img.get("url"):
                    return img["url"]
                raise RuntimeError("No image data in response")
            except httpx.TimeoutException:
                raise  # propagate — per SPEC §Generation times out after 180 seconds
            except RuntimeError:
                raise
            except Exception as exc:
                errors.append(f"{deployment}: {exc}")
                continue

    raise RuntimeError(f"All Azure deployments failed: {'; '.join(errors)}")


# ─────────────────────────────────────────────────────────────────────
# Azure image edit (multipart/form-data)
# ─────────────────────────────────────────────────────────────────────


async def azure_image_edit(
    image_data_urls: list[str] | str,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
    input_fidelity: float = 0.8,
) -> str:
    """Send a multipart/form-data edit request to Azure.

    Per SPEC:
    - Accepts a single string or list of data URLs; all sent as image[]
    - input_fidelity float >= 0.7 → 'high', < 0.7 → 'low' (never a float)
    - Tries each deployment in AZURE_DEPLOYMENTS order
    - Skips on 404/400; accumulates error on 429
    - Raises 'All Azure edit deployments failed: ...' if all fail
    """
    if not (AZURE_KEY and AZURE_ENDPOINT):
        raise RuntimeError("Azure not configured")

    urls = [image_data_urls] if isinstance(image_data_urls, str) else list(image_data_urls)
    blobs: list[tuple[bytes, str]] = []
    for u in urls:
        result = _data_url_to_bytes(u)
        if result:
            blobs.append(result)

    if not blobs:
        raise RuntimeError("No valid images for edit")

    fidelity_str = _fidelity_string(input_fidelity)
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for deployment, api_version in AZURE_DEPLOYMENTS:
            url = (
                f"{AZURE_ENDPOINT}/openai/deployments/{deployment}"
                f"/images/edits?api-version={api_version}"
            )
            try:
                files: list[tuple[str, tuple[str, bytes, str]]] = [
                    ("image[]", (f"image.{'png' if 'png' in mime else 'jpg'}", raw, mime))
                    for raw, mime in blobs
                ]
                data_fields = {
                    "prompt": prompt,
                    "size": size,
                    "n": "1",
                    "quality": quality,
                    "input_fidelity": fidelity_str,
                }

                resp = await client.post(
                    url,
                    headers={"api-key": AZURE_KEY},
                    files=files,
                    data=data_fields,
                )

                if resp.status_code in (404, 400):
                    errors.append(f"{deployment}: HTTP {resp.status_code} (skip)")
                    continue
                if resp.status_code == 429:
                    body = resp.json().get("error", {}).get("message", "RateLimitReached")
                    errors.append(f"RateLimitReached on {deployment}: {body}")
                    continue

                resp.raise_for_status()
                result = resp.json()
                img = (result.get("data") or [{}])[0]
                if img.get("b64_json"):
                    return f"data:image/png;base64,{img['b64_json']}"
                if img.get("url"):
                    return img["url"]
                raise RuntimeError("No image data in edit response")

            except httpx.TimeoutException:
                raise
            except RuntimeError:
                raise
            except Exception as exc:
                errors.append(f"{deployment}: {exc}")
                continue

    raise RuntimeError(f"All Azure edit deployments failed: {'; '.join(errors)}")


# ─────────────────────────────────────────────────────────────────────
# Gemini fallback
# ─────────────────────────────────────────────────────────────────────


async def gemini_image_gen(prompt: str) -> str:
    """Gemini image generation fallback. Returns data URL."""
    if not GEMINI_KEY:
        raise RuntimeError("Gemini not configured")

    url = (
        "https://generativelanguage.googleapis.com/v1beta"
        "/models/gemini-2.5-flash-image:generateContent"
    )
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            url,
            params={"key": GEMINI_KEY},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": f"Generate an image: {prompt}"}]}],
                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        parts = (
            data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        )
        for part in parts:
            if "inlineData" in part:
                inline = part["inlineData"]
                return f"data:{inline['mimeType']};base64,{inline['data']}"
    raise RuntimeError("No image from Gemini")


# ─────────────────────────────────────────────────────────────────────
# Public API — always returns a string, never raises
# ─────────────────────────────────────────────────────────────────────


async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
) -> str:
    """Try Azure → Gemini → placeholder. Always returns a string data URL.

    SPEC invariant generation_never_returns_null:
        generate_image always returns a string (data URL or placeholder),
        never None, never raises.
    """
    if AZURE_KEY and AZURE_ENDPOINT:
        try:
            return await azure_image_gen(prompt, size, quality)
        except Exception as exc:
            logger.warning("[image_provider] Azure failed: %s", type(exc).__name__)

    if GEMINI_KEY:
        try:
            return await gemini_image_gen(prompt)
        except Exception as exc:
            logger.warning("[image_provider] Gemini failed: %s", type(exc).__name__)

    logger.info("[image_provider] All providers failed; returning placeholder")
    return _make_placeholder(prompt)


async def render_layer_draft(
    prompt: str,
    reference_image: str | None = None,
) -> str:
    """Draft quality: 1024x1024, quality='low'. Per SPEC §renderLayerDraft."""
    if reference_image:
        try:
            return await azure_image_edit(reference_image, prompt, "1024x1024", "low", 0.5)
        except Exception:
            pass
    return await generate_image(prompt, "1024x1024", "low")


async def render_layer_final(
    prompt: str,
    reference_image: str | None = None,
) -> str:
    """Final quality: 1024x1024, quality='medium'. Per SPEC §renderLayerFinal."""
    if reference_image:
        upgrade_prompt = " ".join([
            "Enhance this illustration to higher quality.",
            "Keep the EXACT same composition, colors, pose, and layout.",
            "Add finer detail, smoother gradients, crisper edges, and better lighting.",
            "Do NOT change the subject, pose, or scene in any way.",
            "This is a quality upgrade, not a new illustration.",
            prompt,
        ])
        try:
            return await azure_image_edit(
                reference_image, upgrade_prompt, "1024x1024", "medium", 0.9
            )
        except Exception as exc:
            logger.warning(
                "[image_provider] HQ edit failed (%s), regenerating from text...",
                type(exc).__name__,
            )
    return await generate_image(prompt, "1024x1024", "medium")
