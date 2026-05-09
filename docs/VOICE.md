# VOICE.md — Canvas Studio Brand Voice

The voice rules below are a contract. They apply to all user-facing
copy across `/`, `/storybook-series.html`, `/app.html`, and any future
surface. They were established in chat3 of the Anthropic design
bundle and are codified here so future contributors can find them.

## Hard rules

### 1. No em dashes.

Use commas, periods, "and", or "then" instead. The brand reads slow
and warm; em dashes read clipped and modern.

```
✗  "It saves itself — without asking."
✓  "It saves itself, without asking."
✓  "It saves itself. Without asking."
```

`src/brand/voice.ts` exposes `stripEmDashes()` and `lintVoice()` —
use them when you accept user-facing text into a template.

### 2. No clipped tech-bro phrasing.

Avoid: "leverage", "powered by AI", "next-generation", "phased
pipeline", "enterprise-grade", "cutting-edge."

Prefer: "made", "shaped", "tucked away", "kept", "with care",
"with patience", "looked after."

### 3. Honest about the AI.

If software is doing something, say so plainly without dressing it
up. The "Honest about the magic" band on the Canvas Studio site is
the canonical example:

> We'll be honest. There is software in here, and ours is led by an
> AI Engineer in Residence who's worked deep inside the AI world and
> the studios behind some of the most beloved children's stories
> ever told. Our **Story Conductor** guides an ensemble of AI to
> compose your tale like magic, and you finish it in your own voice,
> with the touch that makes every book a perfect symphony of
> *love, magic, and family*.

### 4. The user is the parent. The protagonist is the child.

Hero copy, CTAs, and the AI Engineer in Residence framing all
position the parent as the editor, conductor, and final voice. The
child is the hero of the book, never the user.

### 5. No diagnosis-related SEO terms in visible copy.

The Storybook Series page is for parents of neurodivergent children
in part. Diagnosis terms (autism, ADHD, sensory processing, etc.) go
in `<meta>` tags and structured-data hidden landing variants, not in
the visible body. The visible voice is "for the days that ask the
most" and "for the moments when [their feelings get too big to
hold]."

## Vocabulary

### Categories

`Plants · DIY Projects · Handmade Pieces · Real Life`

These are the parent-brand pillars from Rooted & Revitalized. Canvas
Studio is one outlet of the parent brand; sub-brand vocabulary may
extend this list but should not contradict it.

### Roles

- **AI Engineer in Residence** — the human shaping the AI ensemble.
  Background phrased in capabilities, not company names: "deep
  inside the AI world and the studios behind some of the most
  beloved children's stories." Avoid name-dropping employers.
- **Story Conductor** — the role guiding the AI ensemble. The
  metaphor: an orchestra conductor working a symphony.
- **Story Curator / Tale Weaver / Storykeeper / Story Doula** —
  considered alternatives in chat3. Story Conductor won.

### Tagline lockup

`ROOTED IN GROWTH ✦ REVITALIZED THROUGH CREATING`

Caps + tracked, with the 4-point sparkle as the separator. Consumed
via `src/brand/primitives/TaglineRow.tsx`.

### Closing line

`with care, with patience.` — script font, sage-600, lowercase. Footer
treatment.

## Page-by-page guidance

### `/` — Canvas Studio marketing

Hero: "A storybook studio for the people you love most" /
"A storybook, grown from your family memories." Lead names the
process: pictures → one page at a time → bedtime book.

Pipeline: 5 steps as a vertical sprig. Each step is a quiet promise,
not a feature. Phase 01 is "Story drafting", not "LLM
decomposition." The AI Engineer in Residence framing belongs in the
"Honest about the magic" band, not next to the pipeline steps.

Stats band: small reassurances, not capabilities. `5 photos to teach
the art of your little one's face` / `∞ do-overs, always` /
`3 sec between quiet saves` / `1 family at a time`.

### `/storybook-series.html` — Series marketing

Hero: "Stories for the days that ask the most." Different from the
custom-book pitch: the story is *already written*; the parent brings
the heart. Three differences to call out (we wrote / you bring the
heart / ready before bedtime). The Calm Down Donuts feature shows the
shape of a single book. The persona grid (six cards) walks through
basics → look → comfort tools → world dialled down → how they
speak → favorites.

### `/app.html` — BookWizard product

Voice in the app should match the marketing pages — friendly, slow,
careful. Step labels use the same pipeline vocabulary (Story / Style
/ Character / Storyboard / Pages).

## Linting

`stripEmDashes()` and `lintVoice()` from `src/brand/voice.ts` are
imported by any code path that accepts user-supplied text into a
template. Future surfaces should add a CI step that runs
`lintVoice()` over checked-in copy and fails the PR on `—`.

## Provenance

- Anthropic design bundle "Rooted & Revitalized Design System" —
  chat3 transcripts contain the iteration history.
- `src/brand/voice.ts` — code-side enforcement.
- This document — the contract.
