import type { CSSProperties, ReactNode } from 'react';
import { palette, shadow } from '../tokens';

export interface TornPaperProps {
  bg?: string;
  children?: ReactNode;
  style?: CSSProperties;
}

/** Cream rectangle with a torn-edge clip-path and a soft paper shadow. */
export function TornPaper({
  bg = palette.cream[50],
  children,
  style,
}: TornPaperProps) {
  return (
    <div
      style={{
        background: bg,
        boxShadow: shadow.paper,
        clipPath:
          'polygon(0% 8%, 4% 2%, 12% 6%, 22% 0%, 40% 4%, 60% 0%, 80% 5%, 100% 2%, 98% 98%, 82% 94%, 65% 100%, 45% 95%, 22% 100%, 8% 95%, 2% 100%)',
        padding: '14px 24px',
        ...style,
      }}
    >
      {children}
    </div>
  );
}
