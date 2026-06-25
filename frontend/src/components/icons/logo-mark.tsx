interface LogoMarkProps {
  className?: string;
}

/**
 * StockStalker AI mark — a rising stock chart line locked onto a tactical
 * targeting reticle at its peak. Transparent background; brand-green baked in.
 */
export default function LogoMark({ className }: LogoMarkProps) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="cL" x1="4" y1="52" x2="44" y2="16" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#16a34a" />
          <stop offset="0.65" stopColor="#22c55e" />
          <stop offset="1" stopColor="#4ade80" />
        </linearGradient>
        <linearGradient id="cA" x1="0" y1="12" x2="0" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#22c55e" stopOpacity="0.26" />
          <stop offset="1" stopColor="#22c55e" stopOpacity="0" />
        </linearGradient>
        <radialGradient id="cG" cx="44" cy="16" r="5" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#4ade80" stopOpacity="0.5" />
          <stop offset="1" stopColor="#4ade80" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* chart */}
      <path d="M4 52 L10 47 L18 49 L26 39 L34 42 L44 16 L44 58 L4 58Z" fill="url(#cA)" />
      <path d="M4 52 L10 47 L18 49 L26 39 L34 42 L44 16" stroke="url(#cL)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="10" cy="47" r="1.2" fill="#22c55e" opacity="0.5" />
      <circle cx="18" cy="49" r="1.2" fill="#22c55e" opacity="0.5" />
      <circle cx="26" cy="39" r="1.2" fill="#22c55e" opacity="0.5" />
      <circle cx="34" cy="42" r="1.2" fill="#22c55e" opacity="0.5" />

      {/* targeting reticle at the peak */}
      <circle cx="44" cy="16" r="15" stroke="#22c55e" strokeWidth="0.5" opacity="0.1" />
      <path d="M54.83 17.91 A11 11 0 0 1 45.91 26.83" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M42.09 26.83 A11 11 0 0 1 33.17 17.91" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M33.17 14.09 A11 11 0 0 1 42.09 5.17" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M45.91 5.17 A11 11 0 0 1 54.83 14.09" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="44" cy="16" r="8" stroke="#22c55e" strokeWidth="0.75" opacity="0.38" />
      <line x1="44" y1="2" x2="44" y2="12" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="44" y1="20" x2="44" y2="30" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="30" y1="16" x2="40" y2="16" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="48" y1="16" x2="58" y2="16" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="42" y1="2" x2="46" y2="2" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" opacity="0.65" />
      <line x1="42" y1="30" x2="46" y2="30" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" opacity="0.65" />
      <line x1="30" y1="14" x2="30" y2="18" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" opacity="0.65" />
      <line x1="58" y1="14" x2="58" y2="18" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" opacity="0.65" />
      <circle cx="44" cy="16" r="5" stroke="#22c55e" strokeWidth="1" opacity="0.65" />
      <circle cx="44" cy="16" r="4" fill="url(#cG)" />
      <circle cx="44" cy="16" r="1.8" fill="#4ade80" />
    </svg>
  );
}
