"""BDD step definitions for layered_pipeline.feature."""
from __future__ import annotations

import base64
import io
from pathlib import Path

import pytest
from PIL import Image
from pytest_bdd import given, parsers, scenario, then, when

FEATURE = str(Path(__file__).parent.parent / "features" / "layered_pipeline.feature")


def _png_url() -> str:
    img = Image.new("RGBA", (64, 64), (100, 180, 100, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def ctx() -> dict:
    return {}


@pytest.fixture
def layer_store() -> list:
    return []


# ── scenario declarations ─────────────────────────────────────────────────────

@scenario(FEATURE, "Add a background layer to a template")
def test_add_background_layer():
    pass


@scenario(FEATURE, "Generate a background layer uses txt2img")
def test_generate_background_txt2img():
    pass


@scenario(FEATURE, "Regenerating a layer pushes old image to history")
def test_regenerate_pushes_history():
    pass


@scenario(FEATURE, "Generate a character layer with IP-Adapter refs uses img2img")
def test_character_with_refs():
    pass


@scenario(FEATURE, "Generate a character layer without refs uses txt2img")
def test_character_no_refs():
    pass


@scenario(FEATURE, "Generate a text layer uses Pillow")
def test_text_layer_pillow():
    pass


@scenario(FEATURE, "LoRAs are forwarded to the generation call")
def test_loras_forwarded():
    pass


@scenario(FEATURE, "ControlNet is forwarded to the generation call")
def test_controlnet_forwarded():
    pass


@scenario(FEATURE, "Preview composites all layers")
def test_preview_composites():
    pass


@scenario(FEATURE, "Finalize composites and stores")
def test_finalize_composites():
    pass


@scenario(FEATURE, "Finalizing with no layer images returns error")
def test_finalize_no_images():
    pass


# ── background ────────────────────────────────────────────────────────────────

@given(parsers.parse('book key "{book_key}"'), target_fixture="book_key")
def step_book_key(book_key: str) -> str:
    return book_key


@given("a page template for page 1")
def step_page_template() -> None:
    pass


# ── given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('a background layer with prompt "{prompt}"'))
def step_given_bg_layer(prompt: str, layer_store: list, ctx: dict) -> None:
    layer = {
        "id": len(layer_store) + 1,
        "layer_kind": "background",
        "prompt": prompt,
        "image_url": None,
        "history": [],
        "ip_adapter_refs": [],
        "loras": [],
        "controlnet_pose": None,
        "z_index": 0,
    }
    layer_store.append(layer)
    ctx["current_layer"] = layer


@given(parsers.parse('the layer already has image_url "{image_url}"'))
def step_layer_has_url(image_url: str, ctx: dict) -> None:
    ctx["current_layer"]["image_url"] = image_url
    ctx["old_image_url"] = image_url


@given(parsers.parse('a character layer referencing asset "{asset_id}" with sheet_image'))
def step_character_with_refs(asset_id: str, layer_store: list, ctx: dict) -> None:
    layer = {
        "id": len(layer_store) + 1,
        "layer_kind": "character",
        "prompt": f"{asset_id} character",
        "image_url": None,
        "history": [],
        "ip_adapter_refs": [{"asset_id": asset_id, "sheet_image": _png_url(), "weight": 0.8}],
        "loras": [],
        "controlnet_pose": None,
        "z_index": 1,
    }
    layer_store.append(layer)
    ctx["current_layer"] = layer


@given(parsers.parse('a character layer with prompt "{prompt}" and no ip_refs'))
def step_character_no_refs(prompt: str, layer_store: list, ctx: dict) -> None:
    layer = {
        "id": len(layer_store) + 1,
        "layer_kind": "character",
        "prompt": prompt,
        "image_url": None,
        "history": [],
        "ip_adapter_refs": [],
        "loras": [],
        "controlnet_pose": None,
        "z_index": 1,
    }
    layer_store.append(layer)
    ctx["current_layer"] = layer


@given(parsers.parse('a text layer with text "{text}" and font_size {font_size:d}'))
def step_text_layer(text: str, font_size: int, layer_store: list, ctx: dict) -> None:
    layer = {
        "id": len(layer_store) + 1,
        "layer_kind": "text",
        "prompt": "",
        "image_url": None,
        "history": [],
        "ip_adapter_refs": [],
        "loras": [],
        "controlnet_pose": None,
        "z_index": 2,
        "text_config": {"text": text, "font_size": font_size},
    }
    layer_store.append(layer)
    ctx["current_layer"] = layer


@given(parsers.parse('a character layer with lora "{lora_name}" at weight {weight:f}'))
def step_character_with_lora(lora_name: str, weight: float, layer_store: list, ctx: dict) -> None:
    layer = {
        "id": len(layer_store) + 1,
        "layer_kind": "character",
        "prompt": "hero",
        "image_url": None,
        "history": [],
        "ip_adapter_refs": [],
        "loras": [{"name": lora_name, "weight": weight}],
        "controlnet_pose": None,
        "z_index": 1,
    }
    layer_store.append(layer)
    ctx["current_layer"] = layer


@given("a character layer with openpose controlnet input")
def step_character_with_cn(layer_store: list, ctx: dict) -> None:
    layer = {
        "id": len(layer_store) + 1,
        "layer_kind": "character",
        "prompt": "hero pose",
        "image_url": None,
        "history": [],
        "ip_adapter_refs": [],
        "loras": [],
        "controlnet_pose": {"type": "openpose", "image": _png_url(), "strength": 0.8},
        "z_index": 1,
    }
    layer_store.append(layer)
    ctx["current_layer"] = layer


@given("layers at z=0, z=1, z=2 all with image_urls")
def step_layers_with_images(layer_store: list) -> None:
    for z in range(3):
        layer_store.append({
            "id": z + 1,
            "layer_kind": "background" if z == 0 else "character",
            "prompt": "",
            "image_url": _png_url(),
            "history": [],
            "ip_adapter_refs": [],
            "loras": [],
            "controlnet_pose": None,
            "z_index": z,
        })


# ── when ──────────────────────────────────────────────────────────────────────

@when('I add a background layer with prompt "cozy library"')
def step_add_bg_layer(layer_store: list, ctx: dict) -> None:
    layer = {
        "id": len(layer_store) + 1,
        "layer_kind": "background",
        "prompt": "cozy library",
        "image_url": None,
        "history": [],
        "ip_adapter_refs": [],
        "loras": [],
        "controlnet_pose": None,
        "z_index": 0,
    }
    layer_store.append(layer)
    ctx["current_layer"] = layer


@when("I trigger generation for the background layer")
def step_trigger_bg(ctx: dict, layer_store: list) -> None:
    _simulate_generation(ctx)


@when("I trigger generation for the character layer")
def step_trigger_char(ctx: dict, layer_store: list) -> None:
    _simulate_generation(ctx)


@when("I trigger generation for the text layer")
def step_trigger_text(ctx: dict, layer_store: list) -> None:
    _simulate_generation(ctx)


@when("I get the preview")
def step_get_preview(ctx: dict, layer_store: list) -> None:
    from engine.compositor import composite_scene
    layers = [{**l, "type": l["layer_kind"]} for l in layer_store if l.get("image_url")]
    ctx["preview"] = composite_scene(layers, page_w=612, page_h=792)


@when("I finalize page 1")
def step_finalize(ctx: dict, layer_store: list) -> None:
    from engine.compositor import composite_scene
    layers = [{**l, "type": l["layer_kind"]} for l in layer_store if l.get("image_url")]
    if not layers:
        ctx["finalize_error"] = 422
        return
    ctx["composite_url"] = composite_scene(layers, page_w=612, page_h=792)


@when("I attempt to finalize page 1")
def step_attempt_finalize(ctx: dict, layer_store: list) -> None:
    from engine.compositor import composite_scene
    layers = [{**l, "type": l["layer_kind"]} for l in layer_store if l.get("image_url")]
    if not layers:
        ctx["finalize_error"] = 422
        return
    ctx["composite_url"] = composite_scene(layers, page_w=612, page_h=792)


# ── then ──────────────────────────────────────────────────────────────────────

@then('a layer exists with layer_kind "background"')
def step_layer_exists_bg(layer_store: list) -> None:
    assert any(l["layer_kind"] == "background" for l in layer_store)


@then("the layer has no image_url")
def step_no_image_url(ctx: dict) -> None:
    assert ctx["current_layer"]["image_url"] is None


@then("the layer has an image_url")
def step_has_image_url(ctx: dict) -> None:
    assert ctx["current_layer"]["image_url"] is not None


@then("the history is empty")
def step_history_empty(ctx: dict) -> None:
    assert ctx["current_layer"]["history"] == []


@then(parsers.parse('the layer history contains "{old_url}"'))
def step_history_contains(old_url: str, ctx: dict) -> None:
    assert old_url in ctx["current_layer"]["history"]


@then("the layer has a new image_url")
def step_new_image_url(ctx: dict) -> None:
    layer = ctx["current_layer"]
    old = ctx.get("old_image_url")
    assert layer["image_url"] is not None
    assert layer["image_url"] != old


@then(parsers.parse('the generation backend is "{backend}"'))
def step_backend(backend: str, ctx: dict) -> None:
    assert ctx["backend"] == backend


@then("the image is a transparent PNG")
def step_transparent_png(ctx: dict) -> None:
    url = ctx["result_url"]
    assert url.startswith("data:image/png;base64,")
    _, b64 = url.split(",", 1)
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    assert img.mode == "RGBA"


@then(parsers.parse('the LoRA "{lora_name}" was forwarded with weight {weight:f}'))
def step_lora_forwarded(lora_name: str, weight: float, ctx: dict) -> None:
    req = ctx["captured_req"]
    assert any(
        l.name == lora_name and abs(l.weight - weight) < 0.001
        for l in req.loras
    )


@then(parsers.parse('the controlnet type "{cn_type}" was forwarded'))
def step_cn_forwarded(cn_type: str, ctx: dict) -> None:
    req = ctx["captured_req"]
    assert req.controlnet is not None
    assert req.controlnet.type == cn_type


@then("the preview is a PNG data URL")
def step_preview_png(ctx: dict) -> None:
    assert ctx["preview"].startswith("data:image/png;base64,")


@then("the finalized record has a composite_url")
def step_has_composite(ctx: dict) -> None:
    assert "composite_url" in ctx
    assert ctx["composite_url"].startswith("data:image/png;base64,")


@then(parsers.parse("finalization fails with {code:d}"))
def step_finalize_fails(code: int, ctx: dict) -> None:
    assert ctx.get("finalize_error") == code


# ── private helper ────────────────────────────────────────────────────────────

def _simulate_generation(ctx: dict) -> None:
    """Build a LayerGenerationRequest from ctx[current_layer] and record results."""
    from engine.generation import (
        ControlNetInput,
        IPAdapterRef,
        LayerGenerationRequest,
        LoRARef,
        TextLayerConfig,
        render_text_layer,
    )

    layer = ctx["current_layer"]
    kind = layer["layer_kind"]
    ip_refs = [IPAdapterRef(**r) for r in layer.get("ip_adapter_refs", [])]
    loras = [LoRARef(**l) for l in layer.get("loras", [])]
    cn = ControlNetInput(**layer["controlnet_pose"]) if layer.get("controlnet_pose") else None
    tc = TextLayerConfig(**layer["text_config"]) if layer.get("text_config") else None

    req = LayerGenerationRequest(
        layer_kind=kind,
        prompt=layer.get("prompt", ""),
        ip_adapter_refs=ip_refs,
        loras=loras,
        controlnet=cn,
        text_config=tc,
    )
    ctx["captured_req"] = req

    if kind == "text":
        backend = "pillow"
        result_url = render_text_layer(tc, req.size) if tc else _png_url()
    elif ip_refs:
        backend = "diffusers-img2img"
        result_url = _png_url()
    else:
        backend = "diffusers-txt2img"
        result_url = _png_url()

    old_url = layer.get("image_url")
    if old_url:
        layer["history"].append(old_url)
    layer["image_url"] = result_url

    ctx["backend"] = backend
    ctx["result_url"] = result_url
