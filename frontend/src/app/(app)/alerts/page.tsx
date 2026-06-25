"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Bell, FileText, Plus, Send, Sun, X } from "lucide-react";
import { api } from "@/lib/api";
import { useTickers } from "@/hooks/use-tickers";
import { useSystemStatus } from "@/hooks/use-system";
import {
  useAlertRules,
  useAlertStatus,
  useCreateAlertRule,
  useDeleteAlertRule,
} from "@/hooks/use-alerts";
import { useDashboardStore } from "@/stores/dashboard-store";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import type { AlertConditionType, AlertRule } from "@/lib/types";

const COND_LABEL: Record<AlertConditionType, string> = {
  sentiment_below: "Sentiment Below",
  sentiment_above: "Sentiment Above",
  new_sec_filing: "SEC Filing",
  daily_summary: "Daily Summary",
};

function ruleIcon(c: AlertConditionType) {
  if (c === "new_sec_filing") return <FileText className="h-4 w-4" />;
  if (c === "daily_summary") return <Sun className="h-4 w-4" />;
  return <Bell className="h-4 w-4" />;
}

function describeRule(r: AlertRule): string {
  const who = r.ticker ?? "any ticker";
  switch (r.condition_type) {
    case "sentiment_below":
      return `Alert when ${who} sentiment drops below ${r.threshold ?? "—"}`;
    case "sentiment_above":
      return `Alert when ${who} sentiment rises above ${r.threshold ?? "—"}`;
    case "new_sec_filing":
      return `Alert on a new SEC filing for ${who}`;
    case "daily_summary":
      return `Daily summary for ${who}`;
    default:
      return "Alert rule";
  }
}

function fmtWhen(iso: string | null): string {
  if (!iso) return "Never";
  return iso.replace("T", " ").slice(0, 16);
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-qm-border bg-qm-card p-4">
      <div className="text-[10px] uppercase tracking-wider text-qm-text3">{label}</div>
      <div className="mt-1 truncate text-lg font-bold text-qm-text">{value}</div>
    </div>
  );
}

function CreateRuleModal({ onClose }: { onClose: () => void }) {
  const { data: tickers } = useTickers();
  const create = useCreateAlertRule();
  const addNotification = useDashboardStore((s) => s.addNotification);
  const [ticker, setTicker] = useState("");
  const [cond, setCond] = useState<AlertConditionType>("sentiment_below");
  const [threshold, setThreshold] = useState(-0.5);

  const isSentiment = cond === "sentiment_below" || cond === "sentiment_above";
  const selectClass =
    "w-full rounded-lg border border-qm-border bg-qm-bg px-3 py-2 text-sm text-qm-text focus:border-qm-green focus:outline-none";

  const save = async () => {
    const res = await create.mutateAsync({
      ticker: ticker || null,
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
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-qm-text2">Ticker</span>
            <select value={ticker} onChange={(e) => setTicker(e.target.value)} className={selectClass}>
              <option value="">Any ticker</option>
              {(tickers ?? []).map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-qm-text2">Condition</span>
            <select
              value={cond}
              onChange={(e) => setCond(e.target.value as AlertConditionType)}
              className={selectClass}
            >
              {(Object.keys(COND_LABEL) as AlertConditionType[]).map((c) => (
                <option key={c} value={c}>
                  {COND_LABEL[c]}
                </option>
              ))}
            </select>
          </label>

          {isSentiment && (
            <label className="block">
              <span className="mb-1 flex justify-between text-sm font-medium text-qm-text2">
                <span>Threshold</span>
                <span className="tabular-nums text-qm-green">{threshold.toFixed(1)}</span>
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
            </label>
          )}
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

export default function AlertsPage() {
  const router = useRouter();
  const { data: status } = useAlertStatus();
  const { data: rules } = useAlertRules();
  const { data: sysStatus } = useSystemStatus();
  const del = useDeleteAlertRule();
  const addNotification = useDashboardStore((s) => s.addNotification);
  const [modalOpen, setModalOpen] = useState(false);
  const [testing, setTesting] = useState(false);

  const connected = status?.connected ?? false;
  const ruleList = rules ?? [];
  const lastSent = ruleList
    .map((r) => r.last_triggered_at)
    .filter((x): x is string => Boolean(x))
    .sort()
    .reverse()[0];

  const sendTest = async () => {
    setTesting(true);
    const res = await api.sendTestNotification();
    addNotification(res.message, res.success ? "success" : "error");
    setTesting(false);
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-4 text-2xl font-bold text-qm-text">Alerts</h1>

      {/* Telegram connection banner */}
      {connected ? (
        <div className="mb-6 flex items-center justify-between rounded-xl border border-qm-green/30 bg-qm-green-bg p-4">
          <div className="text-sm text-qm-text">
            ✅ Telegram connected
            {status?.chat_id ? (
              <span className="text-qm-text3"> · Chat ID: {status.chat_id}</span>
            ) : null}
          </div>
          <Button size="sm" variant="outline" loading={testing} onClick={sendTest}>
            <Send className="h-3.5 w-3.5" /> Send test
          </Button>
        </div>
      ) : (
        <div className="mb-6 flex items-center justify-between rounded-xl border border-qm-amber/30 bg-qm-amber-bg p-4">
          <div className="text-sm text-qm-text">⚠️ Telegram not connected</div>
          <Button size="sm" onClick={() => router.push("/alerts/setup")}>
            Connect Now →
          </Button>
        </div>
      )}

      {/* Quick stats */}
      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatCard label="Active Rules" value={String(ruleList.length)} />
        <StatCard label="Last Alert Sent" value={fmtWhen(lastSent ?? null)} />
        <StatCard label="Next Daily Summary" value={sysStatus?.scheduler_time ?? "—"} />
      </div>

      {/* Rules */}
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-qm-text">Alert Rules</h2>
        <Button size="sm" onClick={() => setModalOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> Create Rule
        </Button>
      </div>

      {ruleList.length === 0 ? (
        <EmptyState
          icon="🔔"
          title="No alert rules yet"
          description="Create your first rule to get notified on Telegram."
        />
      ) : (
        <div className="space-y-2">
          {ruleList.map((r) => (
            <div
              key={r.id}
              className="flex items-center gap-3 rounded-xl border border-qm-border bg-qm-card p-4"
            >
              <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-qm-green-bg text-qm-green">
                {ruleIcon(r.condition_type)}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-qm-text">{describeRule(r)}</div>
                <div className="text-xs text-qm-text3">
                  via {r.delivery_channel} · last triggered: {fmtWhen(r.last_triggered_at)}
                </div>
              </div>
              <span className="rounded-full bg-qm-green-bg px-2 py-0.5 text-xs font-medium text-qm-green">
                Active
              </span>
              <button
                onClick={() => r.id != null && del.mutate(r.id)}
                className="text-qm-text3 transition-colors hover:text-qm-red"
                title="Delete rule"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {modalOpen && <CreateRuleModal onClose={() => setModalOpen(false)} />}
    </div>
  );
}
