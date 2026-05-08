import { palette } from '../tokens';

export interface HeartGlyphProps {
  color?: string;
  size?: number;
}

export function HeartGlyph({ color = palette.sage[600], size = 14 }: HeartGlyphProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill={color} aria-hidden>
      <path d="M10,16.5 C9.2,15.8 3,11 3,7 C3,4.8 4.8,3 7,3 C8.2,3 9.3,3.6 10,4.5 C10.7,3.6 11.8,3 13,3 C15.2,3 17,4.8 17,7 C17,11 10.8,15.8 10,16.5 Z" />
    </svg>
  );
}
