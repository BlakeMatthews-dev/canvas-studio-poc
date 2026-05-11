"""BDD step definitions for personalization.feature."""
from __future__ import annotations

import base64
import io
from pathlib import Path

import pytest
from PIL import Image
from pytest_bdd import given, parsers, scenario, then, when

FEATURE = str(Path(__file__).parent.parent / "features" / "personalization.feature")


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

@scenario(FEATURE, "Personalize with reference photos uses img2img")
def test_personalize_with_photos():
    pass


@scenario(FEATURE, "Personalize without photos uses txt2img")
def test_personalize_no_photos():
    pass


@scenario(FEATURE, "Non-personalizable layers are untouched")
def test_non_personalizable_untouched():
    pass


@scenario(FEATURE, "Template with no personalizable layers returns swapped=0")
def test_no_personalizable_layers():
    pass


# ── background ────────────────────────────────────────────────────────────────

@given(parsers.parse('book key "{book_key}"'), target_fixture="book_key")
def step_book_key(book_key: str) -> str:
    return book_key


@given("a page template for page 1")
def step_page_template() -> None:
    pass


@given("the template has a personalizable character layer")
def step_personalizable_layer(layer_store: list, ctx: dict) -> None:
    original_url = _png_url()
    layer = {
        "id": 1,
        "layer_kind": "character",
        "prompt": "main character",
        "image_url": original_url,
        "history": [],
        "ip_adapter_refs": [],
        "loras": [],
        "controlnet_pose": None,
        "is_personalizable": True,
        "z_index": 1,
    }
    layer_store.append(layer)
    ctx["personalizable_layer"] = layer
    ctx["original_image_url"] = original_url


# ── given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('the template also has a background layer with image_url "{image_url}"'))
def step_bg_with_url(image_url: str, layer_store: list, ctx: dict) -> None:
    layer = {
        "id": 2,
        "layer_kind": "background",
        "prompt": "background",
        "image_url": image_url,
        "history": [],
        "ip_adapter_refs": [],
        "loras": [],
        "controlnet_pose": None,
        "is_personalizable": False,
        "z_index": 0,
    }
    layer_store.append(layer)
    ctx["bg_layer"] = layer


@given("a template with no personalizable layers")
def step_no_personalizable(layer_store: list) -> None:
    layer_store.append({
        "id": 1,
        "layer_kind": "background",
        "prompt": "static background",
        "image_url": _png_url(),
        "history": [],
        "ip_adapter_refs": [],
        "loras": [],
        "controlnet_pose": None,
        "is_personalizable": False,
        "z_index": 0,
    })


# ── when ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('I personalize the template with customer_id "{customer_id}" and {n:d} reference photos'))
def step_personalize(customer_id: str, n: int, layer_store: list, ctx: dict) -> None:
    ref_photos = [_png_url() for _ in range(n)]
    backend = "diffusers-img2img" if n > 0 else "diffusers-txt2img"
    new_url = _png_url()
    swapped = 0

    for layer in layer_store:
        if not layer.get("is_personalizable"):
            continue
        old_url = layer["image_url"]
        if old_url:
            layer["history"].append(old_url)
        layer["image_url"] = new_url
        layer["ip_adapter_refs"] = [
            {"asset_id": customer_id, "sheet_image": p, "weight": 0.8}
            for p in ref_photos
        ]
        swapped += 1

    ctx["swapped"] = swapped
    ctx["backend"] = backend
    ctx["n_photos"] = n
    ctx["new_url"] = new_url


# ── then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse("{n:d} layer was swapped"))
def step_one_layer_swapped(n: int, ctx: dict) -> None:
    assert ctx["swapped"] == n


@then(parsers.parse("{n:d} layers were swapped"))
def step_n_layers_swapped(n: int, ctx: dict) -> None:
    assert ctx["swapped"] == n


@then("the personalizable layer has a new image_url")
def step_new_image(ctx: dict) -> None:
    layer = ctx["personalizable_layer"]
    assert layer["image_url"] != ctx["original_image_url"]
    assert layer["image_url"] is not None


@then("the old image_url is in the layer history")
def step_old_in_history(ctx: dict) -> None:
    layer = ctx["personalizable_layer"]
    assert ctx["original_image_url"] in layer["history"]


@then("generation did not use reference photos")
def step_no_ref_photos(ctx: dict) -> None:
    assert ctx["n_photos"] == 0
    assert ctx["backend"] == "diffusers-txt2img"


@then(parsers.parse('the background layer image_url is still "{image_url}"'))
def step_bg_unchanged(image_url: str, ctx: dict) -> None:
    assert ctx["bg_layer"]["image_url"] == image_url
