"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";

const SETUP_STEPS = [
  "Open Claude Desktop → Settings → Developer → MCP Servers",
  "Click 'Add Server' → enter name 'QuantMind' and the URL above",
  "Restart Claude Desktop — QuantMind tools appear in your conversations",
];

const EXAMPLE_QUERIES = [
  "What's the current sentiment on AAPL?",
  "Compare AAPL, MSFT, and NVDA sentiment",
  "What's the QuantMind system status?",
  "Show me the entity graph for NVDA",
];

// Sample query per real tool (for the per-tool "Example" copy button).
const TOOL_EXAMPLES: Record<string, string> = {
  get_stock_analysis: "What's the latest analysis for AAPL?",
  run_stock_analysis: "Run a fresh analysis on TSLA",
  get_watchlist: "What's in my QuantMind watchlist?",
  compare_tickers: "Compare AAPL, MSFT and NVDA",
  get_system_status: "What's the QuantMind system status?",
  get_ml_signal: "What's the ML signal for AAPL?",
  get_entity_graph: "Show me the entity graph for NVDA",
};

function CopyButton({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };
  return (
    <button
      onClick={copy}
      className="flex flex-shrink-0 items-center gap-1.5 rounded-lg border border-qm-border px-3 py-1.5 text-xs text-qm-text2 transition-colors hover:border-qm-green hover:text-qm-green"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-qm-green" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied" : (label ?? "Copy")}
    </button>
  );
}

function StatCard({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-xl border border-qm-border bg-qm-card p-4">
      <div className="text-[10px] uppercase tracking-wider text-qm-text3">{label}</div>
      <div className={cn("mt-1 text-lg font-bold text-qm-text", valueClass)}>{value}</div>
    </div>
  );
}

export default function McpPage() {
  const { data: mcp } = useQuery({ queryKey: ["mcp-status"], queryFn: api.getMcpStatus });
  const running = mcp?.running ?? false;
  const tools = mcp?.tools ?? [];
  const url = mcp?.url ?? "http://127.0.0.1:8765/mcp";

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-2xl font-bold text-qm-text">MCP Server</h1>
        <span
          className={cn(
            "rounded-full px-2.5 py-0.5 text-xs font-medium",
            running ? "bg-qm-green-bg text-qm-green" : "bg-qm-card2 text-qm-text3",
          )}
        >
          {running ? "● Running" : "○ Stopped"}
        </span>
      </div>

      {/* Status cards */}
      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatCard
          label="Status"
          value={running ? "● Running" : "○ Stopped"}
          valueClass={running ? "text-qm-green" : "text-qm-red"}
        />
        <StatCard label="Port" value={String(mcp?.port ?? "—")} />
        <StatCard label="Tools Available" value={`${tools.length} tools`} />
      </div>

      {/* Connection URL */}
      <div className="mb-6">
        <div className="mb-2 text-sm font-semibold text-qm-text">Connection URL</div>
        <div className="flex items-center gap-3 rounded-lg border border-qm-border bg-qm-bg p-3">
          <code className="flex-1 break-all font-mono text-sm text-qm-green">{url}</code>
          <CopyButton text={url} label="Copy URL" />
        </div>
      </div>

      {/* Not-running hint */}
      {!running && (
        <div className="mb-6 rounded-lg border border-qm-amber/30 bg-qm-amber-bg p-3 text-xs text-qm-text2">
          The MCP server runs as a separate process. Start it with{" "}
          <span className="font-mono text-qm-text">quantmind mcp-server</span> (or{" "}
          <span className="font-mono text-qm-text">quantmind run-scheduler --with-mcp</span>).
        </div>
      )}

      {/* Setup guide */}
      <div className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-qm-text">Connect Claude Desktop</h2>
        <div className="space-y-2">
          {SETUP_STEPS.map((s, i) => (
            <div
              key={i}
              className="flex items-start gap-3 rounded-xl border border-qm-border bg-qm-card p-3"
            >
              <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-qm-green text-xs font-bold text-white">
                {i + 1}
              </span>
              <span className="text-sm text-qm-text2">{s}</span>
            </div>
          ))}
        </div>

        <h3 className="mb-2 mt-4 text-sm font-semibold text-qm-text">What can you ask Claude?</h3>
        <div className="space-y-1.5">
          {EXAMPLE_QUERIES.map((q) => (
            <div
              key={q}
              className="flex items-center justify-between gap-2 rounded-lg border border-qm-border bg-qm-card px-3 py-2"
            >
              <span className="text-sm text-qm-text2">“{q}”</span>
              <CopyButton text={q} />
            </div>
          ))}
        </div>
      </div>

      {/* Available tools */}
      <div className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-qm-text">Available Tools ({tools.length})</h2>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {tools.map((t) => (
            <div key={t.name} className="rounded-xl border border-qm-border bg-qm-card p-3">
              <div className="flex items-center justify-between gap-2">
                <code className="font-mono text-sm text-qm-green">{t.name}</code>
                {TOOL_EXAMPLES[t.name] && <CopyButton text={TOOL_EXAMPLES[t.name]} label="Example" />}
              </div>
              <p className="mt-1 text-xs text-qm-text3">{t.description}</p>
            </div>
          ))}
          {tools.length === 0 && <p className="text-sm text-qm-text3">No tools listed.</p>}
        </div>
      </div>

      {/* Recent MCP calls */}
      <div>
        <h2 className="mb-3 text-sm font-semibold text-qm-text">Recent MCP Calls</h2>
        <div className="rounded-xl border border-dashed border-qm-border p-6 text-center text-sm text-qm-text3">
          No calls recorded yet — connect Claude Desktop to start.
          <div className="mt-1 text-xs">
            (Calls run in the MCP server process and aren&apos;t tracked here yet.)
          </div>
        </div>
      </div>
    </div>
  );
}
