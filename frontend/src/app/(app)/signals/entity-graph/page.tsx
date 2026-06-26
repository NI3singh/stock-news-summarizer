"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useTickers } from "@/hooks/use-tickers";
import { EntityGraphFlow } from "@/components/charts/entity-graph";
import { SignalsTabs } from "@/components/signals/signals-tabs";

const LEGEND = [
  { label: "Company", color: "#3b82f6" },
  { label: "Person", color: "#a855f7" },
  { label: "Product", color: "#22c55e" },
  { label: "Regulatory", color: "#f59e0b" },
  { label: "Event", color: "#06b6d4" },
];

function EmptyGraph() {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <svg width="240" height="160" viewBox="0 0 240 160" className="mb-6 opacity-30">
        <line x1="120" y1="80" x2="50" y2="40" stroke="#475569" strokeWidth="1.5" />
        <line x1="120" y1="80" x2="190" y2="40" stroke="#475569" strokeWidth="1.5" />
        <line x1="120" y1="80" x2="60" y2="130" stroke="#475569" strokeWidth="1.5" />
        <line x1="120" y1="80" x2="185" y2="125" stroke="#475569" strokeWidth="1.5" />
        <circle cx="120" cy="80" r="20" fill="#1e3a8a" stroke="#3b82f6" strokeWidth="2" />
        <circle cx="50" cy="40" r="12" fill="#581c87" stroke="#a855f7" strokeWidth="2" />
        <circle cx="190" cy="40" r="12" fill="#14532d" stroke="#22c55e" strokeWidth="2" />
        <circle cx="60" cy="130" r="12" fill="#78350f" stroke="#f59e0b" strokeWidth="2" />
        <circle cx="185" cy="125" r="12" fill="#164e63" stroke="#06b6d4" strokeWidth="2" />
      </svg>
      <h2 className="text-lg font-bold text-qm-text">No entities yet</h2>
      <p className="mt-1 max-w-sm text-sm text-qm-text3">
        The entity graph builds automatically as QuantMind analyzes news. Run a few analyses to see
        company relationships emerge.
      </p>
    </div>
  );
}

export default function EntityGraphPage() {
  const { data: tickers } = useTickers();
  const [ticker, setTicker] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["entity-graph", ticker],
    queryFn: () => api.getEntityGraph(ticker || undefined),
    refetchInterval: false,
  });

  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];
  const hasData = nodes.length > 0;
  const selectedNode = nodes.find((n) => n.name === selected);
  const selectedRels = selected
    ? edges.filter((e) => e.source === selected || e.target === selected)
    : [];

  const selectClass =
    "rounded-lg border border-qm-border bg-qm-card px-3 py-1.5 text-sm text-qm-text2 focus:border-qm-green focus:outline-none";

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex flex-shrink-0 items-center justify-between border-b border-qm-border px-6 py-3">
        <SignalsTabs />
        <select
          value={ticker}
          onChange={(e) => {
            setTicker(e.target.value);
            setSelected(null);
          }}
          className={selectClass}
        >
          <option value="">All tickers</option>
          {(tickers ?? []).map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Graph */}
        <div className="relative flex-1">
          {isLoading ? (
            <div className="flex h-full items-center justify-center">
              <Loader2 className="h-7 w-7 animate-spin text-qm-green" />
            </div>
          ) : hasData ? (
            <EntityGraphFlow nodes={nodes} edges={edges} onNodeClick={setSelected} />
          ) : (
            <EmptyGraph />
          )}
        </div>

        {/* Right panel */}
        <aside className="w-[300px] flex-shrink-0 space-y-5 overflow-y-auto border-l border-qm-border p-4">
          <div className="rounded-lg border border-qm-border bg-qm-card p-3">
            <div className="text-[10px] uppercase tracking-wider text-qm-text3">Graph Stats</div>
            <div className="mt-1 text-sm text-qm-text">
              <span className="font-bold text-qm-green">{nodes.length}</span> entities ·{" "}
              <span className="font-bold text-qm-green">{edges.length}</span> relationships
            </div>
          </div>

          <div>
            <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-qm-text3">
              Selected
            </div>
            {selectedNode ? (
              <div className="rounded-lg border border-qm-border bg-qm-card p-3">
                <div className="font-semibold text-qm-text">{selectedNode.name}</div>
                <div className="text-xs text-qm-text3">
                  {selectedNode.type.replace(/_/g, " ")} · {selectedNode.mention_count} mention
                  {selectedNode.mention_count === 1 ? "" : "s"}
                </div>
                <div className="mt-2 space-y-1">
                  {selectedRels.length === 0 ? (
                    <div className="text-xs text-qm-text3">No relationships.</div>
                  ) : (
                    selectedRels.map((r, i) => (
                      <div key={i} className="text-xs text-qm-text2">
                        {r.source === selected ? (
                          <>
                            → <span className="text-qm-green">{r.type.replace(/_/g, " ")}</span>{" "}
                            {r.target}
                          </>
                        ) : (
                          <>
                            ← <span className="text-qm-green">{r.type.replace(/_/g, " ")}</span>{" "}
                            {r.source}
                          </>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            ) : (
              <p className="text-xs text-qm-text3">Click a node to see its relationships.</p>
            )}
          </div>

          <div>
            <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-qm-text3">
              Legend
            </div>
            <div className="space-y-1.5">
              {LEGEND.map((l) => (
                <div key={l.label} className="flex items-center gap-2 text-xs text-qm-text2">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: l.color }} />
                  {l.label}
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
