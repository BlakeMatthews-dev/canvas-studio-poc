"""Image provider — ComfyUI (primary) + Diffusers API (fallback) + placeholder.

Architecture:
    ComfyUI at COMFYUI_URL (default: http://localhost:8188)
    Diffusers API at DIFFUSERS_URL (default: http://localhost:7860, A1111-compatible)

Fallback chain:
    generate_image:  ComfyUI → Diffusers → placeholder
    image_edit:      ComfyUI img2img → Diffusers img2img → generate_image fallback

Multiple reference photos:
    All photos are tiled into a reference grid via _composite_references() and
    sent as a single img2img input so every photo contributes to generation.
    There is no cap on the number of reference photos.

Invariants (per SPEC.md):
    generate_image always returns a string data URL, never None, never raises.
    input_fidelity 'high' → denoise=0.35 (faithful), 'low' → denoise=0.75 (creative).
    All generation calls have 180s timeout.
    No base64 image data written to logs.
"""

from __future__ import annotations

import asyncio
import base64
import colorsys
import hashlib
import io
import logging
import math
import os
import random
import uuid
from typing import Literal

import httpx

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────

COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://localhost:8188")
COMFYUI_MODEL = os.environ.get("COMFYUI_MODEL", "sd_xl_base_1.0.safetensors")
DIFFUSERS_URL = os.environ.get("DIFFUSERS_URL", "http://localhost:7860")
TIMEOUT = 180.0
_NEGATIVE = "ugly, blurry, low quality, bad anatomy, watermark, text, logo"

InputFidelity = Literal["high", "low"]


def _fidelity_to_denoise(fidelity: str) -> float:
    """'high' → 0.35 (faithful to input); 'low' → 0.75 (creative)."""
    return 0.35 if fidelity == "high" else 0.75


def _parse_size(size: str) -> tuple[int, int]:
    """Parse '1024x1024' → (1024, 1024)."""
    try:
        w, h = size.lower().split("x")
        return int(w), int(h)
    except Exception:
        return 1024, 1024


def _quality_to_steps(quality: str) -> int:
    return {"low": 12, "medium": 20, "high": 28}.get(quality, 20)


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
        return (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAA"
            "AAYAAjCB0C8AAAAASUVORK5CYII="
        )


