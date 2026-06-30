"use client";
import { useEffect, useState } from "react";
import { Loader2, Plus } from "lucide-react";
import { useDashboardStore } from "@/stores/dashboard-store";
import { useSummary, useTickers } from "@/hooks/use-tickers";
import { useAddAndAnalyze } from "@/hooks/use-refresh";
import { CenterPanel } from "@/components/dashboard/center-panel";
import { RightPanel } from "@/components/dashboard/right-panel";
import { EmptyState } from "@/components/ui/empty-state";

function EmptyWatchlistState() {
  const { add } = useAddAndAnalyze();
  const [val, setVal] = useState("");

  const submit = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    const s = val.trim().toUpperCase();
    if (/^[A-Z]{1,10}$/.test(s)) {
      add(s);
      setVal("");
    }
  };

  return (
    <EmptyState
      icon="📈"
      title="Add your first ticker"
      description="Track a stock to get AI-powered analysis."
      action={
        <div className="relative w-full max-w-xs">
          <Plus className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-qm-text3" />
          <input
            value={val}
            onChange={(e) => setVal(e.target.value)}
            onKeyDown={submit}
            placeholder="e.g. AAPL"
            className="w-full rounded-lg border border-qm-border bg-qm-card py-2.5 pl-9 pr-3 text-sm text-qm-text placeholder:text-qm-text3 focus:border-qm-green focus:outline-none"
          />
        </div>
      }
    />
  );
}

function AnalysisLoadingState({ ticker }: { ticker: string }) {
  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-2 text-qm-text2">
        <Loader2 className="h-4 w-4 animate-spin text-qm-green" />
        <span className="text-sm">{ticker ? `Loading ${ticker}...` : "Loading..."}</span>
      </div>
      <div className="mb-6 h-40 animate-pulse rounded-xl bg-qm-card" />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-4 w-full animate-pulse rounded bg-qm-card" />
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const selectedTicker = useDashboardStore((s) => s.selectedTicker);
  const setSelectedTicker = useDashboardStore((s) => s.setSelectedTicker);
  const { data: tickers, isLoading: tickersLoading } = useTickers();
  const { data, isLoading } = useSummary(selectedTicker);

  // Auto-select the first watchlist ticker when none is chosen.
  useEffect(() => {
    if (!selectedTicker && tickers && tickers.length > 0) {
      setSelectedTicker(tickers[0]);
    }
  }, [selectedTicker, tickers, setSelectedTicker]);

  if (!tickersLoading && (!tickers || tickers.length === 0)) {
    return <EmptyWatchlistState />;
  }
  if (!selectedTicker || isLoading) {
    return <AnalysisLoadingState ticker={selectedTicker ?? ""} />;
  }

  return (
    <div className="flex h-full overflow-hidden">
      <CenterPanel data={data} ticker={selectedTicker} />
      <RightPanel />
    </div>
  );
}
