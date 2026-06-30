"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Loader2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSummary } from "@/hooks/use-tickers";
import { useAgentRuns } from "@/hooks/use-system";
import { useRefreshTicker } from "@/hooks/use-refresh";
import { useDashboardStore } from "@/stores/dashboard-store";
import { SentimentTimeline } from "@/components/charts/sentiment-timeline";
import { RsiGauge } from "@/components/charts/rsi-gauge";
import { AgentTimeline } from "@/components/dashboard/agent-timeline";
import { WhatChangedBox } from "@/components/dashboard/what-changed-box";
import { SourceArticles } from "@/components/dashboard/source-articles";
import { HistoryAccordion } from "@/components/dashboard/history-accordion";
import { MarketDataCard } from "@/components/dashboard/market-data-card";
import { AnalysisInProgress } from "@/components/dashboard/analysis-in-progress";

function StatCard({
  label,
  value,
  sub,
  valueClass,
}: {
  label: string;
  value: string;
  sub?: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-xl border border-qm-border bg-qm-card p-4">
      <div className="text-[10px] uppercase tracking-wider text-qm-text3">{label}</div>
      <div className={cn("mt-1 text-2xl font-bold tabular-nums text-qm-text", valueClass)}>
        {value}
      </div>
      {sub && <div className="text-xs text-qm-text2">{sub}</div>}
    </div>
  );
}

export default function TickerDetailPage() {
  const params = useParams();
  const ticker = String(params.ticker ?? "").toUpperCase();
  const { data, isLoading } = useSummary(ticker, 30);
  const { data: allRuns } = useAgentRuns(50);
  const refresh = useRefreshTicker();
  const processing = useDashboardStore((s) => s.processingTickers.has(ticker));

  const latest = data?.latest_summary ?? null;
  const articles = data?.articles ?? [];
  const history = data?.historical_summaries ?? [];
  const tickerRuns = (allRuns ?? []).filter((r) => r.ticker === ticker);

  const sentiment = latest?.sentiment_score ?? null;
  const sig = latest?.technical_signals ?? null;

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
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-5 flex items-center justify-between">
        <Link
          href="/dashboard"
          className="flex items-center gap-1.5 text-sm text-qm-text3 transition-colors hover:text-qm-text2"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Dashboard
        </Link>
        {refreshButton}
      </div>
      <h1 className="mb-6 text-2xl font-bold text-qm-text">{ticker}</h1>

      {isLoading ? (
        <div className="flex items-center gap-2 text-qm-text2">
          <Loader2 className="h-4 w-4 animate-spin text-qm-green" /> Loading {ticker}...
        </div>
      ) : !latest ? (
        processing ? (
          <AnalysisInProgress key={ticker} ticker={ticker} />
        ) : (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-qm-border py-20 text-center">
            <p className="text-qm-text2">
              No analysis yet for <span className="font-semibold text-qm-text">{ticker}</span>.
            </p>
            <div className="mt-4">{refreshButton}</div>
          </div>
        )
      ) : (
        <div className="space-y-6">
          {/* ROW 1 — stat cards */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard
              label="Sentiment"
              value={sentiment == null ? "—" : `${sentiment >= 0 ? "+" : ""}${sentiment.toFixed(2)}`}
              sub={
                sentiment == null
                  ? undefined
                  : sentiment > 0.2
                    ? "Bullish"
                    : sentiment < -0.2
                      ? "Bearish"
                      : "Neutral"
              }
              valueClass={sentiment == null ? "" : sentiment >= 0 ? "text-qm-green" : "text-qm-red"}
            />
            <StatCard
              label="RSI"
              value={sig?.rsi == null ? "N/A" : sig.rsi.toFixed(1)}
              sub={
                sig?.rsi == null
                  ? undefined
                  : sig.rsi > 70
                    ? "Overbought"
                    : sig.rsi < 30
                      ? "Oversold"
                      : "Neutral"
              }
            />
            <StatCard
              label="Volume"
              value={sig?.volume_ratio == null ? "N/A" : `${sig.volume_ratio.toFixed(1)}x`}
              sub={
                sig?.volume_ratio == null
                  ? undefined
                  : sig.volume_ratio > 1
                    ? "Above avg"
                    : "Below avg"
              }
            />
            <StatCard label="Articles" value={String(articles.length)} sub="analyzed" />
          </div>

          {/* ROW 2 — charts */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-xl border border-qm-border bg-qm-card p-4">
              <h2 className="mb-3 text-sm font-semibold text-qm-text">30-Day Sentiment</h2>
              <SentimentTimeline summaries={history} />
            </div>
            <div className="flex flex-col rounded-xl border border-qm-border bg-qm-card p-4">
              <h2 className="mb-3 text-sm font-semibold text-qm-text">Technical (RSI)</h2>
              <div className="flex flex-1 items-center justify-center">
                <RsiGauge value={sig?.rsi ?? null} />
              </div>
            </div>
          </div>

          {/* Market data (yfinance fundamentals) */}
          <MarketDataCard data={latest.market_data} />

          {/* ROW 3 — what changed + synthesis */}
          {latest.what_changed && <WhatChangedBox text={latest.what_changed} />}
          {latest.final_synthesis && (
            <section>
              <h2 className="mb-2 text-sm font-semibold text-qm-text">📝 Daily Synthesis</h2>
              <p className="text-sm leading-7 text-qm-text2">{latest.final_synthesis}</p>
            </section>
          )}

          {/* ROW 4 — articles + agent timeline */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <section>
              <h2 className="mb-2 text-sm font-semibold text-qm-text">
                📰 Source Articles ({articles.length})
              </h2>
              <SourceArticles articles={articles} />
            </section>
            <section>
              <h2 className="mb-2 text-sm font-semibold text-qm-text">🔗 Agent Run Timeline</h2>
              <AgentTimeline agentRuns={tickerRuns} />
            </section>
          </div>

          {/* ROW 5 — 7-day history (expanded by default) */}
          <section>
            <h2 className="mb-2 text-sm font-semibold text-qm-text">🕐 7-Day History</h2>
            <HistoryAccordion summaries={history} initialOpen={0} />
          </section>
        </div>
      )}
    </div>
  );
}
