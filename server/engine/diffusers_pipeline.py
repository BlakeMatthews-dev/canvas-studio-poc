"""Diffusers in-process pipeline with IP-Adapter, multi-LoRA, and ControlNet.

Design
------
Singleton ``DiffusersPipeline`` loads the base SDXL model once (lazily,
on first request) and shares UNet/VAE/text-encoders across all pipeline
variants to avoid double VRAM.

Pipeline variants built on demand
  txt2img   — StableDiffusionXLPipeline
  img2img   — StableDiffusionXLImg2ImgPipeline     (shared UNet)
  t2i + CN  — StableDiffusionXLControlNetPipeline (via from_pipe)
  i2i + CN  — StableDiffusionXLControlNetImg2ImgPipeline (via from_pipe)

IP-Adapter
  Loaded once from IPADAPTER_REPO.  Per-request weights set via
  pipe.set_ip_adapter_scale([w1, w2, ...]).  Each IPAdapterRef carries
  its own weight so you can emphasise a character sheet over a room sheet.

LoRA stacking
  LoRA .safetensors files are loaded once from LORA_DIR (lazy, cached).
  Each inference call calls set_adapters(names, weights) before generation
  so multiple LoRAs with individual weights are active simultaneously.

ControlNet preprocessing
  canny   — cv2.Canny (falls back to numpy threshold when cv2 absent)
  depth   — controlnet_aux MidasDetector (falls back to raw image)
  openpose — controlnet_aux OpenposeDetector (falls back to raw image)
  scribble — no preprocessing required

Environment variables
  DIFFUSERS_MODEL_ID       HF model ID or local path
                           default: stabilityai/stable-diffusion-xl-base-1.0
  DIFFUSERS_DTYPE          float16 | bfloat16 | float32  (default: float16)
  DIFFUSERS_DEVICE         cuda | mps | cpu  (default: auto-detect)
  LORA_DIR                 Directory of .safetensors LoRA files (default: ./loras)
  IPADAPTER_REPO           HF repo for IP-Adapter, e.g. h94/IP-Adapter
                           Leave empty to disable IP-Adapter.
  IPADAPTER_SUBFOLDER      default: sdxl_models
  IPADAPTER_WEIGHT_NAME    default: ip-adapter_sdxl.bin
  CONTROLNET_OPENPOSE_ID   default: xinsir/controlnet-openpose-sdxl-1.0
  CONTROLNET_DEPTH_ID      default: diffusers/controlnet-depth-sdxl-1.0
  CONTROLNET_CANNY_ID      default: diffusers/controlnet-canny-sdxl-1.0
  CONTROLNET_SCRIBBLE_ID   default: xinsir/controlnet-scribble-sdxl-1.0
"""
from __future__ import annotations

import asyncio
import base64
import io
import logging
import math
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CN_DEFAULTS: dict[str, str] = {
    "openpose": os.environ.get("CONTROLNET_OPENPOSE_ID", "xinsir/controlnet-openpose-sdxl-1.0"),
    "depth":    os.environ.get("CONTROLNET_DEPTH_ID",    "diffusers/controlnet-depth-sdxl-1.0"),
    "canny":    os.environ.get("CONTROLNET_CANNY_ID",    "diffusers/controlnet-canny-sdxl-1.0"),
    "scribble": os.environ.get("CONTROLNET_SCRIBBLE_ID", "xinsir/controlnet-scribble-sdxl-1.0"),
}
_STEPS    = {"draft": 20, "standard": 30, "high": 50}
_GUIDANCE = {"draft": 5.0, "standard": 7.5, "high": 8.0}
_NEG_DEFAULT = "blurry, low quality, watermark, text, signature"


# ——— PIL helpers ————————————————————————————————————————————

def _pil_from_data_url(data_url: str) -> Any:
    from PIL import Image
    _, b64 = data_url.split(",", 1)
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")


