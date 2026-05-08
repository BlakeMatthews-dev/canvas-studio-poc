# Rooted & Revitalized — Brand Module

Baseline theming for Canvas Studio. Ported from the Rooted & Revitalized
design system. Earthy, botanical, slow-living. Sage and cream, with clay
accents and gentle signal colors. Display serif paired with a flowing script.

## What's here

```
brand/
├── tokens.css        # CSS custom properties (--rr-*) and .rr utility classes
├── tokens.ts         # same tokens as TS constants for JS consumers
├── theme.ts          # Mantine theme override (brandTheme)
├── voice.ts          # tagline, categories, em-dash linter
├── primitives/       # SVG/text brand atoms (Wordmark, Sprig, Sparkle, …)
├── motifs/           # decorative containers (WatercolorWash, TornPaper, PaperCard)
├── index.ts          # barrel
└── README.md         # this file
```

## Voice rules

- **No em dashes.** Use commas, periods, " and ", or " then ".
- Categories are: Plants, DIY Projects, Handmade Pieces, Real Life.
- Tagline lockup: **Rooted in Growth ✦ Revitalized through Creating**

`voice.ts` exposes `stripEmDashes()` and `lintVoice()` helpers.

## How to use

### Just the tokens (no Mantine)

```tsx
import '@/brand/tokens.css';

<div className="rr">
  <h1 className="rr-h1">Slow living, well-considered.</h1>
  <p className="rr-lead">Some text in the brand voice.</p>
</div>
```

The `.rr` wrapper opts content into the brand styling so it doesn't
collide with the existing Canvas Studio styles.

### Brand primitives

```tsx
import { Wordmark, TaglineRow, CategoryPill, Sprig } from '@/brand';

<Wordmark scale={2} />
<TaglineRow />
<CategoryPill items={["Plants", "DIY"]} />
<Sprig leafCount={9} />
```

### Mantine + brand theme

```tsx
import { MantineProvider } from '@mantine/core';
import { brandTheme } from '@/brand';
import '@mantine/core/styles.css';
import '@/brand/tokens.css';

<MantineProvider theme={brandTheme}>
  {/* Mantine components below get sage primary, pill buttons,
      uppercase-tracked labels, paper shadows, etc. */}
</MantineProvider>
```

**Important:** wrapping the existing `App` in `MantineProvider` will shift
the look of the current Canvas Studio screens (Mantine adds resets and
component styles). The brand-sample entry (`brand-sample.html`) shows the
brand in isolation; the main app stays untouched in this baseline PR.

## Visual smoke test

```bash
npm install
npm run dev
# then open http://localhost:5173/brand-sample.html
```

## Status

- v1: tokens, primitives, motifs, Mantine theme, voice helpers. **Ported,
  not yet validated against the existing screens.**
- Icons (lucide for now). The Rooted & Revitalized hand-drawn icon set was
  unfinished in the source bundle; revisit if/when needed.
- The BookWizard sub-brand (child-friendly variant) is **not** in this PR.
  When defined, it lands as `tokens-bookwizard.css` overriding accent tokens.

## Provenance

Tokens, primitives, and motifs are ported verbatim from
`rooted-revitalized-design-system/project/colors_and_type.css` and
`brand-primitives.jsx`. Iteration history lives in the design bundle's
`chats/` transcripts.
