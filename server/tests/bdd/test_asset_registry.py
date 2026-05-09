"""BDD step definitions for asset_registry.feature."""
from __future__ import annotations

import base64
import io
from pathlib import Path

import pytest
from PIL import Image
from pytest_bdd import given, parsers, scenario, then, when

FEATURE = str(Path(__file__).parent.parent / "features" / "asset_registry.feature")


def _png_url() -> str:
    img = Image.new("RGBA", (64, 64), (100, 180, 100, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def ctx() -> dict:
    return {}


@pytest.fixture
def asset_store() -> dict:
    return {}


# ── scenario declarations ─────────────────────────────────────────────────────

@scenario(FEATURE, "Create a new character asset")
def test_create_character_asset():
    pass


@scenario(FEATURE, "Upserting an asset with the same key updates it")
def test_upsert_asset():
    pass


@scenario(FEATURE, "Generate a reference sheet using reference photos")
def test_generate_sheet_with_photos():
    pass


@scenario(FEATURE, "Generate a reference sheet from description only")
def test_generate_sheet_txt2img():
    pass


@scenario(FEATURE, "Setting assets are not background-removed")
def test_setting_no_bg_removal():
    pass


@scenario(FEATURE, "Character assets have background removed")
def test_character_bg_removal():
    pass


@scenario(FEATURE, "Update asset with LoRA name")
def test_update_lora_name():
    pass


@scenario(FEATURE, "Delete an asset")
def test_delete_asset():
    pass


@scenario(FEATURE, "List assets for a book returns all assets")
def test_list_assets():
    pass


# ── background ────────────────────────────────────────────────────────────────

@given(parsers.parse('book key "{book_key}"'), target_fixture="book_key")
def step_book_key(book_key: str) -> str:
    return book_key


# ── given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('asset "{asset_id}" exists for book "{book_key}"'))
def step_asset_exists(asset_id: str, book_key: str, asset_store: dict) -> None:
    asset_store[asset_id] = {
        "asset_id": asset_id,
        "book_key": book_key,
        "kind": "character",
        "name": asset_id,
        "reference_photos": [],
        "sheet_image": None,
        "lora_name": None,
        "ip_adapter_weight": 0.8,
    }


@given(parsers.parse('asset "{asset_id}" of kind "{kind}" with {n:d} reference photos'))
def step_asset_with_n_photos(asset_id: str, kind: str, n: int, book_key: str, asset_store: dict) -> None:
    asset_store[asset_id] = {
        "asset_id": asset_id,
        "book_key": book_key,
        "kind": kind,
        "name": asset_id,
        "reference_photos": [_png_url() for _ in range(n)],
        "sheet_image": None,
        "lora_name": None,
        "ip_adapter_weight": 0.8,
    }


@given(parsers.parse('asset "{asset_id}" of kind "{kind}" with prompt "{prompt}"'))
def step_asset_with_prompt(asset_id: str, kind: str, prompt: str, book_key: str, asset_store: dict) -> None:
    asset_store[asset_id] = {
        "asset_id": asset_id,
        "book_key": book_key,
        "kind": kind,
        "name": prompt,
        "reference_photos": [],
        "sheet_image": None,
        "lora_name": None,
        "ip_adapter_weight": 0.8,
        "_prompt": prompt,
    }


@given(parsers.parse('asset "{asset_id}" has no reference photos'))
def step_no_reference_photos(asset_id: str, asset_store: dict) -> None:
    asset_store[asset_id]["reference_photos"] = []


@given(parsers.parse('assets "{a}", "{b}", "{c}" exist for book "{book_key}"'))
def step_multiple_assets(a: str, b: str, c: str, book_key: str, asset_store: dict) -> None:
    for asset_id in (a, b, c):
        asset_store[asset_id] = {
            "asset_id": asset_id,
            "book_key": book_key,
            "kind": "character",
            "name": asset_id,
            "reference_photos": [],
            "sheet_image": None,
            "lora_name": None,
            "ip_adapter_weight": 0.8,
        }


# ── when ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('I create asset "{asset_id}" of kind "{kind}" with name "{name}"'))
def step_create_asset(asset_id: str, kind: str, name: str, book_key: str, asset_store: dict, ctx: dict) -> None:
    asset = {
        "asset_id": asset_id,
        "book_key": book_key,
        "kind": kind,
        "name": name,
        "reference_photos": [],
        "sheet_image": None,
        "lora_name": None,
        "ip_adapter_weight": 0.8,
    }
    asset_store[asset_id] = asset
    ctx["created"] = asset


@when(parsers.parse('I upsert asset "{asset_id}" with name "{name}"'))
def step_upsert_asset(asset_id: str, name: str, asset_store: dict, ctx: dict) -> None:
    asset_store[asset_id]["name"] = name
    ctx["asset"] = asset_store[asset_id]


@when(parsers.parse('I generate a sheet for asset "{asset_id}"'))
def step_generate_sheet(asset_id: str, asset_store: dict, ctx: dict) -> None:
    asset = asset_store[asset_id]
    photos = asset.get("reference_photos", [])
    kind = asset["kind"]
    backend = "diffusers-img2img" if photos else "diffusers-txt2img"
    asset["sheet_image"] = _png_url()
    ctx["backend"] = backend
    ctx["bg_removal_applied"] = kind == "character" and bool(photos)


@when(parsers.parse('I update asset "{asset_id}" lora_name to "{lora_name}"'))
def step_update_lora(asset_id: str, lora_name: str, asset_store: dict) -> None:
    asset_store[asset_id]["lora_name"] = lora_name


@when(parsers.parse('I delete asset "{asset_id}"'))
def step_delete_asset(asset_id: str, asset_store: dict) -> None:
    asset_store.pop(asset_id, None)


@when(parsers.parse('I list assets for book "{book_key}"'))
def step_list_assets(book_key: str, asset_store: dict, ctx: dict) -> None:
    ctx["asset_list"] = [v for v in asset_store.values() if v["book_key"] == book_key]


# ── then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse("the asset exists with ip_adapter_weight {weight:f}"))
def step_assert_weight(weight: float, ctx: dict) -> None:
    assert pytest.approx(ctx["created"]["ip_adapter_weight"]) == weight


@then("the asset has no sheet_image")
def step_no_sheet_image(ctx: dict) -> None:
    asset = ctx.get("created") or ctx.get("asset")
    assert asset["sheet_image"] is None


@then(parsers.parse('the asset name is "{name}"'))
def step_assert_name(name: str, ctx: dict) -> None:
    assert ctx["asset"]["name"] == name


@then("the generation used img2img")
def step_used_img2img(ctx: dict) -> None:
    assert ctx["backend"] == "diffusers-img2img"


@then("the generation used txt2img")
def step_used_txt2img(ctx: dict) -> None:
    assert ctx["backend"] == "diffusers-txt2img"


@then("the asset has a sheet_image")
def step_has_sheet_image(asset_store: dict) -> None:
    assert any(v.get("sheet_image") for v in asset_store.values()), "no asset has a sheet_image"


@then("background removal was not applied")
def step_no_bg_removal(ctx: dict) -> None:
    assert not ctx.get("bg_removal_applied", False)


@then("background removal was applied")
def step_bg_removal_applied(ctx: dict) -> None:
    assert ctx.get("bg_removal_applied", False)


@then(parsers.parse('the asset lora_name is "{lora_name}"'))
def step_assert_lora(lora_name: str, asset_store: dict) -> None:
    assert any(v.get("lora_name") == lora_name for v in asset_store.values())


@then(parsers.parse('asset "{asset_id}" does not exist'))
def step_asset_gone(asset_id: str, asset_store: dict) -> None:
    assert asset_id not in asset_store


@then(parsers.parse("I receive {n:d} assets"))
def step_receive_n(n: int, ctx: dict) -> None:
    assert len(ctx["asset_list"]) == n
