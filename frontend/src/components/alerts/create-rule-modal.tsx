"use client";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useTickers } from "@/hooks/use-tickers";
import { useCreateAlertRule } from "@/hooks/use-alerts";
import { useDashboardStore } from "@/stores/dashboard-store";
import { Button } from "@/components/ui/button";
import type { AlertConditionType } from "@/lib/types";

const CONDITIONS: { value: AlertConditionType; label: string }[] = [
  { value: "sentiment_below", label: "Sentiment drops below threshold" },
  { value: "sentiment_above", label: "Sentiment rises above threshold" },
  { value: "daily_summary", label: "Daily morning summary" },
];

export function CreateRuleModal({ onClose }: { onClose: () => void }) {
  const { data: tickers } = useTickers();
  const create = useCreateAlertRule();
  const addNotification = useDashboardStore((s) => s.addNotification);
  const [scope, setScope] = useState<"any" | "specific">("any");
  const [ticker, setTicker] = useState("");
  const [cond, setCond] = useState<AlertConditionType>("sentiment_below");
  const [threshold, setThreshold] = useState(-0.5);

  const isSentiment = cond === "sentiment_below" || cond === "sentiment_above";
  const isBelow = cond === "sentiment_below";
  const effectiveTicker = scope === "specific" ? ticker : "";
  const who = effectiveTicker || "any ticker";

  const presets = isBelow ? [-0.7, -0.5, -0.3] : [0.7, 0.5, 0.3];
  const presetLabels = ["Conservative", "Moderate", "Sensitive"];

  const preview = (() => {
    if (cond === "sentiment_below")
      return `When ${who} sentiment drops below ${threshold.toFixed(2)}, send a Telegram message.`;
    if (cond === "sentiment_above")
      return `When ${who} sentiment rises above ${threshold.toFixed(2)}, send a Telegram message.`;
    if (cond === "new_sec_filing")
      return `When ${who} files a new SEC 8-K, send a Telegram message.`;
    return `Send a daily morning summary for ${who} via Telegram.`;
  })();

  const fieldClass =
    "w-full rounded-lg border border-qm-border bg-qm-bg px-3 py-2 text-sm text-qm-text focus:border-qm-green focus:outline-none";

  const save = async () => {
    if (scope === "specific" && !ticker) {
      addNotification("Pick a ticker or choose 'Any ticker'.", "warning");
      return;
    }
    const res = await create.mutateAsync({
      ticker: effectiveTicker || null,
      condition_type: cond,
      threshold: isSentiment ? threshold : null,
    });
    if (res.success) {
      addNotification("Alert rule created", "success");
      onClose();
    } else {
      addNotification(res.detail || "Failed to create rule", "error");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-xl border border-qm-border bg-qm-card p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-4 text-lg font-bold text-qm-text">Create Alert Rule</h3>

        <div className="space-y-4">
          {/* Field 1 — ticker scope */}
          <div>
            <span className="mb-1.5 block text-sm font-medium text-qm-text2">Ticker</span>
            <div className="flex gap-2">
              {(["any", "specific"] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setScope(s)}
                  className={cn(
                    "flex-1 rounded-lg border px-3 py-1.5 text-sm transition-colors",
                    scope === s
                      ? "border-qm-green bg-qm-green-bg text-qm-green"
                      : "border-qm-border text-qm-text2 hover:text-qm-text",
                  )}
                >
                  {s === "any" ? "Any ticker" : "Specific ticker"}
                </button>
              ))}
            </div>
            {scope === "specific" && (
              <select
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                className={cn(fieldClass, "mt-2")}
              >
                <option value="">Select a ticker…</option>
                {(tickers ?? []).map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Field 2 — condition */}
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-qm-text2">Condition</span>
            <select
              value={cond}
              onChange={(e) => setCond(e.target.value as AlertConditionType)}
              className={fieldClass}
            >
              {CONDITIONS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>

          {/* Field 3 — threshold (sentiment only) */}
          {isSentiment && (
            <div>
              <span className="mb-1 flex justify-between text-sm font-medium text-qm-text2">
                <span>Threshold</span>
                <span className="tabular-nums text-qm-green">{threshold.toFixed(2)}</span>
              </span>
              <input
                type="range"
                min={-1}
                max={1}
                step={0.1}
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full accent-qm-green"
              />
              <div className="mt-2 flex gap-2">
                {presets.map((p, i) => (
                  <button
                    key={p}
                    onClick={() => setThreshold(p)}
                    className={cn(
                      "flex-1 rounded border px-2 py-1 text-xs transition-colors",
                      threshold === p
                        ? "border-qm-green text-qm-green"
                        : "border-qm-border text-qm-text3 hover:text-qm-text2",
                    )}
                  >
                    {presetLabels[i]} {p > 0 ? "+" : ""}
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Preview */}
          <div className="rounded-lg border border-qm-border bg-qm-bg p-3 text-xs text-qm-text2">
            {preview}
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button size="sm" loading={create.isPending} onClick={save}>
            Create Rule
          </Button>
        </div>
      </div>
    </div>
  );
}
