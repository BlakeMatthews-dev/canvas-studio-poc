# ADR-001: Multi-Surface Site (Marketing + App + Brand Kit)

**Status:** Accepted
**Date:** 2026-05-09
**Related:** ADR-002 (brand foundation), ADR-003 (FastAPI cutover)

## Context

`canvas-studio-poc` started as a single-page React app: the
BookWizard at `/`. The Anthropic design bundles delivered three
additional surfaces that needed homes — a marketing site for the
Canvas Studio product, a marketing site for the Storybook Series
sub-product, and a brand-kit smoke test for the design system.

We had three options:

1. **One SPA with client routing** (`react-router`) — single Vite
   bundle, every surface in one app.
2. **Multiple Vite entries** — one HTML per surface, each with its
   own React tree, all built by the same Vite config.
3. **Separate repos per surface** — full isolation, slowest velocity.

## Decision

**Option 2 — multiple Vite entries.** Four HTML files at the repo
root, each with its own entry script, all built by `vite.config.js`'s
`rollupOptions.input`:

| Path | What | Entry script |
|------|------|--------------|
| `/` | Canvas Studio marketing site | `src/website.tsx` |
| `/storybook-series.html` | Storybook Series marketing site | `src/storybook-series.tsx` |
| `/app.html` | BookWizard / Workspace product app | `src/main.jsx` |
| `/brand-sample.html` | Brand kit visual smoke test | `src/brand-sample.tsx` |

Cross-links are plain anchors. The marketing site's "Begin a book"
CTA goes to `/app.html`; the BookWizard's wordmark links back to `/`.

## Rationale

- **Independent bundle size.** The BookWizard pulls Konva, dnd-kit,
  Tiptap, etc. The marketing pages don't. Separate entries keep each
  surface's bundle close to what it actually needs.
- **No SPA shell on marketing pages.** Static HTML loads instantly;
  marketing pages don't need a route resolver between user and pixel.
- **No router needed.** Adding `react-router` for two product pages
  is overkill, and the extra dep would land in the BookWizard bundle.
- **Easier to evolve.** When a marketing surface graduates to a real
  CMS-backed Next.js site, it lifts out cleanly. The BookWizard is
  the one surface that *does* need an SPA, and it stays one.

## Consequences

- `vite.config.js` has four rollup inputs and grows by one when a
  new surface lands. Cheap.
- Cross-page navigation is full-page reloads. Marketing-to-marketing
  is fine; marketing-to-app is fine. App-internal navigation stays
  client-side as it always was.
- Build artefacts: `dist/` ships four HTML files plus their per-page
  JS chunks. The brand module (`src/brand/`) is shared and code-
  splits naturally.

## Out of scope

- A single SPA with client routing. Reconsider if the marketing
  pages start needing dynamic data (blog, gallery, CMS content) —
  Next.js or a Payload-backed homepage repo is the better answer
  there.
- Mounting the BookWizard at `/` instead of `/app.html`. The
  marketing site is the front door for the product; the app is what
  you launch into.

## Source references

- `vite.config.js` — rollup inputs.
- `index.html`, `storybook-series.html`, `app.html`, `brand-sample.html`.
- `src/website/CanvasStudioWebsite.tsx`, `src/website/StorybookSeries.tsx`.
