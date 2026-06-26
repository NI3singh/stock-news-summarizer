"use client";

const sparklinePoints = [
  { x: 0, y: 55 }, { x: 1, y: 52 }, { x: 2, y: 58 }, { x: 3, y: 54 },
  { x: 4, y: 60 }, { x: 5, y: 56 }, { x: 6, y: 53 }, { x: 7, y: 50 },
  { x: 8, y: 47 }, { x: 9, y: 45 }, { x: 10, y: 43 }, { x: 11, y: 45 },
  { x: 12, y: 42 }, { x: 13, y: 41 }, { x: 14, y: 43 },
];

function buildSparklinePath(points: { x: number; y: number }[], w: number, h: number): string {
  const minY = Math.min(...points.map(p => p.y));
  const maxY = Math.max(...points.map(p => p.y));
  const maxX = points.length - 1;
  return points
    .map((p, i) => {
      const cx = (p.x / maxX) * w;
      const cy = h - ((p.y - minY) / (maxY - minY)) * h;
      return `${i === 0 ? "M" : "L"}${cx.toFixed(1)},${cy.toFixed(1)}`;
    })
    .join(" ");
}

export function MarketPreviewCard() {
  const path = buildSparklinePath(sparklinePoints, 480, 70);
  const times = ["9:30", "11:00", "12:30", "2:00", "4:00"];

  return (
    <div className="rounded-xl border border-qm-border bg-qm-card/80 backdrop-blur p-4 w-full">
      {/* Ticker header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-qm-text">AAPL</span>
            <span className="text-xs px-1.5 py-0.5 rounded bg-qm-green/20 text-qm-green font-medium">
              +2.34%
            </span>
          </div>
          <div className="text-xs text-qm-text3 mt-0.5">Apple Inc.</div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-qm-green animate-pulse" />
            <span className="text-xs text-qm-text3">LIVE</span>
          </div>
          <div className="font-bold text-qm-text text-lg mt-0.5">$178.72</div>
          <div className="text-xs text-qm-green">+$4.08</div>
        </div>
      </div>

      {/* Sparkline chart */}
      <div className="relative h-[72px] w-full">
        <svg viewBox="0 0 480 72" className="w-full h-full" preserveAspectRatio="none">
          {/* Fill gradient under line */}
          <defs>
            <linearGradient id="greenFade" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0.02" />
            </linearGradient>
          </defs>
          <path
            d={`${path} L480,72 L0,72 Z`}
            fill="url(#greenFade)"
          />
          <path
            d={path}
            fill="none"
            stroke="#22c55e"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {/* Time labels */}
      <div className="flex justify-between mt-1">
        {times.map(t => (
          <span key={t} className="text-[10px] text-qm-text3">{t}</span>
        ))}
      </div>
    </div>
  );
}
