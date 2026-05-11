# Layered Page Generation Pipeline — Specification

## Overview

Three-phase pipeline:

1. **Asset Registry** — named visual assets (character | setting | prop) each get
   a reference sheet generated once. Every page that features that asset uses
   the same sheet for IP-Adapter conditioning.

2. **Page Templates** — a page is a z-ordered stack of independently-generated
   layers. Each layer is regenerable in isolation. The composite is computed
   on demand; only the flat composite reaches the PDF.

3. **Finalization** — `POST /api/finalize` runs the Pillow compositor and
   writes the result to `finalized_pages`. PDF export draws from
   `finalized_pages.composite_url`.

---

## Asset Registry

### Data model — `asset_sheets`

| Field              | Type | Invariant |
|--------------------|------|-----------|
| book_key + asset_id | text | UNIQUE — upsert on conflict |
| kind               | text | character \| setting \| prop |
| reference_photos   | jsonb | all photos stored — no cap |
| sheet_image        | text | data URL; null until generated |
| lora_name          | text | filename relative to LORA_DIR |
| ip_adapter_weight  | real | default 0.8; clamped 0–1 |
| prompt_description | text | used when reference_photos is empty |

### Acceptance Criteria

| ID  | Criterion |
|-----|----------|
| AS-1 | Creating an asset with an existing (book_key, asset_id) upserts — no 409 |
| AS-2 | `generate-sheet` uses img2img when reference_photos is non-empty |
| AS-3 | `generate-sheet` uses txt2img when reference_photos is empty |
| AS-4 | `generate-sheet` applies background removal for kind ≠ "setting" |
| AS-5 | `generate-sheet` does NOT apply background removal for kind = "setting" |
| AS-6 | ip_adapter_weight defaults to 0.8 when omitted |
| AS-7 | All reference photos are stored without truncation |

---

## Page Templates

### Data model — `page_templates`

| Field       | Type | Invariant |
|-------------|------|-----------|
| book_key + page_number | text+int | UNIQUE — upsert on conflict |
| status      | text | draft \| ready \| finalized |
| layout      | jsonb | arbitrary UI metadata |

### Acceptance Criteria

| ID  | Criterion |
|-----|----------|
| PT-1 | Duplicate (book_key, page_number) upserts rather than errors |
| PT-2 | Deleting a template cascades DELETE to all its page_layers |
| PT-3 | status defaults to "draft" |

---

## Page Layers

### Data model — `page_layers`

| Field               | Type    | Invariant |
|---------------------|---------|----------|
| template_id         | int FK  | CASCADE DELETE from page_templates |
| layer_kind          | text    | background \| character \| text |
| z_index             | int     | 0 = back; higher = front |
| ip_adapter_refs     | jsonb   | [{asset_id, weight}]; resolved at generation time |
| loras               | jsonb   | [{name, weight}]; all stacked in single call |
| controlnet_pose     | jsonb   | {image, strength, type} |
| image_url           | text    | current generated data URL; null until first generation |
| history             | jsonb   | ordered list of previous image_urls |
| is_personalizable   | boolean | true → replaced during personalization |
| slot                | jsonb   | "full_page" or {x,y,w,h} fractions |
| text_config         | jsonb   | {text, font_size, font_color, align} |

### Acceptance Criteria

| ID  | Criterion |
|-----|----------|
| PL-1 | Triggering generation writes result to image_url and appends old value to history |
| PL-2 | IP-Adapter refs resolved from asset_sheets.sheet_image at generation time |
| PL-3 | character layers always have remove_background=True in the generation request |
| PL-4 | text layers call render_text_layer (Pillow) — never the image provider |
| PL-5 | Multiple LoRAs are stacked via set_adapters(names, weights=[...]) in one call |
| PL-6 | ControlNet preprocessing applied before passing image to model |
| PL-7 | Regenerating a layer that has no previous image_url leaves history empty |

---

## Personalization

### Acceptance Criteria

| ID  | Criterion |
|-----|----------|
| PE-1 | Only layers with is_personalizable=TRUE are replaced |
| PE-2 | With reference_photos: uses image_edit (img2img path) |
| PE-3 | Without reference_photos: uses generate_layer (txt2img path) |
| PE-4 | Each swapped layer's old image_url is appended to its history |
| PE-5 | Response body includes {swapped: N, customer_id, template_id} |
| PE-6 | Template with no personalizable layers returns swapped=0, 200 |

---

## Finalization

### Acceptance Criteria

| ID  | Criterion |
|-----|----------|
| FI-1 | Layers composited in z_index order using Pillow compositor |
| FI-2 | composite_url stored in finalized_pages, not in page_layers |
| FI-3 | Second call to finalize same (book_key, page_number, customer_id) upserts |
| FI-4 | No layers with image_urls → 422 Unprocessable Entity |
| FI-5 | pdf_ready defaults to false |

---

## DiffusersPipeline

### Acceptance Criteria

| ID  | Criterion |
|-----|----------|
| DP-1 | available() returns False when torch not installed — no exception |
| DP-2 | Model loading is lazy (first call to ensure_ready, not import time) |
| DP-3 | LoRA files loaded once; subsequent requests use cached adapter |
| DP-4 | Multiple LoRAs activated via set_adapters(names, weights) in one call |
| DP-5 | IP-Adapter scales set per-request via set_ip_adapter_scale([w1, w2, ...]) |
| DP-6 | ControlNet pipelines built via from_pipe() — share UNet with base pipeline |
| DP-7 | Canny preprocessing: cv2 if available, numpy threshold fallback |
| DP-8 | openpose/depth preprocessing: controlnet_aux if available, pass-through fallback |
| DP-9 | img2img path used when ref_pil is provided; txt2img when ref_pil is None |

---

## Key Invariants

1. `generate_layer()` never raises — worst case returns placeholder data URL
2. `image_url` history is append-only — regeneration never loses a prior image
3. IP-Adapter refs stored as asset_id+weight only; sheet_image resolved fresh at generation time
4. Background removal applied to all character layers; never to background layers
5. Text layers bypass all image generation — Pillow only
6. Compositor always receives layers with `type` key set from `layer_kind`
