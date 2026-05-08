/**
 * Rooted & Revitalized — Brand Tokens (TS)
 *
 * Mirrors tokens.css for JS consumers (Mantine theme, inline styles,
 * SVG primitives that need raw color values). When changing a value,
 * change it here AND in tokens.css.
 */

export const palette = {
  sage: {
    50: '#f3f1e7',
    100: '#e6e5d2',
    200: '#c9ccb0',
    300: '#a7aa89',
    400: '#818664',
    500: '#5c6148',
    600: '#434731',
    700: '#32361f',
  },
  cream: {
    50: '#fbf8ef',
    100: '#f6f1e1',
    200: '#ede6d0',
    300: '#dcd3b8',
  },
  clay: {
    100: '#e8d5c4',
    300: '#c4a48a',
    500: '#8f6d54',
  },
  ink: {
    900: '#2d2a20',
    700: '#4a4638',
    500: '#6e6a5a',
    300: '#a29c89',
    100: '#cfc9b4',
  },
  signal: {
    bloom: '#b07a8a',
    leaf:  '#6b8a52',
    honey: '#c89a4a',
    rust:  '#a35a3f',
  },
} as const;

export const semantic = {
  bg:          palette.cream[100],
  bgElevated:  palette.cream[50],
  bgMuted:     palette.cream[200],
  bgBand:      palette.sage[500],
  bgWash:      palette.sage[200],
  fg:          palette.sage[600],
  fgBody:      palette.ink[700],
  fgMuted:     palette.ink[500],
  fgSubtle:    palette.ink[300],
  fgOnDark:    palette.cream[50],
  border:      palette.ink[100],
  borderStrong: palette.sage[300],
  divider:     palette.sage[400],
  accent:      palette.sage[600],
  accentSoft:  palette.sage[200],
  accentWarm:  palette.clay[500],
} as const;

export const fonts = {
  display: "'Cormorant Garamond', 'Playfair Display', Georgia, serif",
  script:  "'Dancing Script', 'Pinyon Script', 'Allura', 'Brush Script MT', cursive",
  label:   "'Cormorant Garamond', Georgia, serif",
  body:    "'Nunito Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
} as const;

export const tracking = {
  tight:   '-0.01em',
  normal:  '0',
  wide:    '0.08em',
  wider:   '0.18em',
  widest:  '0.28em',
} as const;

export const radius = {
  sm:   4,
  md:  10,
  lg:  18,
  pill: 999,
} as const;

export const space = {
  1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48, 8: 64, 9: 96,
} as const;

export const shadow = {
  sm:    '0 1px 2px rgba(67, 71, 49, 0.06)',
  md:    '0 4px 14px rgba(67, 71, 49, 0.09), 0 1px 2px rgba(67, 71, 49, 0.05)',
  lg:    '0 18px 40px rgba(67, 71, 49, 0.12), 0 2px 6px rgba(67, 71, 49, 0.06)',
  paper: '0 1px 0 rgba(255,255,255,.5) inset, 0 8px 24px rgba(50, 54, 31, 0.08)',
} as const;

export const motion = {
  easeOut:   'cubic-bezier(.2,.7,.2,1)',
  easeInOut: 'cubic-bezier(.55,.08,.25,1)',
  fast:      160,
  med:       260,
  slow:      520,
} as const;

export const tokens = {
  palette, semantic, fonts, tracking, radius, space, shadow, motion,
} as const;

export type Tokens = typeof tokens;
