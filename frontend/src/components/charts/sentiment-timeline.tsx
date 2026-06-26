"use client";
import { useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cn } from "@/lib/utils";
import type { SummaryRow } from "@/lib/types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function fmtDay(iso: string): string {
  const [datePart] = iso.split("T");
  const [, m, day] = datePart.split("-").map(Number);
  if (!m || !day) return iso;
  return `${MONTHS[m - 1]} ${day}`;
}

const RANGES = [
  { label: "7d", days: 7 },
  { label: "14d", days: 14 },
  { label: "30d", days: 30 },
  { label: "All", days: 99999 },
];

type Point = { date: string; iso: string; score: number; whatChanged: string };

export function SentimentTimeline({ summaries }: { summaries: SummaryRow[] }) {
  const [range, setRange] = useState(30);

  const points: Point[] = [...summaries].reverse().map((s) => ({
    date: fmtDay(s.analyzed_at),
    iso: s.analyzed_at,
    score: s.sentiment_score ?? 0,
    whatChanged: s.what_changed ?? "",
  }));

  const latestIso = points.length ? points[points.length - 1].iso : null;
  const data =
    !latestIso || range >= 99999
      ? points
      : points.filter((p) => {
          const cutoff = new Date(latestIso.slice(0, 10)).getTime() - range * 86_400_000;
          return new Date(p.iso.slice(0, 10)).getTime() >= cutoff;
        });

  const tabs = (
    <div className="mb-3 flex gap-1">
      {RANGES.map((r) => (
        <button
          key={r.label}
          onClick={() => setRange(r.days)}
          className={cn(
            "rounded px-2 py-0.5 text-xs",
            range === r.days ? "bg-qm-green-bg text-qm-green" : "text-qm-text3 hover:text-qm-text2",
          )}
        >
          {r.label}
        </button>
      ))}
    </div>
  );

  if (data.length < 2) {
    return (
      <div>
        {tabs}
        <div className="flex h-[180px] items-center justify-center text-center text-sm text-qm-text3">
          Not enough history yet — need 2+ analyses.
        </div>
      </div>
    );
  }

  const vals = data.map((d) => d.score);
  const dmax = Math.max(...vals);
  const dmin = Math.min(...vals);
  const off = dmax <= 0 ? 0 : dmin >= 0 ? 1 : dmax / (dmax - dmin);

  return (
    <div>
      {tabs}
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="sentStroke" x1="0" y1="0" x2="0" y2="1">
              <stop offset={off} stopColor="#22c55e" />
              <stop offset={off} stopColor="#ef4444" />
            </linearGradient>
            <linearGradient id="sentFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset={off} stopColor="#22c55e" stopOpacity={0.25} />
              <stop offset={off} stopColor="#ef4444" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
          <YAxis
            domain={[-1, 1]}
            ticks={[-1, -0.5, 0, 0.5, 1]}
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            width={40}
          />
          <ReferenceLine y={0} stroke="#475569" strokeDasharray="4 4" />
          <Tooltip
            cursor={{ stroke: "#475569" }}
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null;
              const p = payload[0].payload as Point;
              return (
                <div className="rounded-lg border border-qm-border bg-qm-card px-3 py-2 text-xs shadow-lg">
                  <div className="font-medium text-qm-text">{p.date}</div>
                  <div className={p.score >= 0 ? "text-qm-green" : "text-qm-red"}>
                    {p.score >= 0 ? "+" : ""}
                    {p.score.toFixed(2)}
                  </div>
                  {p.whatChanged && (
                    <div className="mt-1 max-w-[200px] text-qm-text3">
                      {p.whatChanged.slice(0, 80)}
                      {p.whatChanged.length > 80 ? "…" : ""}
                    </div>
                  )}
                </div>
              );
            }}
          />
          <Area
            type="monotone"
            dataKey="score"
            stroke="url(#sentStroke)"
            strokeWidth={2}
            fill="url(#sentFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
