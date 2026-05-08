import { Fragment } from 'react';
import { palette } from '../tokens';
import { Sparkle } from './Sparkle';

export interface TaglineRowProps {
  color?: string;
  scale?: number;
  left?: string;
  right?: string;
}

/** Underlined tagline split by a centered sparkle. */
export function TaglineRow({
  color = palette.sage[600],
  scale = 1,
  left = 'Rooted in Growth',
  right = 'Revitalized through Creating',
}: TaglineRowProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14 * scale,
        color,
        fontFamily: "'Nunito Sans', sans-serif",
        fontSize: 10.5 * scale,
        letterSpacing: '.28em',
        textTransform: 'uppercase',
        fontWeight: 500,
      }}
    >
      <Fragment>
        <span style={{ borderBottom: `1px solid ${color}`, padding: '0 4px 2px' }}>{left}</span>
        <Sparkle color={color} size={12 * scale} />
        <span style={{ borderBottom: `1px solid ${color}`, padding: '0 4px 2px' }}>{right}</span>
      </Fragment>
    </div>
  );
}
