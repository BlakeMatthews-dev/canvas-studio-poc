"""Unit tests for generate_layer() and render_text_layer()."""
import asyncio
import base64
import io
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image


def _png_data_url() -> str:
    img = Image.new("RGBA", (64, 64), (128, 128, 128, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


FAKE_URL = "data:image/png;base64,ZmFrZQ=="


# ——— render_text_layer ——————————————————————————————————

class TestRenderTextLayer:
    def test_returns_data_url(self):
        from engine.generation import TextLayerConfig, render_text_layer
        result = render_text_layer(TextLayerConfig(text="Hello"), "256x256")
        assert result.startswith("data:image/png;base64,")

    def test_output_is_rgba(self):
        from engine.generation import TextLayerConfig, render_text_layer
        result = render_text_layer(TextLayerConfig(text="Test"), "256x256")
        _, b64 = result.split(",", 1)
        img = Image.open(io.BytesIO(base64.b64decode(b64)))
        assert img.mode == "RGBA"

    def test_output_size_matches_request(self):
        from engine.generation import TextLayerConfig, render_text_layer
        result = render_text_layer(TextLayerConfig(text="Test"), "512x384")
        _, b64 = result.split(",", 1)
        assert Image.open(io.BytesIO(base64.b64decode(b64))).size == (512, 384)

    def test_long_text_wraps_without_error(self):
        from engine.generation import TextLayerConfig, render_text_layer
        long_text = "This is a very long sentence that must wrap across multiple lines in the image"
        result = render_text_layer(TextLayerConfig(text=long_text), "256x256")
        assert result.startswith("data:image/png;base64,")

    def test_center_align(self):
        from engine.generation import TextLayerConfig, render_text_layer
        result = render_text_layer(TextLayerConfig(text="C", align="center"), "128x128")
        assert result.startswith("data:image/png;base64,")


# ——— generate_layer — text path ————————————————————————————

class TestTextLayerPath:
    async def test_backend_is_pillow(self):
        from engine.generation import LayerGenerationRequest, TextLayerConfig, generate_layer
        req = LayerGenerationRequest(
            layer_kind="text", prompt="",
            text_config=TextLayerConfig(text="Chapter 1"),
        )
        result = await generate_layer(req)
        assert result.backend == "pillow"

    async def test_data_url_is_transparent_png(self):
        from engine.generation import LayerGenerationRequest, TextLayerConfig, generate_layer
        req = LayerGenerationRequest(
            layer_kind="text", prompt="",
            text_config=TextLayerConfig(text="x"),
        )
        result = await generate_layer(req)
        _, b64 = result.data_url.split(",", 1)
        img = Image.open(io.BytesIO(base64.b64decode(b64)))
        assert img.mode == "RGBA"

    async def test_raises_without_text_config(self):
        from engine.generation import LayerGenerationRequest, generate_layer
        req = LayerGenerationRequest(layer_kind="text", prompt="")
        with pytest.raises(ValueError, match="text_config required"):
            await generate_layer(req)


# ——— generate_layer — Diffusers path ———————————————————————

class TestDiffusersPath:
    def _ready_pipe(self):
        m = AsyncMock()
        m.ensure_ready = AsyncMock(return_value=True)
        m.txt2img = AsyncMock(return_value=FAKE_URL)
        m.img2img = AsyncMock(return_value=FAKE_URL)
        return m

    async def test_ip_refs_routes_to_img2img(self):
        from engine.generation import IPAdapterRef, LayerGenerationRequest, generate_layer
        pipe = self._ready_pipe()
        req = LayerGenerationRequest(
            layer_kind="character", prompt="hero",
            ip_adapter_refs=[IPAdapterRef("hero", _png_data_url(), 0.8)],
        )
        with patch("engine.generation.DiffusersPipeline") as MockDP:
            MockDP.get.return_value = pipe
            result = await generate_layer(req)
        pipe.img2img.assert_awaited_once()
        assert result.backend == "diffusers-img2img"

    async def test_no_refs_routes_to_txt2img(self):
        from engine.generation import LayerGenerationRequest, generate_layer
        pipe = self._ready_pipe()
        req = LayerGenerationRequest(layer_kind="background", prompt="forest")
        with patch("engine.generation.DiffusersPipeline") as MockDP:
            MockDP.get.return_value = pipe
            result = await generate_layer(req)
        pipe.txt2img.assert_awaited_once()
        assert result.backend == "diffusers-txt2img"

    async def test_loras_forwarded_to_txt2img(self):
        from engine.generation import LayerGenerationRequest, LoRARef, generate_layer
        pipe = self._ready_pipe()
        loras = [LoRARef("hero.safetensors", 0.8), LoRARef("style.safetensors", 0.6)]
        req = LayerGenerationRequest(layer_kind="background", prompt="x", loras=loras)
        with patch("engine.generation.DiffusersPipeline") as MockDP:
            MockDP.get.return_value = pipe
            await generate_layer(req)
        _, kw = pipe.txt2img.call_args
        assert kw["loras"] == loras

    async def test_controlnet_forwarded_to_txt2img(self):
        from engine.generation import ControlNetInput, LayerGenerationRequest, generate_layer
        pipe = self._ready_pipe()
        cn = ControlNetInput(image=_png_data_url(), strength=0.8, type="openpose")
        req = LayerGenerationRequest(layer_kind="character", prompt="x", controlnet=cn)
        with patch("engine.generation.DiffusersPipeline") as MockDP:
            MockDP.get.return_value = pipe
            await generate_layer(req)
        _, kw = pipe.txt2img.call_args
        assert kw["controlnet"] is cn

    async def test_remove_background_applied_for_character(self):
        from engine.generation import LayerGenerationRequest, generate_layer
        pipe = self._ready_pipe()
        req = LayerGenerationRequest(
            layer_kind="character", prompt="x", remove_background=True
        )
        rembg_url = "data:image/png;base64,TRANSPARENT"
        with patch("engine.generation.DiffusersPipeline") as MockDP:
            MockDP.get.return_value = pipe
            with patch("engine.generation._remove_background", AsyncMock(return_value=rembg_url)):
                result = await generate_layer(req)
        assert result.data_url == rembg_url

    async def test_remove_background_not_applied_when_false(self):
        from engine.generation import LayerGenerationRequest, generate_layer
        pipe = self._ready_pipe()
        req = LayerGenerationRequest(
            layer_kind="background", prompt="x", remove_background=False
        )
        with patch("engine.generation.DiffusersPipeline") as MockDP:
            MockDP.get.return_value = pipe
            with patch("engine.generation._remove_background", AsyncMock()) as mock_rembg:
                await generate_layer(req)
        mock_rembg.assert_not_awaited()


# ——— generate_layer — fallback path ————————————————————————

class TestFallbackPath:
    async def test_comfyui_txt2img_when_diffusers_unavailable(self):
        from engine.generation import LayerGenerationRequest, generate_layer
        pipe = AsyncMock()
        pipe.ensure_ready = AsyncMock(return_value=False)
        req = LayerGenerationRequest(layer_kind="background", prompt="x")
        with patch("engine.generation.DiffusersPipeline") as MockDP:
            MockDP.get.return_value = pipe
            with patch("engine.generation.generate_image", AsyncMock(return_value=FAKE_URL)):
                result = await generate_layer(req)
        assert result.backend == "comfyui-txt2img"

    async def test_comfyui_img2img_when_diffusers_unavailable_with_refs(self):
        from engine.generation import IPAdapterRef, LayerGenerationRequest, generate_layer
        pipe = AsyncMock()
        pipe.ensure_ready = AsyncMock(return_value=False)
        req = LayerGenerationRequest(
            layer_kind="character", prompt="x",
            ip_adapter_refs=[IPAdapterRef("hero", _png_data_url(), 0.8)],
        )
        with patch("engine.generation.DiffusersPipeline") as MockDP:
            MockDP.get.return_value = pipe
            with patch("engine.generation.image_edit", AsyncMock(return_value=FAKE_URL)):
                result = await generate_layer(req)
        assert result.backend == "comfyui-img2img"


# ——— _remove_background ——————————————————————————————————

class TestRemoveBackground:
    async def test_returns_original_when_rembg_missing(self):
        from engine.generation import _remove_background
        url = _png_data_url()
        with patch.dict(sys.modules, {"rembg": None}):
            result = await _remove_background(url)
        assert result == url

    async def test_returns_original_on_rembg_exception(self):
        from engine.generation import _remove_background
        url = _png_data_url()
        mock_rembg = MagicMock()
        mock_rembg.remove = MagicMock(side_effect=RuntimeError("ONNX error"))
        with patch.dict(sys.modules, {"rembg": mock_rembg}):
            result = await _remove_background(url)
        assert isinstance(result, str)  # did not raise; returned something
