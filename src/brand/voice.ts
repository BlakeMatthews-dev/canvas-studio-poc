/**
 * Brand voice helpers and copy tokens.
 *
 * Voice rules:
 *   - No em dashes (—). Use commas, periods, " and ", or " then " instead.
 *   - Warm, slow, hand-made. Short sentences. Let small things matter.
 *   - Categories: Plants, DIY Projects, Handmade Pieces, Real Life.
 */

/**
 * Parent brand: Rooted & Revitalized. The umbrella creator brand.
 */
export const parentBrand = {
  name: 'Rooted & Revitalized',
  tagline: {
    primary: 'Rooted in Growth',
    secondary: 'Revitalized through Creating',
  },
  categories: ['Plants', 'DIY Projects', 'Handmade Pieces', 'Real Life'],
} as const;

/**
 * Product brand: Main Character Crew.
 *
 * Customer-facing line for the personalised illustrated children's
 * books product (the BookWizard at /app.html). Sub-brand of the
 * Rooted & Revitalized parent.
 */
export const productBrand = {
  name: 'Main Character Crew',
  tagline: 'Stories Made the Way You’re Made.',
  /** Optional umbrella publisher imprint. TBD; Stim & Story Press is a candidate. */
  publisher: null as string | null,
  // The four signal words layered into the tagline:
  //   - "Stories"     — what we make
  //   - "the Way"     — process / care
  //   - "You're Made" — the child's character + sensory profile
  // Keep these in mind when extending copy.
} as const;

/**
 * Backwards-compatible re-exports. Existing imports of `tagline` and
 * `categories` see the parent-brand values.
 */
export const tagline = parentBrand.tagline;
export const categories = parentBrand.categories;

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
