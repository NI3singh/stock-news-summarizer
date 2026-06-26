"use client";
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CorrelationSample } from "@/lib/types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function fmtDay(iso: string): string {
  const [datePart] = iso.split("T");
  const [, m, day] = datePart.split("-").map(Number);
  if (!m || !day) return iso;
  return `${MONTHS[m - 1]} ${day}`;
}

type Row = { date: string; sentiment: number; ret: number };

export function CorrelationChart({ samples }: { samples: CorrelationSample[] }) {
  if (!samples?.length) {
    return (
      <div className="flex h-[260px] items-center justify-center text-center text-sm text-qm-text3">
        Run more analyses to build correlation data.
      </div>
    );
  }

  const data: Row[] = samples.map((s) => ({
    date: fmtDay(s.date),
    sentiment: s.sentiment_score ?? 0,
    ret: s.next_day_return_pct,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 10, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
        <YAxis
          yAxisId="left"
          domain={[-1, 1]}
          ticks={[-1, -0.5, 0, 0.5, 1]}
          stroke="#3b82f6"
          fontSize={11}
          tickLine={false}
          width={36}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          stroke="#64748b"
          fontSize={11}
          tickLine={false}
          width={44}
          tickFormatter={(v) => `${v}%`}
        />
        <ReferenceLine yAxisId="left" y={0} stroke="#475569" strokeDasharray="4 4" />
        <Tooltip
          cursor={{ fill: "rgba(148,163,184,0.08)" }}
          content={({ active, payload, label }) => {
            if (!active || !payload || payload.length === 0) return null;
            const row = payload[0].payload as Row;
            return (
              <div className="rounded-lg border border-qm-border bg-qm-card px-3 py-2 text-xs shadow-lg">
                <div className="font-medium text-qm-text">{label}</div>
                <div className="text-[#3b82f6]">
                  Sentiment: {row.sentiment >= 0 ? "+" : ""}
                  {row.sentiment.toFixed(2)}
                </div>
                <div className={row.ret >= 0 ? "text-qm-green" : "text-qm-red"}>
                  Next-day: {row.ret >= 0 ? "+" : ""}
                  {row.ret.toFixed(2)}%
                </div>
              </div>
            );
          }}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Bar yAxisId="right" dataKey="ret" name="Next-Day Return % (right)" radius={[2, 2, 0, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.ret >= 0 ? "#22c55e" : "#ef4444"} />
          ))}
        </Bar>
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="sentiment"
          name="Sentiment Score (left)"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ r: 2 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
