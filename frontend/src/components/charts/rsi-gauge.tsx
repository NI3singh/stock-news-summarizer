"use client";

const R = 90;
const CX = 100;
const CY = 100;

function pt(v: number): [number, number] {
  const clamped = Math.max(0, Math.min(100, v));
  const a = ((180 - 1.8 * clamped) * Math.PI) / 180;
  return [CX + R * Math.cos(a), CY - R * Math.sin(a)];
}

function arc(v1: number, v2: number): string {
  const [sx, sy] = pt(v1);
  const [ex, ey] = pt(v2);
  return `M ${sx.toFixed(2)},${sy.toFixed(2)} A ${R},${R} 0 0 1 ${ex.toFixed(2)},${ey.toFixed(2)}`;
}

function rsiLabel(v: number): string {
  return v > 70 ? "Overbought" : v < 30 ? "Oversold" : "Neutral";
}

export function RsiGauge({ value }: { value: number | null }) {
  const has = value != null && !Number.isNaN(value);
  const v = has ? Math.max(0, Math.min(100, value!)) : 0;
  const [nx, ny] = pt(v);

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 120" className="w-48">
        {/* zones: 0-30 oversold (red), 30-70 neutral (gray), 70-100 overbought (red) */}
        <path d={arc(0, 30)} fill="none" stroke="#ef4444" strokeWidth="12" strokeLinecap="round" />
        <path d={arc(30, 70)} fill="none" stroke="#475569" strokeWidth="12" />
        <path d={arc(70, 100)} fill="none" stroke="#ef4444" strokeWidth="12" strokeLinecap="round" />
        {has && (
          <circle cx={nx} cy={ny} r="7" fill="#fff" stroke="#22c55e" strokeWidth="3" />
        )}
      </svg>
      <div className="text-2xl font-bold tabular-nums text-qm-text">{has ? v.toFixed(0) : "N/A"}</div>
      <div className="text-xs text-qm-text2">RSI · {has ? rsiLabel(v) : "not stored yet"}</div>
    </div>
  );
}
