"""Unit tests for DiffusersPipeline."""
import asyncio
import base64
import io
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image


def _png_data_url(w=64, h=64, color=(128, 128, 128)) -> str:
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ——— availability ———————————————————————————————————————

class TestAvailability:
    def setup_method(self):
        from engine.diffusers_pipeline import DiffusersPipeline
        DiffusersPipeline._available = None  # reset cached state between tests

    def test_returns_false_when_torch_missing(self):
        with patch.dict(sys.modules, {"torch": None, "diffusers": None}):
            from engine.diffusers_pipeline import DiffusersPipeline
            DiffusersPipeline._available = None
            assert DiffusersPipeline.available() is False

    def test_returns_bool(self):
        from engine.diffusers_pipeline import DiffusersPipeline
        assert isinstance(DiffusersPipeline.available(), bool)

    def test_get_returns_same_instance_on_repeated_calls(self):
        from engine.diffusers_pipeline import DiffusersPipeline
        assert DiffusersPipeline.get() is DiffusersPipeline.get()


# ——— ensure_ready ————————————————————————————————————

class TestEnsureReady:
    def _make_dp(self):
        from engine.diffusers_pipeline import DiffusersPipeline
        dp = DiffusersPipeline.__new__(DiffusersPipeline)
        dp._ready = False
        dp._lock = asyncio.Lock()
        return dp

    async def test_returns_false_when_unavailable(self):
        dp = self._make_dp()
        with patch("engine.diffusers_pipeline.DiffusersPipeline.available", return_value=False):
            assert await dp.ensure_ready() is False

    async def test_returns_true_after_successful_load(self):
        dp = self._make_dp()
        with patch("engine.diffusers_pipeline.DiffusersPipeline.available", return_value=True), \
             patch.object(dp, "_load_model"):
            assert await dp.ensure_ready() is True

    async def test_returns_false_on_load_error(self):
        dp = self._make_dp()
        with patch("engine.diffusers_pipeline.DiffusersPipeline.available", return_value=True), \
             patch.object(dp, "_load_model", side_effect=RuntimeError("CUDA OOM")):
            assert await dp.ensure_ready() is False

    async def test_does_not_reload_when_already_ready(self):
        dp = self._make_dp()
        dp._ready = True
        with patch.object(dp, "_load_model") as mock_load:
            await dp.ensure_ready()
        mock_load.assert_not_called()


# ——— LoRA ———————————————————————————————————————————

class TestApplyLoras:
    def _dp(self):
        from engine.diffusers_pipeline import DiffusersPipeline
        dp = DiffusersPipeline.__new__(DiffusersPipeline)
        dp._loras = set()
        return dp

    def test_loads_new_lora_and_calls_set_adapters(self, tmp_path):
        (tmp_path / "hero_style.safetensors").write_bytes(b"fake lora")
        dp = self._dp()
        pipe = MagicMock()
        from engine.generation import LoRARef
        with patch.dict("os.environ", {"LORA_DIR": str(tmp_path)}):
            dp._apply_loras(pipe, [LoRARef(name="hero_style.safetensors", weight=0.8)])
        pipe.load_lora_weights.assert_called_once_with(
            str(tmp_path), weight_name="hero_style.safetensors", adapter_name="hero_style"
        )
        pipe.set_adapters.assert_called_once_with(["hero_style"], adapter_weights=[0.8])

    def test_skips_missing_file_and_disables_lora(self, tmp_path):
        dp = self._dp()
        pipe = MagicMock()
        from engine.generation import LoRARef
        with patch.dict("os.environ", {"LORA_DIR": str(tmp_path)}):
            dp._apply_loras(pipe, [LoRARef(name="missing.safetensors", weight=0.5)])
        pipe.load_lora_weights.assert_not_called()
        pipe.disable_lora.assert_called_once()

    def test_stacks_multiple_loras_in_one_set_adapters_call(self, tmp_path):
        for n in ("a.safetensors", "b.safetensors"):
            (tmp_path / n).write_bytes(b"fake")
        dp = self._dp()
        pipe = MagicMock()
        from engine.generation import LoRARef
        with patch.dict("os.environ", {"LORA_DIR": str(tmp_path)}):
            dp._apply_loras(pipe, [
                LoRARef(name="a.safetensors", weight=0.8),
                LoRARef(name="b.safetensors", weight=0.6),
            ])
        assert pipe.load_lora_weights.call_count == 2
        pipe.set_adapters.assert_called_once_with(["a", "b"], adapter_weights=[0.8, 0.6])

    def test_does_not_reload_cached_lora(self, tmp_path):
        (tmp_path / "cached.safetensors").write_bytes(b"fake")
        dp = self._dp()
        pipe = MagicMock()
        from engine.generation import LoRARef
        loras = [LoRARef(name="cached.safetensors", weight=0.7)]
        with patch.dict("os.environ", {"LORA_DIR": str(tmp_path)}):
            dp._apply_loras(pipe, loras)
            dp._apply_loras(pipe, loras)  # second call
        assert pipe.load_lora_weights.call_count == 1  # loaded only once


