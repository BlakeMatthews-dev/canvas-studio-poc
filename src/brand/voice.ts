/**
 * Brand voice helpers and copy tokens.
 *
 * Voice rules:
 *   - No em dashes (—). Use commas, periods, " and ", or " then " instead.
 *   - Warm, slow, hand-made. Short sentences. Let small things matter.
 *   - Categories: Plants, DIY Projects, Handmade Pieces, Real Life.
 */

export const tagline = {
  primary: 'Rooted in Growth',
  secondary: 'Revitalized through Creating',
} as const;

export const categories = ['Plants', 'DIY Projects', 'Handmade Pieces', 'Real Life'] as const;

export type Category = (typeof categories)[number];

/**
 * Replace any em dashes in a string with the brand-friendly substitutes.
 * Default: replace " — " with ", " and bare em dashes with commas.
 */
export function stripEmDashes(input: string, replacement = ', '): string {
  return input
    .replace(/\s+—\s+/g, replacement)
    .replace(/—/g, replacement.trim());
}

/**
 * Lint a string for brand voice violations. Returns issue messages.
 * Empty array means clean.
 */
export function lintVoice(input: string): string[] {
  const issues: string[] = [];
  if (input.includes('—')) issues.push('Contains em dash; use a comma or period.');
  return issues;
}
