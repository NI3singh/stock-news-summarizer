"use client";
import { useEffect, useState } from "react";
import { Brain, Loader2 } from "lucide-react";
import { SignalsTabs } from "@/components/signals/signals-tabs";
import { cn } from "@/lib/utils";
import { useTickers } from "@/hooks/use-tickers";
import { useMlCorrelation, useMlStatus, useTrainModel } from "@/hooks/use-ml";
import { useDashboardStore } from "@/stores/dashboard-store";
import { Button } from "@/components/ui/button";
import { CorrelationChart } from "@/components/charts/correlation-chart";
import type { SignalBucket } from "@/lib/types";

const RANGES = [7, 14, 30];

function StatCard({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-xl border border-qm-border bg-qm-card p-4">
      <div className="text-[10px] uppercase tracking-wider text-qm-text3">{label}</div>
      <div className={cn("mt-1 text-lg font-bold text-qm-text", valueClass)}>{value}</div>
    </div>
  );
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return iso.replace("T", " ").slice(0, 16);
}

function accColor(a: number | null): string {
  if (a == null) return "text-qm-text3";
  if (a > 0.6) return "text-qm-green";
  if (a >= 0.5) return "text-qm-amber";
  return "text-qm-red";
}

const ACC_GRID = "grid grid-cols-[1.3fr_0.8fr_0.8fr_0.8fr] gap-2";

function AccuracyRow({ label, b }: { label: string; b: SignalBucket }) {
  return (
    <div className={cn(ACC_GRID, "px-4 py-2.5 text-sm")}>
      <span className="text-qm-text2">{label}</span>
      <span className="tabular-nums text-qm-text2">{b.occurrences}</span>
      <span className="tabular-nums text-qm-text2">{b.correct}</span>
      <span className={cn("tabular-nums font-medium", accColor(b.accuracy))}>
        {b.accuracy == null ? "—" : `${(b.accuracy * 100).toFixed(0)}%`}
      </span>
    </div>
  );
}

export default function SignalsPage() {
  const { data: tickers } = useTickers();
  const { data: mlStatus } = useMlStatus();
  const addNotification = useDashboardStore((s) => s.addNotification);
  const train = useTrainModel();
  const [ticker, setTicker] = useState("");
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (!ticker && tickers && tickers.length) setTicker(tickers[0]);
  }, [ticker, tickers]);

  const { data: corr, isLoading: corrLoading } = useMlCorrelation(ticker || null, days);
  const model = mlStatus?.models.find((m) => m.ticker === ticker);

  const handleTrain = async () => {
    if (!ticker) return;
    const res = await train.mutateAsync(ticker);
    addNotification(res.message ?? res.detail ?? "Training started", "info");
  };

  const corrText =
    corr?.correlation != null
      ? `${corr.correlation >= 0 ? "+" : ""}${corr.correlation.toFixed(2)}`
      : "—";

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-qm-green" />
          <h1 className="text-2xl font-bold text-qm-text">ML Signals</h1>
        </div>
        <SignalsTabs />
      </div>

      {/* Section 1 — model status */}
      <div className="mb-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatCard
          label="Model Status"
          value={model?.trained ? "✓ Trained" : "Not trained yet"}
          valueClass={model?.trained ? "text-qm-green" : "text-qm-text3"}
        />
        <StatCard label="Trained At" value={fmtDate(model?.trained_at ?? null)} />
        <StatCard
          label="CV Accuracy"
          value={model?.cv_accuracy != null ? `${(model.cv_accuracy * 100).toFixed(1)}%` : "—"}
        />
      </div>
      <div className="mb-6">
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={handleTrain} loading={train.isPending} disabled={!ticker}>
            Train / Retrain Model{ticker ? ` (${ticker})` : ""}
          </Button>
          {model && !model.trained && (
            <span className="text-xs text-qm-text3">
              {model.analyses_count} analyses available
              {model.analyses_count < 10 ? " — need ~10 to train" : ""}
            </span>
          )}
        </div>
        {train.isSuccess && (
          <p className="mt-2 text-xs text-qm-text3">
            Training in background… check back in ~30 seconds (status auto-refreshes).
          </p>
        )}
      </div>

      {/* Section 2 — ticker selector + date range */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          className="rounded-lg border border-qm-border bg-qm-card px-3 py-1.5 text-sm text-qm-text2 focus:border-qm-green focus:outline-none"
        >
          {(tickers ?? []).map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <div className="flex gap-1">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setDays(r)}
              className={cn(
                "rounded px-2.5 py-1 text-xs",
                days === r ? "bg-qm-green-bg text-qm-green" : "text-qm-text3 hover:text-qm-text2",
              )}
            >
              {r}d
            </button>
          ))}
        </div>
      </div>
      {corr && corr.sample_count < 7 && (
        <div className="mb-4 rounded-lg border border-qm-amber/30 bg-qm-amber-bg p-3 text-xs text-qm-text2">
          Need at least 7 days of analyses for a meaningful correlation (have {corr.sample_count}).
        </div>
      )}

      {/* Section 3 — correlation coefficient */}
      <div className="mb-6 rounded-xl border border-qm-border bg-qm-card p-5 text-center">
        <div className="text-[10px] uppercase tracking-wider text-qm-text3">
          Correlation (sentiment → next-day return)
        </div>
        <div className="mt-1 text-4xl font-extrabold tabular-nums text-qm-text">r = {corrText}</div>
        {corr && (
          <span className="mt-2 inline-block rounded-full bg-qm-green-bg px-3 py-0.5 text-xs font-medium text-qm-green">
            {corr.correlation_label}
          </span>
        )}
        {corr && <p className="mx-auto mt-3 max-w-xl text-sm text-qm-text2">{corr.interpretation}</p>}
      </div>

      {/* Section 4 — dual-axis chart */}
      <div className="mb-6 rounded-xl border border-qm-border bg-qm-card p-4">
        <h2 className="mb-3 text-sm font-semibold text-qm-text">Sentiment vs Next-Day Return</h2>
        {corrLoading ? (
          <div className="flex h-[260px] items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-qm-green" />
          </div>
        ) : (
          <CorrelationChart samples={corr?.samples ?? []} />
        )}
      </div>

      {/* Section 5 — signal accuracy */}
      {corr?.accuracy && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-qm-text">Signal Accuracy</h2>
          <div className="overflow-hidden rounded-xl border border-qm-border">
            <div
              className={cn(
                ACC_GRID,
                "border-b border-qm-border bg-qm-card px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-qm-text3",
              )}
            >
              <span>Signal</span>
              <span>Occurrences</span>
              <span>Correct</span>
              <span>Accuracy</span>
            </div>
            <div className="divide-y divide-qm-border">
              <AccuracyRow label="Positive (>0.3)" b={corr.accuracy.positive} />
              <AccuracyRow label="Negative (<-0.3)" b={corr.accuracy.negative} />
              <AccuracyRow label="Neutral" b={corr.accuracy.neutral} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
