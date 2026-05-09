# ADR-002: Brand Foundation Module

**Status:** Accepted
**Date:** 2026-05-09
**Related:** ADR-001 (multi-surface site)

## Context

The Anthropic design bundles delivered a complete brand identity for
Rooted & Revitalized (the parent brand) and the Canvas Studio sub-
brand: palette, type, motifs, primitives, voice. Canvas Studio's
existing UI used a tech-tool aesthetic (phosphor green, JetBrains
Mono) that did not match.

Three things needed to fall out of the same module:

1. CSS tokens consumed by stylesheets and inline styles.
2. JSX primitives (Wordmark, Sprig, Sparkle, Leaf, BotanicalBranch,
   TaglineRow, CategoryPill, …) for use across surfaces.
3. A Mantine theme so the BookWizard's interactive components share
   the brand without per-component restyling.

## Decision

`src/brand/` is a self-contained brand module:

```
src/brand/
├── tokens.css             # CSS variables: --rr-sage-*, --rr-cream-*, …
├── tokens.ts              # Same tokens as TS constants
├── theme.ts               # Mantine theme override
├── voice.ts               # Tagline, categories, em-dash linter
├── primitives/            # SVG/text brand atoms
├── motifs/                # WatercolorWash, TornPaper, PaperCard
├── README.md              # How to consume + brand rules
└── index.ts               # Barrel
```

Three deliberate choices:

### 1. Token names are namespaced `--rr-*`

The existing `index.css` defined `--ink-0 .. --ink-5`, `--phosphor`,
`--text`, etc. Brand tokens use `--rr-*` (Rooted & Revitalized) to
avoid collision. Inside scoped wrappers (`.canvas-studio-website`,
`.storybook-series-website`), the brand tokens are aliased to
unprefixed names so the design source can be ported close to verbatim.

### 2. Mantine for the BookWizard, raw for marketing

The BookWizard needs rich interactive components (multi-step wizard,
panels, generation tray, modals, properties grids). Mantine ships
those and themes via `MantineProvider`. The marketing pages are
mostly bespoke layout; raw HTML + scoped CSS is cleaner there.

### 3. Sub-brand strategy: token override, not primitive fork

When Canvas Studio diverges from Rooted & Revitalized as a sub-brand,
the divergence ships as `tokens-bookwizard.css` overriding accent
tokens (palette, script font). The primitives (Wordmark, Sprig,
Sparkle, …) stay shared; only the values they read change.

## Rationale

- **One source of truth for shape.** Tokens are CSS-first; TS exports
  the same values for inline-style consumers. There's no second
  authoring path that can drift.
- **Sub-branding is cheap.** Overriding 5–10 accent tokens in a
  sibling stylesheet covers most of what a sub-brand differs in.
- **Marketing pages stay framework-light.** The brand foundation is
  the shared dependency; the marketing pages don't import Mantine.

## Consequences

- The BookWizard's existing class names (`.app-shell`, `.topbar`,
  `.layer-item`, …) keep working; their token values now resolve to
  brand colours. PR #3 (BookWizard restyle) demonstrates this — no
  JSX changes, only token reassignment.
- Adding a third surface (e.g. an admin UI) is a one-file `tokens.css`
  import + optional `MantineProvider` wrap.
- The brand module has no dependencies of its own beyond React and
  Mantine; it's portable to a future shared package the moment a
  homepage repo materialises.

## Voice rule

The brand voice is part of the foundation. `voice.ts` exposes:

- `tagline` — `Rooted in Growth ✦ Revitalized through Creating`
- `categories` — `Plants, DIY Projects, Handmade Pieces, Real Life`
- `stripEmDashes(s)` / `lintVoice(s)` — enforce the no-em-dash rule
  from chat3 of the design bundle

See `frontend/VOICE.md` for the full voice contract.

## Out of scope

- Visual regression testing (Percy / Chromatic) — separate effort.
- A custom icon library — the design bundle's icon set was unfinished;
  we use lucide via shadcn/Mantine integration for now.
- Sub-brand naming and direction — blocked on product input.

## Source references

- `src/brand/README.md` — usage notes.
- `src/website/website.css`, `src/website/storybook-series.css` —
  examples of scoped token aliasing.
- Anthropic design bundle "Rooted & Revitalized Design System" —
  source of palette, type, motifs, primitives, and voice.