# ——— ControlNet ————————————————————————————————————

class TestControlNetPipe:
    def _dp(self):
        from engine.diffusers_pipeline import DiffusersPipeline
        dp = DiffusersPipeline.__new__(DiffusersPipeline)
        dp._cn_t2i = {}
        dp._cn_i2i = {}
        dp._cn_models = {}
        dp._t2i = MagicMock()
        dp._ip_loaded = False
        return dp

    def test_returns_none_for_unknown_type(self):
        assert self._dp()._cn_pipe("unknown_type", i2i=False) is None

    def test_returns_cached_t2i_pipe(self):
        dp = self._dp()
        mock = MagicMock()
        dp._cn_t2i["canny"] = mock
        assert dp._cn_pipe("canny", i2i=False) is mock

    def test_returns_cached_i2i_pipe(self):
        dp = self._dp()
        mock = MagicMock()
        dp._cn_i2i["openpose"] = mock
        assert dp._cn_pipe("openpose", i2i=True) is mock


# ——— ControlNet preprocessing ———————————————————————————

class TestPreprocessCN:
    def _dp(self):
        from engine.diffusers_pipeline import DiffusersPipeline
        return DiffusersPipeline.__new__(DiffusersPipeline)

    def test_scribble_resizes_and_returns_image(self):
        dp = self._dp()
        result = dp._preprocess_cn(_png_data_url(128, 128), "scribble", 64, 64)
        assert result.size == (64, 64)

    def test_canny_returns_edge_image_same_size(self):
        dp = self._dp()
        result = dp._preprocess_cn(_png_data_url(64, 64), "canny", 64, 64)
        assert result.size == (64, 64)

    def test_canny_works_without_cv2(self):
        dp = self._dp()
        with patch.dict(sys.modules, {"cv2": None}):
            result = dp._preprocess_cn(_png_data_url(64, 64), "canny", 64, 64)
        assert result.size == (64, 64)

    def test_openpose_falls_back_without_controlnet_aux(self):
        dp = self._dp()
        with patch.dict(sys.modules, {"controlnet_aux": None}):
            result = dp._preprocess_cn(_png_data_url(64, 64), "openpose", 64, 64)
        assert result.size == (64, 64)

    def test_depth_falls_back_without_controlnet_aux(self):
        dp = self._dp()
        with patch.dict(sys.modules, {"controlnet_aux": None}):
            result = dp._preprocess_cn(_png_data_url(64, 64), "depth", 64, 64)
        assert result.size == (64, 64)


# ——— helpers —————————————————————————————————————————

class TestHelpers:
    def test_parse_size_square(self):
        from engine.diffusers_pipeline import _parse_size
        assert _parse_size("1024x1024") == (1024, 1024)

    def test_parse_size_rectangular(self):
        from engine.diffusers_pipeline import _parse_size
        assert _parse_size("1536x1024") == (1536, 1024)

    def test_parse_size_invalid_defaults(self):
        from engine.diffusers_pipeline import _parse_size
        assert _parse_size("bad") == (1024, 1024)

    def test_adapter_name_strips_extension(self):
        from engine.diffusers_pipeline import _adapter_name
        assert _adapter_name("hero-style.safetensors") == "hero_style"

    def test_tile_pil_produces_correct_size(self):
        from engine.diffusers_pipeline import _tile_pil
        imgs = [Image.new("RGB", (64, 64), (i * 40, 0, 0)) for i in range(4)]
        result = _tile_pil(imgs, 256, 256)
        assert result.size == (256, 256)

    def test_tile_pil_single_image(self):
        from engine.diffusers_pipeline import _tile_pil
        result = _tile_pil([Image.new("RGB", (32, 32), (0, 0, 0))], 64, 64)
        assert result.size == (64, 64)
