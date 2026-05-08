import type { CSSProperties, ReactNode } from 'react';
import { palette } from '../tokens';

export interface WatercolorWashProps {
  primary?: string;
  secondary?: string;
  blur?: number;
  children?: ReactNode;
  style?: CSSProperties;
}

/**
 * Soft radial-gradient backdrop in two sage tones, blurred for a watercolor feel.
 * Wrap content; the wash sits behind it.
 */
export function WatercolorWash({
  primary = palette.sage[200],
  secondary = palette.sage[300],
  blur = 4,
  children,
  style,
}: WatercolorWashProps) {
  const primaryRgba = hexToRgba(primary, 0.45);
  const secondaryRgba = hexToRgba(secondary, 0.35);
  return (
    <div style={{ position: 'relative', ...style }}>
      <div
        aria-hidden
        style={{
          position: 'absolute',
          inset: 14,
          background: `radial-gradient(ellipse at 30% 40%, ${primary} 0%, ${primaryRgba} 40%, transparent 70%), radial-gradient(ellipse at 70% 60%, ${secondary} 0%, ${secondaryRgba} 50%, transparent 75%)`,
          filter: `blur(${blur}px)`,
          borderRadius: '50%',
          pointerEvents: 'none',
        }}
      />
      <div style={{ position: 'relative' }}>{children}</div>
    </div>
  );
}

function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace('#', '');
  const bigint = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
