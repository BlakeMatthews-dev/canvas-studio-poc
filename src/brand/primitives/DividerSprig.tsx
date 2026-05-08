import type { ReactNode } from 'react';
import { palette } from '../tokens';
import { HeartGlyph } from './HeartGlyph';

export interface DividerSprigProps {
  color?: string;
  width?: number | string;
  /** Glyph element rendered between the hairlines. Defaults to a heart. */
  glyph?: ReactNode;
}

/** Hairline divider with a small centered glyph — a brand motif. */
export function DividerSprig({
  color = palette.sage[400],
  width = '100%',
  glyph,
}: DividerSprigProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        color,
        width,
      }}
    >
      <div style={{ flex: 1, height: 1, background: color }} />
      {glyph ?? <HeartGlyph color={color} size={14} />}
      <div style={{ flex: 1, height: 1, background: color }} />
    </div>
  );
}
