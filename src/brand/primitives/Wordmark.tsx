import { palette } from '../tokens';

export interface WordmarkProps {
  color?: string;
  /** 1 ≈ 56px caps + 82px script. The original primitive uses 3 for the full logo lockup. */
  scale?: number;
  align?: 'flex-start' | 'center';
}

/**
 * "ROOTED & Revitalized" lockup.
 * Display caps + flowing script, with the script slightly offset so its
 * R ascender and d descender wrap around "Rooted &" above.
 */
export function Wordmark({
  color = palette.sage[600],
  scale = 3,
  align = 'center',
}: WordmarkProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: align === 'center' ? 'center' : 'flex-start',
        lineHeight: 1,
        color,
        position: 'relative',
      }}
    >
      <div
        style={{
          fontFamily: "'Cormorant Garamond', 'Playfair Display', Georgia, serif",
          fontWeight: 600,
          fontSize: 56 * scale,
          letterSpacing: '.01em',
          textTransform: 'uppercase',
          lineHeight: 0.95,
          transform: `translateX(${12 * scale}px)`,
        }}
      >
        <span style={{ letterSpacing: '-.05em' }}>Rooted</span>
        <span style={{ marginLeft: `${10 * scale}px` }}>&amp;</span>
      </div>
      <div
        style={{
          fontFamily: "'Dancing Script', 'Pinyon Script', cursive",
          fontSize: 82 * scale,
          lineHeight: 0.85,
          fontWeight: 400,
          marginTop: -12 * scale,
          transform: `translateX(${-10 * scale}px)`,
        }}
      >
        Revitalized
      </div>
    </div>
  );
}
