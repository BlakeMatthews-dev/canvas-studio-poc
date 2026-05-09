"""Layer generation — typed request/result models and generation functions.

Props are generated as part of the character layer that owns them; only
environmental background props (furniture nobody interacts with) go in
the background layer.

Pipeline per layer:
  1. Build prompt (with IP-Adapter refs described textually until real
     IP-Adapter wiring is in place).
  2. Call image_provider.image_edit() when reference sheets are available
     (img2img path), otherwise image_provider.generate_image() (txt2img).
  3. Strip background via rembg for character layers (transparent PNG).
  4. Return LayerGenerationResult with data URL + telemetry.

Text layers bypass image generation entirely — they are rendered with
Pillow and returned as transparent PNGs ready to composite over art.
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
    sheet_image: str    # data URL
    weight: float = 0.8


@dataclass
class LoRARef:
    name: str           # filename relative to the configured LoRA directory
    weight: float = 0.8


@dataclass
class ControlNetInput:
    image: str          # pose skeleton / depth map as data URL
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


async def generate_layer(req: LayerGenerationRequest) -> LayerGenerationResult:
    """Generate one page layer and return the result."""
    import time
    start = time.monotonic()

    if req.layer_kind == "text":
        if req.text_config is None:
            raise ValueError("text_config required for text layers")
        data_url = render_text_layer(req.text_config, req.size)
        return LayerGenerationResult(
            data_url=data_url,
            elapsed_s=time.monotonic() - start,
            backend="pillow",
        )

    effective_prompt = req.prompt
    if req.ip_adapter_refs:
        ref_desc = ", ".join(
            f"{r.asset_id}(w={r.weight:.1f})" for r in req.ip_adapter_refs
        )
        effective_prompt = f"{effective_prompt}, consistent with: {ref_desc}"

    from engine.image_provider import generate_image, image_edit

    if req.ip_adapter_refs:
        ref_images = [r.sheet_image for r in req.ip_adapter_refs]
        data_url = await image_edit(
            ref_images,
            effective_prompt,
            size=req.size,
            quality=req.quality,
            input_fidelity="high" if req.quality == "high" else "low",
        )
        backend = "comfyui-img2img"
    else:
        data_url = await generate_image(
            effective_prompt, size=req.size, quality=req.quality
        )
        backend = "comfyui-t2i"

    if req.remove_background and data_url:
        data_url = await _remove_background(data_url)

    return LayerGenerationResult(
        data_url=data_url,
        seed=req.seed,
        elapsed_s=time.monotonic() - start,
        backend=backend,
    )


async def _remove_background(data_url: str) -> str:
    """Strip background, returning an RGBA PNG data URL."""
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

    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    try:
        if cfg.font_path and os.path.exists(cfg.font_path):
            font = ImageFont.truetype(cfg.font_path, cfg.font_size)
        else:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                cfg.font_size,
            )
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
    total_h = len(lines) * line_h
    y = (height - total_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        if cfg.align == "center":
            x = (width - text_w) // 2
        elif cfg.align == "right":
            x = width - text_w - cfg.padding
        else:
            x = cfg.padding
        draw.text((x, y), line, font=font, fill=cfg.font_color)
        y += line_h

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
