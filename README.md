# Canvas Studio POC

A storybook studio for the people you love most. Three product
surfaces and a brand kit, built on a shared brand foundation.

## Surfaces

| Path | What |
|------|------|
| `/` | Canvas Studio marketing site (custom illustrated children's books) |
| `/storybook-series.html` | Storybook Series marketing site (curated, ready-before-bedtime) |
| `/app.html` | BookWizard / Workspace — the actual product |
| `/brand-sample.html` | Brand kit visual smoke test |

## Stack

- **Frontend:** React 19 + Vite + TypeScript (TypeScript and JSX
  coexist; new code prefers TypeScript).
- **UI:** Mantine 7 themed to the Rooted & Revitalized brand
  (sage / cream / clay / signal palette). Marketing pages use raw
  HTML + scoped CSS.
- **Canvas:** Konva via react-konva for layered editing, dnd-kit
  for layer reordering and asset library.
- **Animation:** Motion (Framer Motion) for UI micro-interactions.
- **API:** FastAPI (`server/main.py`) on `:5174`, talking to
  Postgres on `:5440`. The Vite dev server proxies `/api → :5174`
  and `/litellm → :4000`.
- **Print:** Lulu Print-on-Demand via a separate Python service at
  `LULU_SERVICE_URL` (defaults to `:8260`).

## Getting started

```bash
# 1. Install Node deps
npm install

# 2. Install Python deps for the API server (one-time)
npm run server:install

# 3. Start dev (uvicorn + vite together)
npm run dev
```

Open `http://localhost:5173/` for the marketing site, or
`http://localhost:5173/app.html` for the BookWizard.

## Layout

```
.
├── index.html                     # marketing site entry
├── storybook-series.html          # series page entry
├── app.html                       # BookWizard entry
├── brand-sample.html              # brand kit entry
├── src/
│   ├── brand/                     # brand foundation (ADR-002)
│   │   ├── tokens.css             # CSS variables (--rr-*)
│   │   ├── tokens.ts              # TS constants
│   │   ├── theme.ts               # Mantine theme override
│   │   ├── voice.ts               # tagline + categories + em-dash linter
│   │   ├── primitives/            # Wordmark, Sprig, Sparkle, Leaf, …
│   │   ├── motifs/                # WatercolorWash, TornPaper, PaperCard
│   │   └── README.md
│   ├── website/
│   │   ├── CanvasStudioWebsite.tsx
│   │   ├── StorybookSeries.tsx
│   │   ├── website.css
│   │   └── storybook-series.css
│   ├── components/                # BookWizard / Workspace / Layer panel / …
│   ├── lib/                       # persistence, templates, characters, …
│   ├── App.jsx                    # BookWizard root
│   ├── main.jsx                   # /app.html entry
│   ├── website.tsx                # / entry
│   ├── storybook-series.tsx       # /storybook-series.html entry
│   └── brand-sample.tsx           # /brand-sample.html entry
├── server/
│   ├── main.py                    # FastAPI app (ADR-003)
│   ├── requirements.txt           # Python deps
│   ├── export_book.py             # PDF export (subprocess from main.py)
│   ├── lulu/                      # Lulu print client
│   ├── mcp/                       # canvas pipeline, illustration, refinement
│   ├── models/                    # SQLAlchemy models
│   ├── orchestrator/              # job orchestration
│   └── templates/                 # story templates
├── docs/
│   ├── ADR-001-multi-surface-site.md
│   ├── ADR-002-brand-foundation.md
│   ├── ADR-003-fastapi-cutover.md
│   └── VOICE.md
├── alembic/                       # DB migrations
├── docker-compose.yml             # local Postgres on :5440
├── package.json
├── vite.config.js
├── tsconfig.json
└── eslint.config.js
```

## ADRs

Architectural decisions live under `docs/`:

- **[ADR-001](docs/ADR-001-multi-surface-site.md)** — multiple Vite
  entries vs. SPA routing.
- **[ADR-002](docs/ADR-002-brand-foundation.md)** — `src/brand/`
  module, namespacing, Mantine choice, sub-brand strategy.
- **[ADR-003](docs/ADR-003-fastapi-cutover.md)** — Express → FastAPI.
- **[VOICE.md](docs/VOICE.md)** — brand voice contract (no em dashes,
  Story Conductor framing, etc.).

Engine-side ADRs covering the typed canvas model
(`LayerKind` / scene graph / world style / etc.) live in the
[maistro-engine repo](https://github.com/BlakeMatthews-dev/maistro-engine):
ADR-039 through ADR-045.

## Scripts

| Command | What |
|---------|------|
| `npm run dev` | uvicorn + vite together |
| `npm run server` | uvicorn only |
| `npm run server:install` | `pip install -r server/requirements.txt` |
| `npm run build` | Vite production build (all 4 entries) |
| `npm run preview` | Serve the production build |
| `npm run test` | Vitest |
| `npm run lint` | ESLint |

## Voice rule

**No em dashes.** Use commas, periods, " and ", or " then " instead.
Run `lintVoice(text)` from `src/brand/voice.ts` on user-facing copy
before committing. See [docs/VOICE.md](docs/VOICE.md) for the full
voice contract.

## Provenance

The brand and the marketing copy were ported from three Anthropic
design bundles. Iteration history (including the chat3 transcripts
with the voice rules and the Story Conductor framing) lives in the
design bundle archives, not in this repo. PR descriptions for #1
through #5 reference them.
