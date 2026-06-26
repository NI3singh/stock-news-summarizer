import { cn } from "@/lib/utils";
import type { MlSignalResponse } from "@/lib/types";

export function MlSignalCard({ signal }: { signal: MlSignalResponse | undefined }) {
  if (!signal?.available || !signal.prediction) return null;

  const up = signal.prediction === "UP";
  const conf = signal.confidence ?? 0;
  const pUp = signal.probability_up ?? 0;
  const pDown = signal.probability_down ?? 0;

  return (
    <div className="rounded-lg border border-qm-border bg-qm-card p-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-wider text-qm-text3">ML Signal</span>
        <span
          className={cn(
            "rounded px-2 py-0.5 text-xs font-bold",
            up ? "bg-qm-green-bg text-qm-green" : "bg-red-500/10 text-red-400",
          )}
        >
          {signal.prediction}
        </span>
      </div>

      <div className="mt-2">
        <div className="flex justify-between text-xs text-qm-text3">
          <span>Confidence</span>
          <span className="tabular-nums">{(conf * 100).toFixed(0)}%</span>
        </div>
        <div className="mt-1 h-1.5 w-full rounded-full bg-qm-border">
          <div
            className={cn("h-1.5 rounded-full", up ? "bg-qm-green" : "bg-qm-red")}
            style={{ width: `${Math.max(0, Math.min(100, conf * 100))}%` }}
          />
        </div>
      </div>

      <div className="mt-2 flex justify-between text-xs text-qm-text2">
        <span>
          P(up): <span className="text-qm-green">{(pUp * 100).toFixed(0)}%</span>
        </span>
        <span>
          P(down): <span className="text-qm-red">{(pDown * 100).toFixed(0)}%</span>
        </span>
      </div>

      {signal.signal_strength && (
        <div className="mt-1 text-[10px] text-qm-text3">Strength: {signal.signal_strength}</div>
      )}
    </div>
  );
}
