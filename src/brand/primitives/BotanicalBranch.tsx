import { palette } from '../tokens';

export interface BotanicalBranchProps {
  color?: string;
  width?: number;
  height?: number;
}

/** Horizontal branch with filled leaves, end berries, and a center sparkle flower. */
export function BotanicalBranch({
  color = palette.sage[600],
  width = 400,
  height = 120,
}: BotanicalBranchProps) {
  return (
    <svg width={width} height={height} viewBox="0 0 400 120" fill={color} aria-hidden>
      {/* Main branch */}
      <path d="M10,62 C80,58 160,56 200,58 C240,60 320,62 390,60 L390,65 C320,67 240,65 200,63 C160,61 80,63 10,67 Z" />

      {/* Upward leaves */}
      <path d="M55,60 C55,60 42,44 38,28 C36,18 40,10 46,10 C52,10 57,18 58,30 C59,42 57,55 55,60 Z" />
      <path d="M120,58 C120,58 110,40 112,22 C113,12 119,6 126,8 C133,10 135,18 132,30 C129,42 122,54 120,58 Z" />
      <path d="M200,57 C200,57 192,34 196,14 C198,4 205,0 212,3 C219,6 220,16 216,28 C212,40 202,53 200,57 Z" />
      <path d="M280,58 C280,58 272,40 276,22 C278,12 284,6 291,8 C298,10 299,18 296,30 C293,42 282,54 280,58 Z" />
      <path d="M350,60 C350,60 340,44 342,28 C343,18 349,10 355,12 C361,14 362,22 359,34 C356,46 352,56 350,60 Z" />

      {/* Downward leaves */}
      <path d="M85,64 C85,64 80,82 84,98 C86,108 92,114 98,112 C104,110 104,102 101,90 C98,78 87,66 85,64 Z" />
      <path d="M160,62 C160,62 158,80 164,96 C167,106 174,110 180,107 C186,104 185,96 181,84 C177,72 162,64 160,62 Z" />
      <path d="M240,62 C240,62 240,80 248,96 C252,106 260,108 265,104 C270,100 268,92 263,80 C258,68 242,64 240,62 Z" />
      <path d="M320,62 C320,62 316,80 320,96 C322,106 328,112 334,110 C340,108 340,100 337,88 C334,76 322,64 320,62 Z" />

      {/* End berries — left */}
      <circle cx="10" cy="63" r="5.5" />
      <circle cx="18" cy="56" r="4" />
      <circle cx="18" cy="70" r="4" />

      {/* End berries — right */}
      <circle cx="390" cy="62" r="5.5" />
      <circle cx="382" cy="55" r="4" />
      <circle cx="382" cy="69" r="4" />

      {/* Center sparkle flower */}
      <path
        d="M200,10 C199,4 196,1 193,3 C190,5 191,9 194,12 C191,10 187,10 187,13 C187,16 191,17 194,15 C191,18 190,22 193,23 C196,24 199,21 200,15 C201,21 204,24 207,23 C210,22 209,18 206,15 C209,17 213,16 213,13 C213,10 209,10 206,12 C209,9 210,5 207,3 C204,1 201,4 200,10 Z"
        transform="translate(0, -2)"
      />
    </svg>
  );
}
