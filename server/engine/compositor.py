"""PIL-based server-side compositor.

Implements the compositeScene logic from SPEC.md §Compositing.

Rules:
  - Layers sorted by z_index ascending (back to front)
  - Background layers (slot='full_page') stretch to fill page dimensions
  - Character layers with pose.geo use anchor-snap compositing:
      ground_contact → feet aligned to slot bottom
      seat_contact   → character mid-point at 40% of slot height
  - Generic slotted layers (slot is a dict) scale to fit slot bounds,
    maintaining aspect ratio
  - Fallback: centered at 80% scale
  - Layers with visible=False are skipped entirely
  - Layers with no image_url are skipped

All images must be data URLs (data:image/...;base64,...). External URL
fetching is intentionally absent from the server-side compositor —
only data URLs produced by the generation pipeline are composited.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any

logger = logging.getLogger(__name__)

_PIL_AVAILABLE = False
try:
    from PIL import Image as _PILImage  # noqa: F401

    _PIL_AVAILABLE = True
except ImportError:
    pass


def _load_image(image_url: str) -> Any | None:
    """Load a PIL Image from a data URL. Returns None on any failure."""
    if not _PIL_AVAILABLE:
        return None
    if not image_url.startswith("data:"):
        return None
    try:
        from PIL import Image

        _, b64 = image_url.split(",", 1)
        raw = base64.b64decode(b64)
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception as exc:
        logger.debug("[compositor] Failed to load image: %s", exc)
        return None


def composite_scene(
    layers: list[dict[str, Any]],
    page_w: int = 1536,
    page_h: int = 1024,
) -> str:
    """Composite layers into a single PNG data URL.

    Args:
        layers:  List of layer dicts matching the BookWorkspace layer shape.
        page_w:  Page width in pixels.
        page_h:  Page height in pixels.

    Returns:
        PNG data URL string. Empty string if Pillow is not installed.
    """
    if not _PIL_AVAILABLE:
        logger.warning("[compositor] Pillow not installed; returning empty string")
        return ""

    from PIL import Image

    canvas = Image.new("RGBA", (page_w, page_h), (255, 255, 255, 255))

    visible = [
        layer for layer in layers
        if layer.get("visible", True) and layer.get("image_url")
    ]
    sorted_layers = sorted(visible, key=lambda l: l.get("z_index", 0))

    for layer in sorted_layers:
        img = _load_image(layer["image_url"])
        if img is None:
            continue

        slot = layer.get("slot")
        pose = layer.get("pose")
        layer_type = layer.get("type") or layer.get("layer_type", "")

        if slot == "full_page":
            _composite_full_page(canvas, img, page_w, page_h)
        elif layer_type == "character" and isinstance(pose, dict) and pose.get("geo"):
            slot_dict = (
                slot if isinstance(slot, dict)
                else {"x": 0.3, "y": 0.2, "w": 0.4, "h": 0.7}
            )
            _composite_anchored_character(canvas, img, pose, slot_dict, page_w, page_h)
        elif isinstance(slot, dict):
            _composite_slotted(canvas, img, slot, page_w, page_h)
        else:
            _composite_centered(canvas, img, page_w, page_h)

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _composite_full_page(
    canvas: Any,
    img: Any,
    page_w: int,
    page_h: int,
) -> None:
    from PIL import Image

    stretched = img.resize((page_w, page_h), Image.LANCZOS)
    canvas.paste(stretched, (0, 0), stretched)


def _composite_anchored_character(
    canvas: Any,
    img: Any,
    pose: dict[str, Any],
    slot: dict[str, Any],
    page_w: int,
    page_h: int,
) -> None:
    from PIL import Image

    slot_px = {
        "x": slot["x"] * page_w,
        "y": slot["y"] * page_h,
        "w": slot["w"] * page_w,
        "h": slot["h"] * page_h,
    }

    target_h = slot_px["h"]
    aspect = img.width / img.height if img.height else 1.0
    target_w = target_h * aspect

    resized = img.resize((int(target_w), int(target_h)), Image.LANCZOS)

    anchor = pose.get("anchor", "ground_contact")
    if anchor == "ground_contact":
        draw_x = int(slot_px["x"] + (slot_px["w"] - target_w) / 2)
        draw_y = int(slot_px["y"] + slot_px["h"] - target_h)
    elif anchor == "seat_contact":
        draw_x = int(slot_px["x"] + (slot_px["w"] - target_w) / 2)
        draw_y = int(slot_px["y"] + slot_px["h"] * 0.4 - target_h * 0.5)
    else:
        draw_x = int(slot_px["x"] + (slot_px["w"] - target_w) / 2)
        draw_y = int(slot_px["y"])

    canvas.paste(resized, (draw_x, draw_y), resized)


def _composite_slotted(
    canvas: Any,
    img: Any,
    slot: dict[str, Any],
    page_w: int,
    page_h: int,
) -> None:
    from PIL import Image

    dx = int(slot["x"] * page_w)
    dy = int(slot["y"] * page_h)
    dw = int(slot["w"] * page_w)
    dh = int(slot["h"] * page_h)

    img_aspect = img.width / img.height if img.height else 1.0
    slot_aspect = dw / dh if dh else 1.0

    if img_aspect > slot_aspect:
        draw_h = dh
        draw_w = int(dh * img_aspect)
        draw_x = dx - (draw_w - dw) // 2
        draw_y = dy
    else:
        draw_w = dw
        draw_h = int(dw / img_aspect) if img_aspect else dh
        draw_x = dx
        draw_y = dy - (draw_h - dh) // 2

    resized = img.resize((draw_w, draw_h), Image.LANCZOS)
    canvas.paste(resized, (draw_x, draw_y), resized)


def _composite_centered(
    canvas: Any,
    img: Any,
    page_w: int,
    page_h: int,
) -> None:
    from PIL import Image

    scale = min(page_w / img.width, page_h / img.height) * 0.8
    dw = int(img.width * scale)
    dh = int(img.height * scale)
    resized = img.resize((dw, dh), Image.LANCZOS)
    x = (page_w - dw) // 2
    y = (page_h - dh) // 2
    canvas.paste(resized, (x, y), resized)
