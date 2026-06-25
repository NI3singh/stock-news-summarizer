"use client";
import { useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { SUMMARY_KEY, useTickers } from "@/hooks/use-tickers";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import type { SummaryRow } from "@/lib/types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function fmtDateTime(iso: string): string {
  const [datePart, timePart = ""] = iso.split("T");
  const [y, m, d] = datePart.split("-").map(Number);
  if (!y || !m || !d) return iso;
  const hhmm = timePart.slice(0, 5);
  return `${MONTHS[m - 1]} ${d}, ${y}${hhmm ? ` · ${hhmm}` : ""}`;
}

type Row = SummaryRow & { sources: number };
const GRID = "grid grid-cols-[1.6fr_0.7fr_1.1fr_0.8fr_0.6fr] gap-2";

export default function HistoryPage() {
  const { data: tickers, isLoading: tickersLoading } = useTickers();
  const summaryQueries = useQueries({
    queries: (tickers ?? []).map((t) => ({
      queryKey: SUMMARY_KEY(t),
      queryFn: () => api.getSummary(t),
    })),
  });
  const [tickerFilter, setTickerFilter] = useState("ALL");
  const [sentFilter, setSentFilter] = useState("ALL");
  const [expanded, setExpanded] = useState<string | null>(null);

  const loading = tickersLoading || summaryQueries.some((q) => q.isLoading);

  const allRows: Row[] = summaryQueries
    .flatMap((q) =>
      (q.data?.historical_summaries ?? []).map((s) => ({
        ...s,
        sources: s.articles_used?.length ?? 0,
      })),
    )
    .sort((a, b) => (a.analyzed_at < b.analyzed_at ? 1 : -1));

  const filtered = allRows.filter((r) => {
    if (tickerFilter !== "ALL" && r.ticker !== tickerFilter) return false;
    if (sentFilter !== "ALL") {
      const sc = r.sentiment_score ?? 0;
      if (sentFilter === "POS" && sc <= 0.2) return false;
      if (sentFilter === "NEG" && sc >= -0.2) return false;
      if (sentFilter === "NEU" && (sc > 0.2 || sc < -0.2)) return false;
    }
    return true;
  });

  const selectClass =
    "rounded-lg border border-qm-border bg-qm-card px-3 py-1.5 text-sm text-qm-text2 focus:border-qm-green focus:outline-none";

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-2xl font-bold text-qm-text">Analysis History</h1>

      <div className="mb-4 flex flex-wrap gap-2">
        <select value={tickerFilter} onChange={(e) => setTickerFilter(e.target.value)} className={selectClass}>
          <option value="ALL">All Tickers</option>
          {(tickers ?? []).map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select value={sentFilter} onChange={(e) => setSentFilter(e.target.value)} className={selectClass}>
          <option value="ALL">All Sentiment</option>
          <option value="POS">Positive</option>
          <option value="NEU">Neutral</option>
          <option value="NEG">Negative</option>
        </select>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon="🗂️"
          title="No analysis history yet"
          description="Add tickers and run your first analysis."
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-qm-border">
          <div
            className={cn(
              GRID,
              "border-b border-qm-border bg-qm-card px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-qm-text3",
            )}
          >
            <span>Date</span>
            <span>Ticker</span>
            <span>Sentiment</span>
            <span>Themes</span>
            <span>Sources</span>
          </div>
          {filtered.map((r) => {
            const key = `${r.ticker}-${r.id}`;
            const sc = r.sentiment_score;
            const isOpen = expanded === key;
            return (
              <div key={key} className="border-b border-qm-border last:border-0">
                <button
                  onClick={() => setExpanded(isOpen ? null : key)}
                  className={cn(GRID, "w-full items-center px-4 py-3 text-left text-sm hover:bg-qm-card")}
                >
                  <span className="text-qm-text2">{fmtDateTime(r.analyzed_at)}</span>
                  <span>
                    <span className="rounded bg-qm-card2 px-1.5 py-0.5 text-xs font-semibold text-qm-text">
                      {r.ticker}
                    </span>
                  </span>
                  <span
                    className={cn(
                      "tabular-nums",
                      sc == null ? "text-qm-text3" : sc >= 0 ? "text-qm-green" : "text-qm-red",
                    )}
                  >
                    {sc == null
                      ? "—"
                      : `${sc >= 0 ? "+" : ""}${sc.toFixed(2)} ${sc > 0.2 ? "▲" : sc < -0.2 ? "▼" : "·"}`}
                  </span>
                  <span className="text-qm-text3">—</span>
                  <span className="text-qm-text2">{r.sources}</span>
                </button>
                {isOpen && r.what_changed && (
                  <div className="bg-qm-bg/40 px-4 pb-3 text-sm text-qm-text2">
                    <span className="font-medium text-qm-amber">What changed: </span>
                    {r.what_changed}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
