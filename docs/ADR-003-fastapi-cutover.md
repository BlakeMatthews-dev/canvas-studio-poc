# ADR-003: Express → FastAPI Cutover

**Status:** Accepted
**Date:** 2026-05-09
**Related:** maistro-engine#ADR-045 (canvas-studio ↔ engine cutover)

## Context

`server.js` was a 378-line Express app speaking to Postgres on `:5440`,
proxying the Lulu Python service, and shelling out to `export_book.py`.
Every other Python service in `server/` (lulu, mcp, models, orchestrator)
already uses FastAPI/uvicorn. The Express tier was the odd one out —
two runtimes (Node + Python), two dependency managers (npm + pip), one
team.

Two paths forward:

1. **Self-contained FastAPI in canvas-studio-poc** — same routes, same
   wire shape, same Postgres on `:5440`. Just swap Node for Python.
2. **Cut over to maistro-engine's `/v2/canvas/*`** — the typed routes
   from ADR-042. Bigger change: forces the data-model unification
   (LayerRecord JSONB → AssetInstance typed) at the same time.

## Decision

**Option 1.** PR #5 retired `server.js` and replaced it with
`server/main.py` — a small FastAPI app preserving the legacy `/api/...`
shape against the same Postgres.

The cutover to the engine's `/v2/canvas/*` is a separate effort
tracked at `maistro-engine#ADR-045`, sequenced after that ADR's Phase 3
data backfill.

## Rationale

- **Lowest-risk first step.** Same routes, same wire shape, same
  Postgres. Frontend code is unchanged. The Vite proxy at
  `/api → :5174` keeps working.
- **One runtime down.** No more Node + Python split for the API
  layer. `npm run dev` now invokes uvicorn instead of `node server.js`.
- **Defers the data-model unification.** That decision affects every
  call site in the frontend; doing it at the same time as the
  Node-tier removal multiplies risk without benefit.

## Consequences

- `package.json` drops `express`, `cors`, `pg` and adds a
  `server:install` script that runs `pip install -r
  server/requirements.txt`.
- `server/main.py` uses `psycopg[binary]` + `psycopg-pool` for
  Postgres, `httpx` for the Lulu proxy, and stdlib subprocess for
  `export_book.py`. No new business logic.
- Behaviour preserved verbatim: `safe_key` sanitisation matches the
  Express implementation; `savedAt` timestamps are server-generated;
  Lulu errors are mapped to 502.
- The frontend continues to talk to JSONB blobs. The typed
  `LayerKind` model from `maistro-engine` is *available* at
  `/v2/canvas/*` but not yet used here.

## Future cutover

When `maistro-engine` ADR-045 Phase 3 closes (legacy data backfilled
to `asset_instances`):

- Phase A here: add an opt-in proxy mode (`MAISTRO_MIRROR=on`) that
  calls `/v2/canvas/*` in parallel and logs divergences.
- Phase B: switch reads to engine-first.
- Phase C: switch writes; retire the local `:5440` Postgres.

Per-phase rollback is a feature-flag flip (`MAISTRO_MIRROR`,
`MAISTRO_READS`, `MAISTRO_WRITES`).

## Out of scope

- Authentication beyond the existing CORS-allow-all stance —
  follow-up when the engine cutover defines an auth boundary.
- Replacing the Lulu print proxy at `/api/print/*` — it's already
  a thin pass-through to the Python Lulu service, not engine-bound.
- Adding tests at the FastAPI layer — the legacy server.js had none;
  this PR preserves that posture. Integration tests land alongside
  the engine cutover.

## Source references

- PR #5 (this PR's parent landed it).
- `server/main.py` — FastAPI app.
- `server/requirements.txt` — Python deps.
- `package.json` — `dev`, `server`, `server:install` scripts.
