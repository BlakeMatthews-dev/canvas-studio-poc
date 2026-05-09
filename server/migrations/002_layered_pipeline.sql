-- 002_layered_pipeline.sql
-- Asset registry + layered page pipeline tables.

CREATE TABLE IF NOT EXISTS asset_sheets (
    id                  SERIAL PRIMARY KEY,
    book_key            TEXT NOT NULL,
    asset_id            TEXT NOT NULL,
    kind                TEXT NOT NULL CHECK (kind IN ('character', 'setting', 'prop')),
    name                TEXT NOT NULL,
    reference_photos    JSONB NOT NULL DEFAULT '[]',
    sheet_image         TEXT,
    lora_name           TEXT,
    ip_adapter_weight   REAL NOT NULL DEFAULT 0.8,
    prompt_description  TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (book_key, asset_id)
);

CREATE INDEX IF NOT EXISTS asset_sheets_book_key ON asset_sheets (book_key);

-- ----

CREATE TABLE IF NOT EXISTS page_templates (
    id              SERIAL PRIMARY KEY,
    book_key        TEXT NOT NULL,
    page_number     INT  NOT NULL,
    scene_id        TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    layout          JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (book_key, page_number)
);

CREATE INDEX IF NOT EXISTS page_templates_book_key ON page_templates (book_key);

-- ----

CREATE TABLE IF NOT EXISTS page_layers (
    id                   SERIAL PRIMARY KEY,
    template_id          INT  NOT NULL REFERENCES page_templates(id) ON DELETE CASCADE,
    book_key             TEXT NOT NULL,
    page_number          INT  NOT NULL,
    layer_kind           TEXT NOT NULL CHECK (layer_kind IN ('background', 'character', 'text')),
    z_index              INT  NOT NULL DEFAULT 0,
    asset_id             TEXT,
    prompt               TEXT,
    negative_prompt      TEXT,
    ip_adapter_refs      JSONB NOT NULL DEFAULT '[]',
    loras                JSONB NOT NULL DEFAULT '[]',
    controlnet_pose      JSONB,
    size                 TEXT NOT NULL DEFAULT '1024x1024',
    quality              TEXT NOT NULL DEFAULT 'draft',
    seed                 BIGINT,
    image_url            TEXT,
    slot                 JSONB,
    text_config          JSONB,
    is_personalizable    BOOLEAN NOT NULL DEFAULT FALSE,
    personalization_slot TEXT,
    history              JSONB NOT NULL DEFAULT '[]',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS page_layers_template_id    ON page_layers (template_id);
CREATE INDEX IF NOT EXISTS page_layers_book_key       ON page_layers (book_key, page_number);
CREATE INDEX IF NOT EXISTS page_layers_personalizable ON page_layers (is_personalizable)
    WHERE is_personalizable = TRUE;

-- ----

CREATE TABLE IF NOT EXISTS finalized_pages (
    id            SERIAL PRIMARY KEY,
    book_key      TEXT    NOT NULL,
    page_number   INT     NOT NULL,
    customer_id   TEXT    NOT NULL DEFAULT '',
    template_id   INT     REFERENCES page_templates(id),
    composite_url TEXT    NOT NULL,
    upscaled_url  TEXT,
    pdf_ready     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (book_key, page_number, customer_id)
);

CREATE INDEX IF NOT EXISTS finalized_pages_book_key ON finalized_pages (book_key);
