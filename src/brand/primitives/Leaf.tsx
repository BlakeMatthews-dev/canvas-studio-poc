import { palette } from '../tokens';

export interface LeafProps {
  color?: string;
  size?: number;
  rotate?: number;
}

/** Single filled leaf, closed bezier path with a stroked midrib. */
export function Leaf({ color = palette.sage[600], size = 28, rotate = 0 }: LeafProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill={color}
      style={{ transform: `rotate(${rotate}deg)` }}
      aria-hidden
    >
      <path
        d="M50,5
           C70,5 92,20 92,50
           C92,78 72,94 50,95
           C50,95 50,65 36,52
           C22,39 8,35 8,50
           C8,22 30,5 50,5 Z"
      />
      <path
        d="M50,95 C50,95 48,60 50,5"
        stroke={color}
        strokeWidth="2.5"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  );
}
