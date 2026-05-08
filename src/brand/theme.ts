import { createTheme, type MantineThemeOverride } from '@mantine/core';
import { palette, fonts, radius, shadow, tracking } from './tokens';

/**
 * Mantine theme override mapping Rooted & Revitalized tokens onto Mantine's
 * primitives. Apply via <MantineProvider theme={brandTheme}> at the surface
 * you want to brand. Do NOT apply globally without expecting layout shifts —
 * Mantine adds resets and component styles.
 */
export const brandTheme: MantineThemeOverride = createTheme({
  primaryColor: 'sage',
  primaryShade: { light: 6, dark: 4 },
  colors: {
    sage: [
      palette.sage[50],
      palette.sage[100],
      palette.sage[200],
      palette.sage[300],
      palette.sage[400],
      palette.sage[500],
      palette.sage[600],
      palette.sage[700],
      palette.sage[700],
      palette.sage[700],
    ],
    cream: [
      palette.cream[50],
      palette.cream[50],
      palette.cream[100],
      palette.cream[100],
      palette.cream[200],
      palette.cream[200],
      palette.cream[300],
      palette.cream[300],
      palette.cream[300],
      palette.cream[300],
    ],
    clay: [
      palette.clay[100],
      palette.clay[100],
      palette.clay[100],
      palette.clay[300],
      palette.clay[300],
      palette.clay[500],
      palette.clay[500],
      palette.clay[500],
      palette.clay[500],
      palette.clay[500],
    ],
  },
  white: palette.cream[50],
  black: palette.ink[900],
  fontFamily: fonts.body,
  fontFamilyMonospace: 'ui-monospace, SF Mono, monospace',
  headings: {
    fontFamily: fonts.display,
    fontWeight: '600',
    sizes: {
      h1: { fontSize: 'clamp(32px, 3.6vw, 48px)', lineHeight: '1.05', fontWeight: '600' },
      h2: { fontSize: '28px', lineHeight: '1.25', fontWeight: '500' },
      h3: { fontSize: '22px', lineHeight: '1.25', fontWeight: '500' },
    },
  },
  defaultRadius: 'md',
  radius: {
    xs: `${radius.sm}px`,
    sm: `${radius.sm}px`,
    md: `${radius.md}px`,
    lg: `${radius.lg}px`,
    xl: `${radius.pill}px`,
  },
  shadows: {
    xs: shadow.sm,
    sm: shadow.sm,
    md: shadow.md,
    lg: shadow.lg,
    xl: shadow.paper,
  },
  components: {
    Button: {
      defaultProps: {
        radius: 'xl',
      },
      styles: {
        root: {
          textTransform: 'uppercase' as const,
          letterSpacing: tracking.wider,
          fontWeight: 600,
          fontSize: 11,
        },
      },
    },
    TextInput: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        label: {
          textTransform: 'uppercase' as const,
          letterSpacing: tracking.wider,
          fontSize: 11,
          fontWeight: 600,
          color: palette.sage[500],
        },
      },
    },
    Card: {
      defaultProps: {
        radius: 'lg',
        shadow: 'xl',
        padding: 'lg',
      },
    },
    Badge: {
      defaultProps: {
        radius: 'xl',
      },
      styles: {
        root: {
          textTransform: 'uppercase' as const,
          letterSpacing: tracking.wider,
          fontWeight: 600,
        },
      },
    },
  },
});
