"""Unit tests for composite_scene."""
import base64
import io

import pytest
from PIL import Image


def _data_url(color=(128, 128, 128, 255), size=(64, 64), mode="RGBA") -> str:
    img = Image.new(mode, size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _decode(data_url: str) -> Image.Image:
    _, b64 = data_url.split(",", 1)
    return Image.open(io.BytesIO(base64.b64decode(b64)))


class TestCompositeScene:
    def test_empty_layers_returns_white_canvas(self):
        from engine.compositor import composite_scene
        result = composite_scene([], page_w=64, page_h=64)
        img = _decode(result)
        assert img.size == (64, 64)
        assert img.convert("RGB").getpixel((0, 0)) == (255, 255, 255)

    def test_returns_png_data_url(self):
        from engine.compositor import composite_scene
        assert composite_scene([], page_w=64, page_h=64).startswith("data:image/png;base64,")

    def test_output_matches_page_dimensions(self):
        from engine.compositor import composite_scene
        result = composite_scene([], page_w=100, page_h=200)
        assert _decode(result).size == (100, 200)

    def test_invisible_layer_skipped(self):
        from engine.compositor import composite_scene
        layer = {"z_index": 0, "image_url": _data_url((255, 0, 0, 255)), "visible": False, "slot": "full_page"}
        result = composite_scene([layer], page_w=64, page_h=64)
        # Red layer invisible — canvas should still be white
        pixel = _decode(result).convert("RGB").getpixel((32, 32))
        assert pixel == (255, 255, 255)

    def test_layer_without_image_url_skipped(self):
        from engine.compositor import composite_scene
        result = composite_scene([{"z_index": 0, "slot": "full_page"}], page_w=64, page_h=64)
        assert result.startswith("data:image/png;base64,")

    def test_full_page_layer_fills_canvas(self):
        from engine.compositor import composite_scene
        layer = {"z_index": 0, "image_url": _data_url((0, 0, 255, 255)), "slot": "full_page"}
        img = _decode(composite_scene([layer], page_w=64, page_h=64)).convert("RGB")
        r, g, b = img.getpixel((0, 0))
        assert b > 200 and r < 50  # blue dominant

    def test_higher_z_index_renders_on_top(self):
        from engine.compositor import composite_scene
        bottom = {"z_index": 0, "image_url": _data_url((255, 0, 0, 255)), "slot": "full_page"}
        top    = {"z_index": 1, "image_url": _data_url((0, 0, 255, 255)), "slot": "full_page"}
        img = _decode(composite_scene([bottom, top], page_w=64, page_h=64)).convert("RGB")
        r, g, b = img.getpixel((32, 32))
        assert b > r  # top (blue) dominates

    def test_layers_sorted_regardless_of_input_order(self):
        from engine.compositor import composite_scene
        # Pass top layer first — compositor must sort by z_index
        top    = {"z_index": 1, "image_url": _data_url((0, 0, 255, 255)), "slot": "full_page"}
        bottom = {"z_index": 0, "image_url": _data_url((255, 0, 0, 255)), "slot": "full_page"}
        img = _decode(composite_scene([top, bottom], page_w=64, page_h=64)).convert("RGB")
        r, g, b = img.getpixel((32, 32))
        assert b > r  # blue still on top after sort

    def test_slotted_layer_does_not_crash(self):
        from engine.compositor import composite_scene
        layer = {
            "z_index": 0,
            "image_url": _data_url((0, 255, 0, 255)),
            "slot": {"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5},
        }
        result = composite_scene([layer], page_w=128, page_h=128)
        assert result.startswith("data:image/png;base64,")

    def test_character_layer_type_recognised(self):
        from engine.compositor import composite_scene
        layer = {
            "z_index": 0,
            "image_url": _data_url((100, 200, 100, 255)),
            "type": "character",
            "slot": {"x": 0.3, "y": 0.1, "w": 0.4, "h": 0.8},
        }
        result = composite_scene([layer], page_w=128, page_h=128)
        assert result.startswith("data:image/png;base64,")
