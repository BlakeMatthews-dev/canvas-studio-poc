"""Layer generation — typed request/result models and generate_layer().

Props are generated as part of the character layer that owns them.
Only environmental background elements (furniture nobody touches) go
in the background layer.

Pipeline per layer (preference order)
  1. Diffusers in-process (DiffusersPipeline) — full adapter support:
       IP-Adapter, multi-LoRA, ControlNet, remove_background (rembg)
  2. ComfyUI HTTP fallback — when torch/diffusers not installed.
       IP-Adapter refs used as img2img base; LoRA/ControlNet ignored.
  3. Placeholder data URL — last resort, never raises.

Text layers bypass image generation entirely — rendered via Pillow
as transparent PNGs ready to composite over the art.
"""
from __future__ import annotations

import asyncio
import base64
import io
import os
from dataclasses import dataclass, field
from typing import Literal

ControlNetType = Literal["openpose", "depth", "canny", "scribble"]
GenerationQuality = Literal["draft", "standard", "high"]
LayerKind = Literal["background", "character", "text"]


@dataclass
class IPAdapterRef:
    """Reference sheet injected into IP-Adapter cross-attention."""
    asset_id: str
    sheet_image: str    # data URL of the reference sheet
    weight: float = 0.8


@dataclass
class LoRARef:
    name: str           # filename relative to LORA_DIR
    weight: float = 0.8


@dataclass
class ControlNetInput:
    image: str          # pose skeleton / depth map / edge map as data URL
    strength: float = 0.8
    type: ControlNetType = "openpose"  # type: ignore[assignment]


@dataclass
class TextLayerConfig:
    text: str
    font_size: int = 48
    font_color: tuple[int, int, int, int] = (0, 0, 0, 255)
    align: Literal["left", "center", "right"] = "center"
    font_path: str | None = None
    padding: int = 20


@dataclass
class LayerGenerationRequest:
    layer_kind: LayerKind
    prompt: str
    negative_prompt: str = ""
    ip_adapter_refs: list[IPAdapterRef] = field(default_factory=list)
    loras: list[LoRARef] = field(default_factory=list)
    controlnet: ControlNetInput | None = None
    size: str = "1024x1024"
    quality: GenerationQuality = "draft"
    remove_background: bool = False
    text_config: TextLayerConfig | None = None
    seed: int | None = None


@dataclass
class LayerGenerationResult:
    data_url: str
    seed: int | None = None
    model_id: str | None = None
    elapsed_s: float = 0.0
    backend: str = "unknown"


# — denoise strength: high fidelity = low denoising (keep structure)
_DENOISE = {"high": 0.35, "standard": 0.60, "draft": 0.75}


async def generate_layer(req: LayerGenerationRequest) -> LayerGenerationResult:
    """Generate one page layer and return the result."""
    import time
    start = time.monotonic()

    if req.layer_kind == "text":
        if req.text_config is None:
            raise ValueError("text_config required for text layers")
        data_url = render_text_layer(req.text_config, req.size)
        return LayerGenerationResult(data_url=data_url, elapsed_s=time.monotonic() - start, backend="pillow")

    from engine.diffusers_pipeline import DiffusersPipeline
    pipeline = DiffusersPipeline.get()
    ready = await pipeline.ensure_ready()
    denoise = _DENOISE.get(req.quality, 0.75)

    data_url: str
    backend: str

    if ready:
        has_refs = bool(req.ip_adapter_refs)
        if has_refs:
            data_url = await pipeline.img2img(
                ref_data_urls=[r.sheet_image for r in req.ip_adapter_refs],
                prompt=req.prompt,
                negative_prompt=req.negative_prompt,
                ip_refs=req.ip_adapter_refs,
                loras=req.loras,
                controlnet=req.controlnet,
                size=req.size,
                quality=req.quality,
                denoise=denoise,
                seed=req.seed,
            )
            backend = "diffusers-img2img"
        else:
            data_url = await pipeline.txt2img(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt,
                ip_refs=[],
                loras=req.loras,
                controlnet=req.controlnet,
                size=req.size,
                quality=req.quality,
                seed=req.seed,
            )
            backend = "diffusers-txt2img"
    else:
        # Fallback — ComfyUI HTTP or placeholder; LoRA/ControlNet not available
        from engine.image_provider import generate_image, image_edit
        if req.ip_adapter_refs:
            ref_urls = [r.sheet_image for r in req.ip_adapter_refs]
            data_url = await image_edit(
                ref_urls, req.prompt,
                size=req.size, quality=req.quality,
                input_fidelity="high" if req.quality == "high" else "low",
            )
            backend = "comfyui-img2img"
        else:
            data_url = await generate_image(req.prompt, size=req.size, quality=req.quality)
            backend = "comfyui-txt2img"

    if req.remove_background and data_url:
        data_url = await _remove_background(data_url)

    return LayerGenerationResult(
        data_url=data_url,
        seed=req.seed,
        elapsed_s=time.monotonic() - start,
        backend=backend,
    )


async def _remove_background(data_url: str) -> str:
    """Strip background via rembg, returning an RGBA PNG data URL."""
    try:
        import rembg  # type: ignore[import]
        _, b64 = data_url.split(",", 1)
        img_bytes = base64.b64decode(b64)
        out_bytes: bytes = await asyncio.to_thread(rembg.remove, img_bytes)
        return "data:image/png;base64," + base64.b64encode(out_bytes).decode()
    except ImportError:
        return data_url
    except Exception:
        return data_url


def render_text_layer(cfg: TextLayerConfig, size: str = "1024x1024") -> str:
    """Render a transparent PNG with word-wrapped text."""
    from PIL import Image, ImageDraw, ImageFont

    w_str, h_str = size.split("x")
    width, height = int(w_str), int(h_str)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        if cfg.font_path and os.path.exists(cfg.font_path):
            font = ImageFont.truetype(cfg.font_path, cfg.font_size)
        else:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", cfg.font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()

    max_w = width - 2 * cfg.padding
    words = cfg.text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_h = cfg.font_size + 8
    y = (height - len(lines) * line_h) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2 if cfg.align == "center" else (
            width - text_w - cfg.padding if cfg.align == "right" else cfg.padding
        )
        draw.text((x, y), line, font=font, fill=cfg.font_color)
        y += line_h

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
