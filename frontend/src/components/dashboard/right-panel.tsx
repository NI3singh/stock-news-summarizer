"use client";
import { cn } from "@/lib/utils";
import { useAgentRuns, useSystemStatus } from "@/hooks/use-system";

// Static indices for now — Phase G wires live market data.
const INDICES = [
  { name: "S&P 500", change: "+1.24%", positive: true },
  { name: "NASDAQ", change: "+0.87%", positive: true },
  { name: "DOW", change: "-0.32%", positive: false },
];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-qm-text3">
        {title}
      </div>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-qm-text3">{label}</span>
      <span className="font-medium text-qm-text2">{value}</span>
    </div>
  );
}

export function RightPanel() {
  const { data: status } = useSystemStatus();
  const { data: runs } = useAgentRuns(8);
  const recentRuns = (runs ?? []).slice(0, 4);

  return (
    <aside className="hidden w-[280px] flex-shrink-0 overflow-y-auto border-l border-qm-border p-5 lg:block">
      <Section title="Market Pulse">
        <div className="space-y-2">
          {INDICES.map((idx) => (
            <div
              key={idx.name}
              className="flex items-center justify-between rounded-lg border border-qm-border bg-qm-card px-3 py-2"
            >
              <span className="text-sm text-qm-text2">{idx.name}</span>
              <span
                className={cn(
                  "text-sm font-semibold",
                  idx.positive ? "text-qm-green" : "text-qm-red",
                )}
              >
                {idx.positive ? "▲" : "▼"} {idx.change}
              </span>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Agent Activity">
        {recentRuns.length === 0 ? (
          <p className="text-xs text-qm-text3">No recent runs.</p>
        ) : (
          <div className="space-y-1.5">
            {recentRuns.map((r) => (
              <div key={r.id} className="flex items-center gap-2 text-xs">
                <span className={r.success ? "text-qm-green" : "text-qm-red"}>
                  {r.success ? "✓" : "✗"}
                </span>
                <span className="truncate text-qm-text2">{r.agent_name}</span>
                <span className="ml-auto tabular-nums text-qm-text3">
                  {r.duration_seconds != null ? `${r.duration_seconds.toFixed(1)}s` : "—"}
                </span>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="System Status">
        <div className="space-y-1.5 text-xs">
          <Row label="Tickers" value={status ? String(status.tickers) : "—"} />
          <Row label="Vectors" value={status ? String(status.vector_store_size) : "—"} />
          <Row label="Next refresh" value={status?.scheduler_time ?? "—"} />
        </div>
      </Section>
    </aside>
  );
}