def _data_url_from_pil(img: Any) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _tile_pil(images: list[Any], w: int, h: int) -> Any:
    from PIL import Image
    n = len(images)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    cell_w, cell_h = w // cols, h // rows
    canvas = Image.new("RGB", (w, h), (128, 128, 128))
    for i, img in enumerate(images):
        canvas.paste(img.resize((cell_w, cell_h), Image.LANCZOS), ((i % cols) * cell_w, (i // cols) * cell_h))
    return canvas


def _parse_size(size: str) -> tuple[int, int]:
    parts = size.split("x")
    return (int(parts[0]), int(parts[1])) if len(parts) == 2 else (1024, 1024)


def _adapter_name(filename: str) -> str:
    return Path(filename).stem.replace("-", "_").replace(" ", "_")


# ——— Pipeline singleton ———————————————————————————————————————

class DiffusersPipeline:
    _instance: DiffusersPipeline | None = None
    _available: bool | None = None

    def __init__(self) -> None:
        self._t2i: Any = None         # StableDiffusionXLPipeline (owns UNet)
        self._i2i: Any = None         # StableDiffusionXLImg2ImgPipeline
        self._cn_t2i: dict[str, Any] = {}   # cn_type → ControlNetPipeline
        self._cn_i2i: dict[str, Any] = {}   # cn_type → ControlNetImg2ImgPipeline
        self._cn_models: dict[str, Any] = {} # cn_type → ControlNetModel
        self._loras: set[str] = set()        # loaded adapter_names
        self._ip_loaded = False
        self._lock = asyncio.Lock()
        self._ready = False

    @classmethod
    def get(cls) -> DiffusersPipeline:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def available(cls) -> bool:
        if cls._available is None:
            try:
                import torch, diffusers  # noqa: F401,E401
                cls._available = True
            except ImportError:
                cls._available = False
        return bool(cls._available)

    async def ensure_ready(self) -> bool:
        if not self.available():
            return False
        async with self._lock:
            if not self._ready:
                try:
                    await asyncio.to_thread(self._load_model)
                    self._ready = True
                except Exception as exc:
                    logger.error("[diffusers] model load failed: %s", exc, exc_info=True)
        return self._ready

    # ——— model init ———————————————————————————————————————

    def _load_model(self) -> None:
        import torch
        from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline

        model_id = os.environ.get("DIFFUSERS_MODEL_ID", "stabilityai/stable-diffusion-xl-base-1.0")
        dtype_s   = os.environ.get("DIFFUSERS_DTYPE", "float16")
        dtype     = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}.get(dtype_s, torch.float16)
        device    = self._device()

        logger.info("[diffusers] loading %s  device=%s  dtype=%s", model_id, device, dtype_s)
        kw: dict[str, Any] = {"torch_dtype": dtype, "use_safetensors": True}
        if dtype == torch.float16:
            kw["variant"] = "fp16"

        self._t2i = StableDiffusionXLPipeline.from_pretrained(model_id, **kw)
        if device == "cuda":
            self._t2i.enable_model_cpu_offload()
        else:
            self._t2i.to(device)

        # img2img shares UNet/VAE/encoders — no extra VRAM
        self._i2i = StableDiffusionXLImg2ImgPipeline(**self._t2i.components)

        ip_repo = os.environ.get("IPADAPTER_REPO", "")
        if ip_repo:
            self._load_ip_on(self._t2i, ip_repo, "t2i")
            self._load_ip_on(self._i2i, ip_repo, "i2i")

        logger.info("[diffusers] base model ready")

    def _device(self) -> str:
        d = os.environ.get("DIFFUSERS_DEVICE", "auto")
        if d != "auto":
            return d
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    def _load_ip_on(self, pipe: Any, repo: str, tag: str) -> None:
        subfolder = os.environ.get("IPADAPTER_SUBFOLDER", "sdxl_models")
        weight    = os.environ.get("IPADAPTER_WEIGHT_NAME", "ip-adapter_sdxl.bin")
        try:
            pipe.load_ip_adapter(repo, subfolder=subfolder, weight_name=weight)
            self._ip_loaded = True
            logger.info("[diffusers] IP-Adapter loaded (%s)", tag)
        except Exception as exc:
            logger.warning("[diffusers] IP-Adapter (%s) skipped: %s", tag, exc)

    # ——— LoRA —————————————————————————————————————————

    def _apply_loras(self, pipe: Any, loras: list[Any]) -> None:
        """Load any new LoRAs then activate all requested adapters with weights."""
        lora_dir = Path(os.environ.get("LORA_DIR", "./loras"))
        active_names: list[str] = []
        active_weights: list[float] = []

        for lora in loras:
            aname = _adapter_name(lora.name)
            if aname not in self._loras:
                path = lora_dir / lora.name
                if not path.exists():
                    logger.warning("[diffusers] LoRA not found: %s", path)
                    continue
                try:
                    pipe.load_lora_weights(str(lora_dir), weight_name=lora.name, adapter_name=aname)
                    self._loras.add(aname)
                    logger.info("[diffusers] LoRA loaded: %s", aname)
                except Exception as exc:
                    logger.warning("[diffusers] LoRA load failed %s: %s", lora.name, exc)
                    continue
            if aname in self._loras:
                active_names.append(aname)
                active_weights.append(lora.weight)

        if active_names:
            pipe.set_adapters(active_names, adapter_weights=active_weights)
        else:
            try:
                pipe.disable_lora()
            except Exception:
                pass

    # ——— ControlNet —————————————————————————————————————

    def _cn_pipe(self, cn_type: str, i2i: bool) -> Any | None:
        cache = self._cn_i2i if i2i else self._cn_t2i
        if cn_type in cache:
            return cache[cn_type]

        model_id = _CN_DEFAULTS.get(cn_type)
        if not model_id:
            logger.warning("[diffusers] unknown ControlNet type: %s", cn_type)
            return None

        import torch
        from diffusers import ControlNetModel
        if cn_type not in self._cn_models:
            logger.info("[diffusers] loading ControlNet %s", model_id)
            dtype_s = os.environ.get("DIFFUSERS_DTYPE", "float16")
            dtype   = {"float16": torch.float16, "bfloat16": torch.bfloat16}.get(dtype_s, torch.float16)
            self._cn_models[cn_type] = ControlNetModel.from_pretrained(model_id, torch_dtype=dtype, use_safetensors=True)

        if i2i:
            from diffusers import StableDiffusionXLControlNetImg2ImgPipeline as Cls
        else:
            from diffusers import StableDiffusionXLControlNetPipeline as Cls

        # from_pipe shares UNet/VAE/encoders and handles IP-Adapter transfer
        cn_pipe = Cls.from_pipe(self._t2i, controlnet=self._cn_models[cn_type])
        cache[cn_type] = cn_pipe
        logger.info("[diffusers] ControlNet pipe ready: %s (i2i=%s)", cn_type, i2i)
        return cn_pipe

    def _preprocess_cn(self, image_url: str, cn_type: str, w: int, h: int) -> Any:
        from PIL import Image
        img = _pil_from_data_url(image_url).resize((w, h), Image.LANCZOS)

        if cn_type == "canny":
            import numpy as np
            arr = np.array(img.convert("L"))
            try:
                import cv2
                edges = cv2.Canny(arr, 100, 200)
            except ImportError:
                edges = ((arr > 128).astype(np.uint8)) * 255
            return Image.fromarray(np.stack([edges] * 3, axis=-1))

        if cn_type == "depth":
            try:
                from controlnet_aux import MidasDetector
                return MidasDetector.from_pretrained("lllyasviel/Annotators")(img)
            except Exception as exc:
                logger.warning("[diffusers] depth preprocess failed: %s", exc)
                return img

        if cn_type == "openpose":
            try:
                from controlnet_aux import OpenposeDetector
                return OpenposeDetector.from_pretrained("lllyasviel/Annotators")(img)
            except Exception as exc:
                logger.warning("[diffusers] openpose preprocess failed: %s", exc)
                return img

        return img  # scribble or unknown — pass through as-is

    # ——— core inference ———————————————————————————————————

    def _run(  # noqa: PLR0912
        self,
        *,
        pipe: Any,
        prompt: str,
        negative_prompt: str,
        ip_refs: list[Any],   # IPAdapterRef
        loras: list[Any],     # LoRARef
        cn: Any | None,       # ControlNetInput
        ref_pil: list[Any] | None,  # PIL images for img2img init
        denoise: float,
        width: int,
        height: int,
        steps: int,
        guidance: float,
        seed: int | None,
    ) -> str:
        import torch
        from PIL import Image

        self._apply_loras(pipe, loras)

        ip_images: list[Any] = []
        ip_scales: list[float] = []
        if self._ip_loaded and ip_refs:
            for ref in ip_refs:
                ip_images.append(_pil_from_data_url(ref.sheet_image))
                ip_scales.append(ref.weight)
            try:
                pipe.set_ip_adapter_scale(ip_scales)
            except Exception:
                pass

        gen = torch.Generator().manual_seed(seed) if seed is not None else None

        kw: dict[str, Any] = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or _NEG_DEFAULT,
            "width": width,
            "height": height,
            "num_inference_steps": steps,
            "guidance_scale": guidance,
            "generator": gen,
        }
        if ip_images:
            kw["ip_adapter_image"] = ip_images

        if ref_pil is not None:
            # img2img: base image is the reference composite
            base = _tile_pil(ref_pil, width, height) if len(ref_pil) > 1 else ref_pil[0].resize((width, height), Image.LANCZOS)
            kw["image"] = base
            kw["strength"] = denoise
            if cn is not None:
                kw["control_image"] = self._preprocess_cn(cn.image, cn.type, width, height)
                kw["controlnet_conditioning_scale"] = float(cn.strength)
        else:
            # txt2img: ControlNet conditioning goes in "image"
            if cn is not None:
                kw["image"] = self._preprocess_cn(cn.image, cn.type, width, height)
                kw["controlnet_conditioning_scale"] = float(cn.strength)

        result = pipe(**kw)
        return _data_url_from_pil(result.images[0])

    # ——— public API —————————————————————————————————————

    async def txt2img(
        self,
        prompt: str,
        negative_prompt: str = "",
        ip_refs: list[Any] | None = None,
        loras: list[Any] | None = None,
        controlnet: Any | None = None,
        size: str = "1024x1024",
        quality: str = "draft",
        seed: int | None = None,
    ) -> str:
        w, h = _parse_size(size)
        pipe = self._t2i
        if controlnet is not None:
            cn_pipe = self._cn_pipe(controlnet.type, i2i=False)
            if cn_pipe is not None:
                pipe = cn_pipe
            else:
                controlnet = None  # fallback: ignore ControlNet
        return await asyncio.to_thread(
            self._run,
            pipe=pipe, prompt=prompt, negative_prompt=negative_prompt,
            ip_refs=ip_refs or [], loras=loras or [], cn=controlnet,
            ref_pil=None, denoise=1.0,
            width=w, height=h,
            steps=_STEPS.get(quality, 30), guidance=_GUIDANCE.get(quality, 7.5),
            seed=seed,
        )

    async def img2img(
        self,
        ref_data_urls: list[str],
        prompt: str,
        negative_prompt: str = "",
        ip_refs: list[Any] | None = None,
        loras: list[Any] | None = None,
        controlnet: Any | None = None,
        size: str = "1024x1024",
        quality: str = "draft",
        denoise: float = 0.75,
        seed: int | None = None,
    ) -> str:
        pil_refs = [_pil_from_data_url(u) for u in ref_data_urls]
        w, h = _parse_size(size)
        pipe = self._i2i
        if controlnet is not None:
            cn_pipe = self._cn_pipe(controlnet.type, i2i=True)
            if cn_pipe is not None:
                pipe = cn_pipe
            else:
                controlnet = None
        return await asyncio.to_thread(
            self._run,
            pipe=pipe, prompt=prompt, negative_prompt=negative_prompt,
            ip_refs=ip_refs or [], loras=loras or [], cn=controlnet,
            ref_pil=pil_refs, denoise=denoise,
            width=w, height=h,
            steps=_STEPS.get(quality, 30), guidance=_GUIDANCE.get(quality, 7.5),
            seed=seed,
        )
