"use client";
import Link from "next/link";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SummaryResponse } from "@/lib/types";
import { SentimentGauge } from "@/components/dashboard/sentiment-gauge";
import { WhatChangedBox } from "@/components/dashboard/what-changed-box";
import { SourceArticles } from "@/components/dashboard/source-articles";
import { HistoryAccordion } from "@/components/dashboard/history-accordion";
import { useRefreshTicker } from "@/hooks/use-refresh";
import { useDashboardStore } from "@/stores/dashboard-store";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Deterministic — analyzed_at is naive-UTC "YYYY-MM-DDTHH:MM:SS".
function fmtDateTime(iso: string): string {
  const [datePart, timePart = ""] = iso.split("T");
  const [y, m, d] = datePart.split("-").map(Number);
  if (!y || !m || !d) return iso;
  const hhmm = timePart.slice(0, 5);
  return `${MONTHS[m - 1]} ${d}, ${y}${hhmm ? ` ${hhmm} UTC` : ""}`;
}

export function CenterPanel({
  data,
  ticker,
}: {
  data: SummaryResponse | undefined;
  ticker: string;
}) {
  const refresh = useRefreshTicker();
  const processing = useDashboardStore((s) => s.processingTickers.has(ticker));
  const latest = data?.latest_summary ?? null;

  const refreshButton = (
    <button
      onClick={() => refresh(ticker)}
      disabled={processing}
      className="flex items-center gap-1.5 rounded-lg border border-qm-border px-3 py-1.5 text-sm text-qm-text2 transition-colors hover:border-qm-green hover:text-qm-green disabled:opacity-50"
    >
      <RefreshCw className={cn("h-3.5 w-3.5", processing && "animate-spin")} />
      {processing ? "Processing..." : "Refresh"}
    </button>
  );

  return (
    <div className="flex-1 overflow-y-auto p-6">
      {/* Ticker header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <Link
            href={`/dashboard/${ticker}`}
            className="text-3xl font-bold text-qm-text transition-colors hover:text-qm-green"
          >
            {ticker}
          </Link>
          <p className="mt-0.5 text-sm text-qm-text3">
            {latest ? `Analyzed: ${fmtDateTime(latest.analyzed_at)}` : "Not analyzed yet"}
          </p>
        </div>
        {refreshButton}
      </div>

      {!latest ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-qm-border py-20 text-center">
          <p className="text-qm-text2">
            No analysis yet for <span className="font-semibold text-qm-text">{ticker}</span>.
          </p>
          <p className="mt-1 text-sm text-qm-text3">Click Refresh to generate one (~15s).</p>
          <div className="mt-4">{refreshButton}</div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Sentiment gauge */}
          <div className="flex justify-center rounded-xl border border-qm-border bg-qm-card py-6">
            <SentimentGauge score={latest.sentiment_score ?? 0} size="lg" />
          </div>

          {/* What changed */}
          {latest.what_changed && <WhatChangedBox text={latest.what_changed} />}

          {/* News summary */}
          {latest.news_summary && (
            <section>
              <h2 className="mb-2 text-sm font-semibold text-qm-text">🗞️ News Summary</h2>
              <p className="text-sm leading-7 text-qm-text2">{latest.news_summary}</p>
            </section>
          )}

          {/* Daily synthesis */}
          {latest.final_synthesis && (
            <section>
              <h2 className="mb-2 text-sm font-semibold text-qm-text">📝 Daily Synthesis</h2>
              <p className="text-sm leading-7 text-qm-text2">{latest.final_synthesis}</p>
            </section>
          )}

          {/* Technical signals — interpretation text (raw signals are not persisted) */}
          {latest.quant_interpretation && (
            <section>
              <h2 className="mb-2 text-sm font-semibold text-qm-text">📈 Technical Signals</h2>
              <p className="text-sm leading-7 text-qm-text2">{latest.quant_interpretation}</p>
            </section>
          )}

          {/* Source articles */}
          <section>
            <h2 className="mb-2 text-sm font-semibold text-qm-text">
              📰 Source Articles ({data?.articles?.length ?? 0})
            </h2>
            <SourceArticles articles={data?.articles ?? []} />
          </section>

          {/* 7-day history */}
          <section>
            <h2 className="mb-2 text-sm font-semibold text-qm-text">🕐 7-Day History</h2>
            <HistoryAccordion summaries={data?.historical_summaries ?? []} />
          </section>
        </div>
      )}
    </div>
  );
}
