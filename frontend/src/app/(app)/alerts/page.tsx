"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Send } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { useSystemStatus } from "@/hooks/use-system";
import {
  useAlertEvents,
  useAlertRules,
  useAlertStatus,
  useDeleteAlertRule,
  useToggleAlertRule,
} from "@/hooks/use-alerts";
import { useDashboardStore } from "@/stores/dashboard-store";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { RuleCard } from "@/components/alerts/rule-card";
import { CreateRuleModal } from "@/components/alerts/create-rule-modal";

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-qm-border bg-qm-card p-4">
      <div className="text-[10px] uppercase tracking-wider text-qm-text3">{label}</div>
      <div className="mt-1 truncate text-lg font-bold text-qm-text">{value}</div>
    </div>
  );
}

function fmtWhen(iso: string | null): string {
  if (!iso) return "Never";
  return iso.replace("T", " ").slice(0, 16);
}

const EVENT_GRID = "grid grid-cols-[0.8fr_1.8fr_1.2fr_0.7fr] gap-2";

export default function AlertsPage() {
  const router = useRouter();
  const { data: status } = useAlertStatus();
  const { data: rules } = useAlertRules();
  const { data: events } = useAlertEvents();
  const { data: sysStatus } = useSystemStatus();
  const del = useDeleteAlertRule();
  const toggle = useToggleAlertRule();
  const addNotification = useDashboardStore((s) => s.addNotification);
  const [modalOpen, setModalOpen] = useState(false);
  const [testing, setTesting] = useState(false);

  const connected = status?.connected ?? false;
  const ruleList = rules ?? [];
  const activeCount = ruleList.filter((r) => r.is_active).length;
  const eventList = events ?? [];
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

  const handleDelete = (id: number | null) => {
    if (id == null) return;
    if (window.confirm("Delete this alert rule?")) del.mutate(id);
  };

  const handleToggle = (id: number | null, isActive: boolean) => {
    if (id == null) return;
    toggle.mutate({ id, is_active: !isActive });
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
        <StatCard label="Active Rules" value={String(activeCount)} />
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
            <RuleCard
              key={r.id}
              rule={r}
              onDelete={() => handleDelete(r.id)}
              onToggle={() => handleToggle(r.id, r.is_active)}
            />
          ))}
        </div>
      )}

      {/* Recent alert events */}
      <div className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-qm-text">Recent Alerts</h2>
        {eventList.length === 0 ? (
          <p className="text-sm text-qm-text3">No alerts triggered yet.</p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-qm-border">
            <div
              className={cn(
                EVENT_GRID,
                "border-b border-qm-border bg-qm-card px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-qm-text3",
              )}
            >
              <span>Ticker</span>
              <span>Event</span>
              <span>Triggered</span>
              <span>Delivered</span>
            </div>
            {eventList.map((e) => (
              <div
                key={e.id}
                className={cn(EVENT_GRID, "items-center px-4 py-2.5 text-sm text-qm-text2")}
              >
                <span className="font-semibold text-qm-text">{e.ticker}</span>
                <span className="truncate">{e.message || "—"}</span>
                <span className="text-qm-text3">{fmtWhen(e.triggered_at)}</span>
                <span className={e.delivered ? "text-qm-green" : "text-qm-text3"}>
                  {e.delivered ? "✓ Sent" : "Pending"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {modalOpen && <CreateRuleModal onClose={() => setModalOpen(false)} />}
    </div>
  );
}
