import { Bell, FileText, Sun, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AlertRule } from "@/lib/types";

function iconFor(r: AlertRule): { icon: React.ReactNode; cls: string } {
  switch (r.condition_type) {
    case "sentiment_below":
      return { icon: <Bell className="h-4 w-4" />, cls: "bg-red-500/10 text-red-400" };
    case "sentiment_above":
      return { icon: <Bell className="h-4 w-4" />, cls: "bg-qm-green-bg text-qm-green" };
    case "new_sec_filing":
      return { icon: <FileText className="h-4 w-4" />, cls: "bg-blue-500/10 text-blue-400" };
    case "daily_summary":
      return { icon: <Sun className="h-4 w-4" />, cls: "bg-amber-500/10 text-amber-400" };
    default:
      return { icon: <Bell className="h-4 w-4" />, cls: "bg-qm-card2 text-qm-text2" };
  }
}

export function ruleTitle(r: AlertRule): string {
  const who = r.ticker ?? "Any ticker";
  switch (r.condition_type) {
    case "sentiment_below":
      return `${who} sentiment below ${r.threshold ?? "—"}`;
    case "sentiment_above":
      return `${who} sentiment above ${r.threshold ?? "—"}`;
    case "new_sec_filing":
      return `${who} — new SEC filing`;
    case "daily_summary":
      return `${who} — daily summary`;
    default:
      return "Alert rule";
  }
}

function fmtWhen(iso: string | null): string {
  if (!iso) return "Never";
  return iso.replace("T", " ").slice(0, 16);
}

export function RuleCard({
  rule,
  onDelete,
  onToggle,
}: {
  rule: AlertRule;
  onDelete: () => void;
  onToggle: () => void;
}) {
  const { icon, cls } = iconFor(rule);

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-xl border border-qm-border bg-qm-card p-4",
        !rule.is_active && "opacity-60",
      )}
    >
      <div className={cn("flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg", cls)}>
        {icon}
      </div>

      <div className="min-w-0 flex-1">
        <div className="text-sm text-qm-text">{ruleTitle(rule)}</div>
        <div className="text-xs text-qm-text3">
          via {rule.delivery_channel} · Last triggered: {fmtWhen(rule.last_triggered_at)}
        </div>
      </div>

      {/* toggle switch */}
      <button
        onClick={onToggle}
        role="switch"
        aria-checked={rule.is_active}
        title={rule.is_active ? "Active — click to pause" : "Paused — click to activate"}
        className={cn(
          "relative h-5 w-9 flex-shrink-0 rounded-full transition-colors",
          rule.is_active ? "bg-qm-green" : "bg-qm-border",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all",
            rule.is_active ? "left-[18px]" : "left-0.5",
          )}
        />
      </button>

      <button
        onClick={onDelete}
        className="text-qm-text3 transition-colors hover:text-qm-red"
        title="Delete rule"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
