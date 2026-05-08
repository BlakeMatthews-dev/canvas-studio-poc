import { Fragment } from 'react';
import { palette } from '../tokens';

export interface CategoryPillProps {
  items?: string[];
  scale?: number;
  bg?: string;
  fg?: string;
}

/** The brand's signature dotted-pill: dark sage filled with cream caps. */
export function CategoryPill({
  items = ['Plants', 'DIY Projects', 'Handmade Pieces', 'Real Life'],
  scale = 1,
  bg = palette.sage[300],
  fg = palette.cream[50],
}: CategoryPillProps) {
  return (
    <div
      style={{
        background: bg,
        color: fg,
        padding: `${8 * scale}px ${22 * scale}px`,
        borderRadius: 999,
        fontFamily: "'Nunito Sans', sans-serif",
        fontSize: 10.5 * scale,
        letterSpacing: '.22em',
        textTransform: 'uppercase',
        fontWeight: 600,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 10 * scale,
      }}
    >
      {items.map((item, i) => (
        <Fragment key={item}>
          {i > 0 && <span style={{ opacity: 0.6 }}>·</span>}
          <span>{item}</span>
        </Fragment>
      ))}
    </div>
  );
}
