"use client";
import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SummaryRow } from "@/lib/types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Deterministic (string-parsed) — analyzed_at is naive-UTC "YYYY-MM-DDTHH:MM:SS".
function fmtDay(iso: string): string {
  const [datePart] = iso.split("T");
  const [y, m, d] = datePart.split("-").map(Number);
  if (!m || !d) return iso;
  return `${MONTHS[m - 1]} ${d}, ${y}`;
}

export function HistoryAccordion({
  summaries,
  initialOpen = null,
}: {
  summaries: SummaryRow[];
  initialOpen?: number | null;
}) {
  const [open, setOpen] = useState<number | null>(initialOpen);

  if (!summaries?.length) {
    return <p className="text-sm text-qm-text3">No history yet.</p>;
  }

  return (
    <div className="divide-y divide-qm-border overflow-hidden rounded-lg border border-qm-border">
      {summaries.map((s, i) => {
        const score = s.sentiment_score;
        const isOpen = open === i;
        return (
          <div key={s.id}>
            <button
              onClick={() => setOpen(isOpen ? null : i)}
              className="flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm hover:bg-qm-card"
            >
              <span className="text-qm-text2">{fmtDay(s.analyzed_at)}</span>
              <span
                className={cn(
                  "tabular-nums",
                  score == null ? "text-qm-text3" : score >= 0 ? "text-qm-green" : "text-qm-red",
                )}
              >
                {score == null ? "—" : `${score >= 0 ? "+" : ""}${score.toFixed(2)}`}
              </span>
              <ChevronDown
                className={cn(
                  "ml-auto h-4 w-4 text-qm-text3 transition-transform",
                  isOpen && "rotate-180",
                )}
              />
            </button>
            {isOpen && (
              <div className="space-y-2 px-3 pb-3 text-sm text-qm-text2">
                {s.what_changed && (
                  <p>
                    <span className="font-medium text-qm-amber">What changed: </span>
                    {s.what_changed}
                  </p>
                )}
                {s.final_synthesis && <p className="leading-relaxed">{s.final_synthesis}</p>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
