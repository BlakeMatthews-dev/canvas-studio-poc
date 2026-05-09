from __future__ import annotations

import asyncio
import base64
import io
import logging

from PIL import Image

from engine.image_provider import (
    image_edit as _async_edit,
    generate_image as _async_generate,
    render_layer_draft,
    render_layer_final,
)

logger = logging.getLogger(__name__)


def _data_url_to_pil(data_url: str) -> Image.Image:
    _, b64 = data_url.split(",", 1)
    return Image.open(io.BytesIO(base64.b64decode(b64)))


def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "low",
    **_kwargs: object,
) -> Image.Image:
    """Synchronous wrapper — returns PIL Image. Never raises, never returns None."""
    data_url = asyncio.run(_async_generate(prompt, size=size, quality=quality))
    return _data_url_to_pil(data_url)


def generate_image_sync(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "low",
) -> str:
    """Return data URL string. Never raises, never returns None."""
    return asyncio.run(_async_generate(prompt, size=size, quality=quality))


__all__ = [
    "generate_image",
    "generate_image_sync",
    "render_layer_draft",
    "render_layer_final",
]
