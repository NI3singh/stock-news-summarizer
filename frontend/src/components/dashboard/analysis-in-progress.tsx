"use client";
import { useEffect, useState } from "react";
import { Brain, Check, LineChart, Loader2, Newspaper, Radar, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

// The real multi-agent pipeline stages, in order. The backend job is opaque
// (pending/running/done), so we pace through these on a timer to keep the screen
// alive — it's an honest preview of what's running, not a live percentage.
const STAGES = [
  { icon: Radar, label: "Gathering news", detail: "Polygon · Yahoo · Finviz · Google" },
  { icon: Brain, label: "Recalling memory", detail: "past analyses & sentiment trend" },
  { icon: Newspaper, label: "Analyzing news", detail: "sentiment, themes & credibility" },
  { icon: LineChart, label: "Crunching signals", detail: "RSI · MACD · trend · volume" },
  { icon: Sparkles, label: "Synthesizing report", detail: "the multi-agent verdict" },
];

export function AnalysisInProgress({ ticker }: { ticker: string }) {
  const [active, setActive] = useState(0);

  // Pace through stages on a timer. The caller mounts this with key={ticker}, so a
  // new ticker remounts the component and naturally resets to the first stage.
  useEffect(() => {
    const id = setInterval(
      () => setActive((s) => Math.min(s + 1, STAGES.length - 1)),
      2600,
    );
    return () => clearInterval(id);
  }, []);

  // Determinate-ish bar, capped below 100% so it never reads "done" while waiting.
  const pct = Math.min(((active + 1) / STAGES.length) * 100, 92);

  return (
    <div className="animate-fade-in mx-auto flex w-full max-w-md flex-col items-center px-6 py-12 text-center">
      {/* Pulsing brand mark */}
      <div className="pulse-ring mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-qm-green-bg text-qm-green">
        <Loader2 className="h-7 w-7 animate-spin" />
      </div>

      <h2 className="text-xl font-bold text-qm-text">
        Analyzing <span className="gradient-text">{ticker}</span>
      </h2>
      <p className="mt-1.5 text-sm leading-relaxed text-qm-text2">
        Our agents are working through the data. This usually takes 15–30s — the
        full report will appear here automatically.
      </p>

      {/* Live stage checklist */}
      <div className="mt-7 w-full space-y-1.5 text-left">
        {STAGES.map((stage, i) => {
          const Icon = stage.icon;
          const done = i < active;
          const current = i === active;
          return (
            <div
              key={stage.label}
              className={cn(
                "flex items-center gap-3 rounded-lg border px-3 py-2 transition-all duration-300",
                current
                  ? "border-qm-green/40 bg-qm-green-bg"
                  : "border-transparent " + (done ? "opacity-70" : "opacity-35"),
              )}
            >
              <span
                className={cn(
                  "flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full",
                  done
                    ? "bg-qm-green text-qm-bg"
                    : current
                      ? "text-qm-green"
                      : "text-qm-text3",
                )}
              >
                {done ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <Icon className={cn("h-4 w-4", current && "animate-pulse")} />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <div
                  className={cn(
                    "text-sm font-medium",
                    current ? "text-qm-text" : "text-qm-text2",
                  )}
                >
                  {stage.label}
                </div>
                <div className="truncate text-xs text-qm-text3">{stage.detail}</div>
              </div>
              {current && <Loader2 className="h-3.5 w-3.5 animate-spin text-qm-green" />}
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="mt-6 h-1.5 w-full overflow-hidden rounded-full bg-qm-card">
        <div
          className="h-full rounded-full bg-gradient-to-r from-qm-green-dim to-qm-green transition-all duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
