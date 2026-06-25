"use client";
import { useState } from "react";
import { useSystemStatus } from "@/hooks/use-system";
import { useDashboardStore } from "@/stores/dashboard-store";
import { Button } from "@/components/ui/button";

const TIMEZONES = [
  "UTC",
  "Asia/Kolkata",
  "America/New_York",
  "America/Los_Angeles",
  "Europe/London",
  "Asia/Tokyo",
  "Asia/Singapore",
];

export default function SchedulePage() {
  const { data: status } = useSystemStatus();
  const addNotification = useDashboardStore((s) => s.addNotification);
  const [time, setTime] = useState("08:00");
  const [tz, setTz] = useState("Asia/Kolkata");
  const [autoRefresh, setAutoRefresh] = useState(true);

  const inputClass =
    "rounded-lg border border-qm-border bg-qm-bg px-3 py-2 text-sm text-qm-text focus:border-qm-green focus:outline-none";

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-qm-border bg-qm-card2 p-3 text-xs text-qm-text3">
        Current backend schedule:{" "}
        <span className="text-qm-text2">{status?.scheduler_time ?? "—"}</span>. Changes here are mocked
        — the live schedule is configured in the backend settings + <code>run-scheduler</code>.
      </div>

      <div className="space-y-4 rounded-xl border border-qm-border bg-qm-card p-4">
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-qm-text2">Refresh Time</span>
          <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className={inputClass} />
        </label>

        <label className="block">
          <span className="mb-1 block text-sm font-medium text-qm-text2">Timezone</span>
          <select value={tz} onChange={(e) => setTz(e.target.value)} className={inputClass}>
            {TIMEZONES.map((z) => (
              <option key={z} value={z}>
                {z}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
            className="h-4 w-4 rounded border-qm-border bg-qm-bg accent-qm-green"
          />
          <span className="text-sm text-qm-text2">Auto-refresh daily</span>
        </label>

        <p className="text-xs text-qm-text3">
          Next refresh: {autoRefresh ? `Tomorrow at ${time} ${tz}` : "Disabled"}
        </p>

        <Button onClick={() => addNotification("Schedule saved (mocked)", "success")}>
          Save Schedule
        </Button>
      </div>
    </div>
  );
}
