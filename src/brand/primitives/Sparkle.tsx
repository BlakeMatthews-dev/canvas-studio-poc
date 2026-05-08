import { palette } from '../tokens';

export interface SparkleProps {
  color?: string;
  size?: number;
}

/** 4-point star, filled closed path. The brand's punctuation glyph. */
export function Sparkle({ color = palette.sage[600], size = 20 }: SparkleProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 300 300" fill={color} aria-hidden>
      <path d="M150,10 C148,80 220,148 290,150 C220,152 148,220 150,290 C152,220 80,152 10,150 C80,148 152,80 150,10 Z" />
    </svg>
  );
}
