import { cn } from "@/lib/utils";
import type { AgentRun } from "@/lib/types";

function agentIcon(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("memory")) return "🧠";
  if (n.includes("news")) return "📰";
  if (n.includes("quant")) return "📈";
  if (n.includes("orchestr")) return "🔗";
  return "⚙️";
}

function durColor(d: number | null): string {
  if (d == null) return "text-qm-text3";
  if (d < 5) return "text-qm-green";
  if (d <= 15) return "text-qm-amber";
  return "text-qm-red";
}

export function AgentTimeline({ agentRuns }: { agentRuns: AgentRun[] }) {
  if (!agentRuns?.length) {
    return <p className="text-sm text-qm-text3">No agent runs for this ticker yet.</p>;
  }

  const runs = agentRuns.slice(0, 8); // most recent (agent_runs come newest-first)

  return (
    <div className="space-y-3">
      {runs.map((r, i) => (
        <div key={r.id} className="relative flex items-start gap-3">
          {i < runs.length - 1 && (
            <span className="absolute left-[11px] top-7 h-[calc(100%-4px)] w-px bg-qm-border" />
          )}
          <span className="z-10 text-lg leading-none">{agentIcon(r.agent_name)}</span>
          <div className="flex-1">
            <div className="flex items-center gap-2 text-sm">
              <span className="font-medium text-qm-text">{r.agent_name}</span>
              <span className={r.success ? "text-qm-green" : "text-qm-red"}>
                {r.success ? "✓" : "✗"}
              </span>
              <span className={cn("ml-auto tabular-nums text-xs", durColor(r.duration_seconds))}>
                {r.duration_seconds != null ? `${r.duration_seconds.toFixed(1)}s` : "—"}
              </span>
            </div>
            {!r.success && r.error_message && (
              <p className="mt-0.5 text-xs text-qm-red">{r.error_message}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
