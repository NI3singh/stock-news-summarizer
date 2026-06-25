import type {
  AgentRun,
  AlertEvent,
  AlertRule,
  AlertStatus,
  JobResponse,
  SummaryResponse,
  SystemStatus,
  TickersResponse,
} from "@/lib/types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
  getTickers: (): Promise<TickersResponse> =>
    fetch(`${BASE}/api/tickers`).then((r) => r.json()),

  addTicker: (
    symbol: string,
  ): Promise<{ success: boolean; message?: string; detail?: string }> =>
    fetch(`${BASE}/api/tickers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol }),
    }).then((r) => r.json()),

  removeTicker: (symbol: string): Promise<{ success: boolean; message: string }> =>
    fetch(`${BASE}/api/tickers/${symbol}`, { method: "DELETE" }).then((r) => r.json()),

  getSummary: (symbol: string, days = 7): Promise<SummaryResponse> =>
    fetch(`${BASE}/api/summary/${symbol}?days=${days}`).then((r) => r.json()),

  refreshTicker: (symbol: string): Promise<{ success: boolean; job_id: string }> =>
    fetch(`${BASE}/api/refresh/${symbol}`, { method: "POST" }).then((r) => r.json()),

  refreshAll: (): Promise<{ success: boolean; job_map: Record<string, string> }> =>
    fetch(`${BASE}/api/refresh-all`, { method: "POST" }).then((r) => r.json()),

  getJob: (jobId: string): Promise<JobResponse> =>
    fetch(`${BASE}/api/job/${jobId}`).then((r) => r.json()),

  getSystemStatus: (): Promise<SystemStatus> =>
    fetch(`${BASE}/api/system/status`).then((r) => r.json()),

  getAgentRuns: (limit = 50): Promise<{ runs: AgentRun[] }> =>
    fetch(`${BASE}/api/system/agent-runs?limit=${limit}`).then((r) => r.json()),

  // --- Alerts (Phase B) ---
  getAlertStatus: (): Promise<AlertStatus> =>
    fetch(`${BASE}/api/alerts/status`).then((r) => r.json()),

  getAlertRules: (): Promise<{ rules: AlertRule[] }> =>
    fetch(`${BASE}/api/alerts/rules`).then((r) => r.json()),

  createAlertRule: (
    rule: Partial<AlertRule>,
  ): Promise<{ success: boolean; rule_id?: number; detail?: string }> =>
    fetch(`${BASE}/api/alerts/rules`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rule),
    }).then((r) => r.json()),

  deleteAlertRule: (id: number): Promise<{ success: boolean }> =>
    fetch(`${BASE}/api/alerts/rules/${id}`, { method: "DELETE" }).then((r) => r.json()),

  updateAlertRule: (id: number, is_active: boolean): Promise<{ success: boolean }> =>
    fetch(`${BASE}/api/alerts/rules/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_active }),
    }).then((r) => r.json()),

  sendTestNotification: (): Promise<{ success: boolean; message: string }> =>
    fetch(`${BASE}/api/alerts/test`, { method: "POST" }).then((r) => r.json()),

  getAlertEvents: (): Promise<{ events: AlertEvent[] }> =>
    fetch(`${BASE}/api/alerts/events`).then((r) => r.json()),
};
