import type { ReactNode } from 'react';
import { palette } from '../tokens';

export interface SprigProps {
  color?: string;
  size?: number;
  /** Total alternating leaves on the stem. The original chose 3, 6, 9, 12, 15, 18, or 21. */
  leafCount?: number;
}

/**
 * Tall stem with alternating filled leaves. Brand mark when used at logo scale,
 * decorative dingbat at smaller sizes.
 */
export function Sprig({ color = palette.sage[600], size = 28, leafCount = 12 }: SprigProps) {
  const topPad = 18;
  const bottomPad = 12;
  const leafSpan = 14;
  const stemLen = topPad + leafCount * leafSpan + bottomPad;
  const stemTop = 2;
  const stemBot = stemTop + stemLen;
  const vbH = stemBot + 4;

  const leaves: ReactNode[] = [];
  for (let i = 0; i < leafCount; i++) {
    const cy = topPad + (i + 0.5) * leafSpan;
    const right = i % 2 === 0;
    if (right) {
      leaves.push(
        <path
          key={i}
          d={`M33,${cy + 4} C33,${cy + 4} 50,${cy} 56,${cy - 11} C58,${cy - 15} 57,${cy - 20} 54,${cy - 21} C51,${cy - 22} 46,${cy - 20} 43,${cy - 15} C39,${cy - 9} 33,${cy} 33,${cy + 4} Z`}
        />,
      );
    } else {
      leaves.push(
        <path
          key={i}
          d={`M33,${cy + 4} C33,${cy + 4} 16,${cy} 10,${cy - 11} C8,${cy - 15} 9,${cy - 20} 12,${cy - 21} C15,${cy - 22} 20,${cy - 20} 23,${cy - 15} C27,${cy - 9} 33,${cy} 33,${cy + 4} Z`}
        />,
      );
    }
  }

  const aspect = vbH / 70;
  return (
    <svg
      width={size * 0.55}
      height={size * 0.55 * aspect}
      viewBox={`0 0 70 ${vbH}`}
      fill={color}
      aria-hidden
    >
      <path
        d={`M33,${stemBot} C30,${stemBot} 28,${stemBot - 2} 28,${stemBot - 5} L28,${stemTop + 5} C28,${stemTop + 2} 30,${stemTop} 33,${stemTop} C36,${stemTop} 38,${stemTop + 2} 38,${stemTop + 5} L38,${stemBot - 5} C38,${stemBot - 2} 36,${stemBot} 33,${stemBot} Z`}
        opacity="0.75"
      />
      <path
        d="M33,18
           C33,18 27,16 25,11
           C23,6 27,1 33,2
           C39,1 43,6 41,11
           C39,16 33,18 33,18 Z"
      />
      {leaves}
    </svg>
  );
}
