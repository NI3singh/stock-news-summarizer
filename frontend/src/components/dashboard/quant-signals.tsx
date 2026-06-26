import { cn } from "@/lib/utils";
import type { TechnicalSignals } from "@/lib/types";

export function QuantSignals({ signals }: { signals: TechnicalSignals | null }) {
  if (!signals) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-[88px] animate-pulse rounded-lg border border-qm-border bg-qm-card"
          />
        ))}
      </div>
    );
  }

  const { rsi, macd, volume_ratio: vol, price_change_pct: chg } = signals;

  const rsiSub = rsi == null ? "—" : rsi > 70 ? "Overbought" : rsi < 30 ? "Oversold" : "Neutral";
  const rsiBar = rsi == null ? "bg-qm-text3" : rsi > 70 || rsi < 30 ? "bg-qm-red" : "bg-qm-green";
  const rsiPct = rsi == null ? 0 : Math.max(0, Math.min(100, rsi));

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {/* RSI */}
      <div className="rounded-lg border border-qm-border bg-qm-card p-3">
        <div className="text-[10px] uppercase tracking-wider text-qm-text3">RSI</div>
        <div className="mt-1 text-xl font-bold tabular-nums text-qm-text">
          {rsi == null ? "N/A" : rsi.toFixed(1)}
        </div>
        <div className="text-xs text-qm-text2">{rsiSub}</div>
        <div className="mt-2 h-1 w-full rounded-full bg-qm-border">
          <div className={cn("h-1 rounded-full", rsiBar)} style={{ width: `${rsiPct}%` }} />
        </div>
      </div>

      {/* MACD */}
      <div className="rounded-lg border border-qm-border bg-qm-card p-3">
        <div className="text-[10px] uppercase tracking-wider text-qm-text3">MACD</div>
        <div
          className={cn(
            "mt-1 text-xl font-bold tabular-nums",
            macd == null ? "text-qm-text" : macd >= 0 ? "text-qm-green" : "text-qm-red",
          )}
        >
          {macd == null ? "N/A" : `${macd >= 0 ? "+" : ""}${macd.toFixed(2)}`}
        </div>
        <div className="text-xs text-qm-text2">
          {macd == null ? "—" : macd >= 0 ? "Bullish" : "Bearish"}
        </div>
      </div>

      {/* Volume */}
      <div className="rounded-lg border border-qm-border bg-qm-card p-3">
        <div className="text-[10px] uppercase tracking-wider text-qm-text3">Volume</div>
        <div className="mt-1 text-xl font-bold tabular-nums text-qm-text">
          {vol == null ? "N/A" : `${vol.toFixed(1)}x`}
        </div>
        <div className="text-xs text-qm-text2">
          {vol == null ? "—" : vol > 1 ? "Above avg" : "Below avg"}
        </div>
      </div>

      {/* Price change */}
      <div className="rounded-lg border border-qm-border bg-qm-card p-3">
        <div className="text-[10px] uppercase tracking-wider text-qm-text3">Price Change</div>
        <div
          className={cn(
            "mt-1 text-xl font-bold tabular-nums",
            chg == null ? "text-qm-text" : chg >= 0 ? "text-qm-green" : "text-qm-red",
          )}
        >
          {chg == null ? "N/A" : `${chg >= 0 ? "+" : ""}${chg.toFixed(1)}%`}
        </div>
        <div className="text-xs text-qm-text2">vs yesterday</div>
      </div>
    </div>
  );
}