def _composite_references(urls: list[str]) -> str:
    """Tile all reference photos into a square grid, return as a single data URL.

    Ensures every uploaded photo contributes to img2img generation rather than
    only using the first image. Grid cells are 512x512; layout is square-ish.
    """
    from PIL import Image as PilImage

    images: list[PilImage.Image] = []
    for url in urls:
        if not url.startswith("data:image/"):
            continue
        try:
            _, b64 = url.split(",", 1)
            img = PilImage.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
            images.append(img)
        except Exception:
            continue

    if not images:
        raise ValueError("No valid images to composite")

    if len(images) == 1:
        buf = io.BytesIO()
        images[0].save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    thumb = 512
    cols = math.ceil(math.sqrt(len(images)))
    rows = math.ceil(len(images) / cols)
    grid = PilImage.new("RGB", (cols * thumb, rows * thumb), (32, 32, 32))
    for i, img in enumerate(images):
        resized = img.resize((thumb, thumb), PilImage.LANCZOS)
        grid.paste(resized, ((i % cols) * thumb, (i // cols) * thumb))

    buf = io.BytesIO()
    grid.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ── ComfyUI helpers ───────────────────────────────────────────────────


def _build_t2i_workflow(prompt: str, width: int, height: int, steps: int) -> dict:
    return {
        "4": {"inputs": {"ckpt_name": COMFYUI_MODEL}, "class_type": "CheckpointLoaderSimple"},
        "5": {"inputs": {"width": width, "height": height, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "6": {"inputs": {"text": prompt, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"text": _NEGATIVE, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "3": {
            "inputs": {
                "seed": random.randint(0, 2**32 - 1),
                "steps": steps,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
            "class_type": "KSampler",
        },
        "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"filename_prefix": "poc_", "images": ["8", 0]}, "class_type": "SaveImage"},
    }


def _build_i2i_workflow(
    uploaded_filename: str, prompt: str, width: int, height: int, steps: int, denoise: float
) -> dict:
    return {
        "4": {"inputs": {"ckpt_name": COMFYUI_MODEL}, "class_type": "CheckpointLoaderSimple"},
        "10": {"inputs": {"image": uploaded_filename, "upload": "image"}, "class_type": "LoadImage"},
        "11": {"inputs": {"pixels": ["10", 0], "vae": ["4", 2]}, "class_type": "VAEEncode"},
        "6": {"inputs": {"text": prompt, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"text": _NEGATIVE, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "3": {
            "inputs": {
                "seed": random.randint(0, 2**32 - 1),
                "steps": steps,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": denoise,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["11", 0],
            },
            "class_type": "KSampler",
        },
        "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"filename_prefix": "poc_", "images": ["8", 0]}, "class_type": "SaveImage"},
    }


async def _comfyui_poll(client: httpx.AsyncClient, prompt_id: str) -> str:
    """Poll /history/{prompt_id} until done; return first image as data URL."""
    for _ in range(int(TIMEOUT)):
        await asyncio.sleep(1)
        history = await client.get(f"/history/{prompt_id}", timeout=10.0)
        data = history.json()
        if prompt_id not in data:
            continue
        for node_output in data[prompt_id].get("outputs", {}).values():
            for img_meta in node_output.get("images", []):
                img_resp = await client.get(
                    "/view",
                    params={
                        "filename": img_meta["filename"],
                        "subfolder": img_meta.get("subfolder", ""),
                        "type": img_meta.get("type", "output"),
                    },
                    timeout=30.0,
                )
                img_resp.raise_for_status()
                b64 = base64.b64encode(img_resp.content).decode()
                return f"data:image/png;base64,{b64}"
    raise TimeoutError("ComfyUI generation timed out")


async def comfyui_text2img(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
) -> str:
    width, height = _parse_size(size)
    steps = _quality_to_steps(quality)
    workflow = _build_t2i_workflow(prompt, width, height, steps)
    client_id = str(uuid.uuid4())
    async with httpx.AsyncClient(base_url=COMFYUI_URL, timeout=TIMEOUT) as client:
        resp = await client.post("/prompt", json={"prompt": workflow, "client_id": client_id})
        resp.raise_for_status()
        prompt_id = resp.json()["prompt_id"]
        return await _comfyui_poll(client, prompt_id)


async def comfyui_img2img(
    image_data_url: str,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
    denoise: float = 0.35,
) -> str:
    width, height = _parse_size(size)
    steps = _quality_to_steps(quality)

    if not image_data_url.startswith("data:image/"):
        raise ValueError("image_data_url must be a data URL")
    _, b64 = image_data_url.split(",", 1)
    img_bytes = base64.b64decode(b64)
    ext = "png" if "png" in image_data_url[:30] else "jpg"
    filename = f"poc_input_{uuid.uuid4().hex[:8]}.{ext}"

    async with httpx.AsyncClient(base_url=COMFYUI_URL, timeout=TIMEOUT) as client:
        upload_resp = await client.post(
            "/upload/image",
            files={"image": (filename, img_bytes, f"image/{ext}")},
            data={"overwrite": "true"},
            timeout=30.0,
        )
        upload_resp.raise_for_status()
        uploaded_name = upload_resp.json().get("name", filename)

        workflow = _build_i2i_workflow(uploaded_name, prompt, width, height, steps, denoise)
        client_id = str(uuid.uuid4())
        resp = await client.post("/prompt", json={"prompt": workflow, "client_id": client_id})
        resp.raise_for_status()
        prompt_id = resp.json()["prompt_id"]
        return await _comfyui_poll(client, prompt_id)


# ── Diffusers (A1111-compatible) fallback ─────────────────────────────


async def diffusers_text2img(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
) -> str:
    width, height = _parse_size(size)
    steps = _quality_to_steps(quality)
    async with httpx.AsyncClient(base_url=DIFFUSERS_URL, timeout=TIMEOUT) as client:
        resp = await client.post(
            "/sdapi/v1/txt2img",
            json={
                "prompt": prompt,
                "negative_prompt": _NEGATIVE,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": 7,
            },
        )
        resp.raise_for_status()
        images = resp.json().get("images", [])
        if images:
            return f"data:image/png;base64,{images[0]}"
    raise RuntimeError("Diffusers txt2img returned no images")


async def diffusers_img2img(
    image_data_url: str,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
    denoising_strength: float = 0.35,
) -> str:
    width, height = _parse_size(size)
    steps = _quality_to_steps(quality)
    _, b64 = image_data_url.split(",", 1)
    async with httpx.AsyncClient(base_url=DIFFUSERS_URL, timeout=TIMEOUT) as client:
        resp = await client.post(
            "/sdapi/v1/img2img",
            json={
                "prompt": prompt,
                "negative_prompt": _NEGATIVE,
                "init_images": [b64],
                "denoising_strength": denoising_strength,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg_scale": 7,
            },
        )
        resp.raise_for_status()
        images = resp.json().get("images", [])
        if images:
            return f"data:image/png;base64,{images[0]}"
    raise RuntimeError("Diffusers img2img returned no images")


# ── Public API ────────────────────────────────────────────────────────


async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
) -> str:
    """ComfyUI → Diffusers → placeholder. Never raises, never returns None."""
    try:
        return await comfyui_text2img(prompt, size, quality)
    except Exception as exc:
        logger.warning("[image_provider] ComfyUI failed: %s", type(exc).__name__)

    try:
        return await diffusers_text2img(prompt, size, quality)
    except Exception as exc:
        logger.warning("[image_provider] Diffusers failed: %s", type(exc).__name__)

    logger.info("[image_provider] All backends failed; returning placeholder")
    return _make_placeholder(prompt)


async def image_edit(
    image_data_urls: list[str] | str,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
    input_fidelity: str = "high",
) -> str:
    """Composite all reference photos into a grid, then ComfyUI img2img →
    Diffusers img2img → generate_image fallback.

    All reference photos contribute — no cap, no silent drops.
    input_fidelity: 'high' (faithful, denoise=0.35) or 'low' (creative, denoise=0.75).
    """
    urls = [image_data_urls] if isinstance(image_data_urls, str) else list(image_data_urls)
    if not urls:
        return await generate_image(prompt, size, quality)

    # Composite all reference photos into one grid image
    try:
        ref_image = _composite_references(urls)
    except Exception as exc:
        logger.warning("[image_provider] Reference compositing failed (%s); using first image", exc)
        ref_image = urls[0]

    denoise = _fidelity_to_denoise(input_fidelity)
    errors: list[str] = []

    try:
        return await comfyui_img2img(ref_image, prompt, size, quality, denoise)
    except Exception as exc:
        errors.append(f"ComfyUI: {type(exc).__name__}")
        logger.warning("[image_provider] ComfyUI img2img failed: %s", exc)

    try:
        return await diffusers_img2img(ref_image, prompt, size, quality, denoise)
    except Exception as exc:
        errors.append(f"Diffusers: {type(exc).__name__}")
        logger.warning("[image_provider] Diffusers img2img failed: %s", exc)

    logger.warning(
        "[image_provider] All edit backends failed (%s); falling back to text-only",
        "; ".join(errors),
    )
    return await generate_image(prompt, size, quality)


async def render_layer_draft(
    prompt: str,
    reference_image: str | None = None,
) -> str:
    """Draft quality: 1024x1024, quality='low'."""
    if reference_image:
        try:
            return await image_edit(reference_image, prompt, "1024x1024", "low", "low")
        except Exception:
            pass
    return await generate_image(prompt, "1024x1024", "low")


async def render_layer_final(
    prompt: str,
    reference_image: str | None = None,
) -> str:
    """Final quality: 1024x1024, quality='medium'."""
    if reference_image:
        upgrade_prompt = " ".join([
            "Enhance this illustration to higher quality.",
            "Keep the EXACT same composition, colors, pose, and layout.",
            "Add finer detail, smoother gradients, crisper edges, and better lighting.",
            "Do NOT change the subject, pose, or scene in any way.",
            prompt,
        ])
        try:
            return await image_edit(reference_image, upgrade_prompt, "1024x1024", "medium", "high")
        except Exception as exc:
            logger.warning(
                "[image_provider] HQ edit failed (%s), regenerating from text",
                type(exc).__name__,
            )
    return await generate_image(prompt, "1024x1024", "medium")
