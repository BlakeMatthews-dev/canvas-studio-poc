import type { CSSProperties, ReactNode } from 'react';
import { palette, radius, shadow } from '../tokens';

export interface PaperCardProps {
  children?: ReactNode;
  bg?: string;
  border?: string;
  style?: CSSProperties;
  /** Inner padding override; default 24. */
  padding?: number | string;
}

/** Cream card with the brand's soft paper shadow and rounded-lg corners. */
export function PaperCard({
  children,
  bg = palette.cream[100],
  border = palette.cream[300],
  padding = 24,
  style,
}: PaperCardProps) {
  return (
    <div
      style={{
        background: bg,
        borderRadius: radius.lg,
        padding,
        boxShadow: shadow.paper,
        border: `1px solid ${border}`,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
