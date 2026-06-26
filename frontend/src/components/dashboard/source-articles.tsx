"use client";
import { useState } from "react";
import { ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Article } from "@/lib/types";

const SOURCE_COLORS: Record<string, string> = {
  polygon: "bg-qm-green-bg text-qm-green",
  tradingview: "bg-blue-500/10 text-blue-400",
  finviz: "bg-purple-500/10 text-purple-400",
  edgar: "bg-amber-500/10 text-amber-400",
  sec_edgar: "bg-amber-500/10 text-amber-400",
};

function sourceBadge(source: string): string {
  return SOURCE_COLORS[source.toLowerCase()] ?? "bg-qm-card2 text-qm-text2";
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function fmtDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  // Deterministic (UTC) formatting to avoid SSR/CSR hydration mismatches.
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`;
}

export function SourceArticles({ articles }: { articles: Article[] }) {
  const [showAll, setShowAll] = useState(false);

  if (!articles?.length) {
    return <p className="text-sm text-qm-text3">No source articles.</p>;
  }

  const visible = showAll ? articles : articles.slice(0, 10);

  return (
    <div className="space-y-2">
      {visible.map((a, i) => (
        <a
          key={`${a.url}-${i}`}
          href={a.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-start gap-3 rounded-lg border border-qm-border bg-qm-card p-3 transition-colors hover:border-qm-green/40"
        >
          <span
            className={cn(
              "flex-shrink-0 rounded px-2 py-0.5 text-[10px] font-semibold uppercase",
              sourceBadge(a.source),
            )}
          >
            {a.source}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-start gap-1 text-sm text-qm-text group-hover:text-qm-green">
              <span className="line-clamp-2">{a.title}</span>
              <ExternalLink className="mt-0.5 h-3 w-3 flex-shrink-0 text-qm-text3" />
            </div>
            {a.published_at && (
              <div className="mt-0.5 text-xs text-qm-text3">{fmtDate(a.published_at)}</div>
            )}
          </div>
        </a>
      ))}
      {articles.length > 10 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="text-xs text-qm-green hover:underline"
        >
          {showAll ? "Show less" : `Show all ${articles.length}`}
        </button>
      )}
    </div>
  );
}
