import type {
  AgentRun,
  AlertEvent,
  AlertRule,
  AlertStatus,
  JobResponse,
  McpStatus,
  SummaryResponse,
  SystemStatus,
  TickersResponse,
} from "@/lib/types";
import { firebaseAuth } from "@/lib/firebase";

// Strip any trailing slash(es) so `${BASE}/api/...` never becomes `//api/...`
// (which 404s) when NEXT_PUBLIC_API_URL is set with a trailing slash.
const BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

const JSON_HEADERS = { "Content-Type": "application/json" };

/** Authorization header from the signed-in Firebase user. Empty when running in
 *  local-dev (no Firebase) or logged out — the backend then uses its dev user. */
async function authHeaders(): Promise<Record<string, string>> {
  const user = firebaseAuth?.currentUser;
  if (!user) return {};
  try {
    return { Authorization: `Bearer ${await user.getIdToken()}` };
  } catch {
    return {};
  }
}

/** fetch() against the API with BASE + the Firebase bearer token attached. */
async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = {
    ...(init.headers as Record<string, string> | undefined),
    ...(await authHeaders()),
  };
  return fetch(`${BASE}${path}`, { ...init, headers });
}

export const api = {
  getTickers: (): Promise<TickersResponse> =>
    apiFetch("/api/tickers").then((r) => r.json()),

  addTicker: async (
    symbol: string,
  ): Promise<{
    ok: boolean;
    status: number;
    success?: boolean;
    job_id?: string;
    message?: string;
    detail?: string;
  }> => {
    const r = await apiFetch("/api/tickers", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify({ symbol }),
    });
    const body = await r.json().catch(() => ({}));
    return { ok: r.ok, status: r.status, ...body };
  },

  removeTicker: (symbol: string): Promise<{ success: boolean; message: string }> =>
    apiFetch(`/api/tickers/${symbol}`, { method: "DELETE" }).then((r) => r.json()),

  getSummary: (symbol: string, days = 7): Promise<SummaryResponse> =>
    apiFetch(`/api/summary/${symbol}?days=${days}`).then((r) => r.json()),

  refreshTicker: (symbol: string): Promise<{ success: boolean; job_id: string }> =>
    apiFetch(`/api/refresh/${symbol}`, { method: "POST" }).then((r) => r.json()),

  refreshAll: (): Promise<{ success: boolean; job_map: Record<string, string> }> =>
    apiFetch("/api/refresh-all", { method: "POST" }).then((r) => r.json()),

  getJob: (jobId: string): Promise<JobResponse> =>
    apiFetch(`/api/job/${jobId}`).then((r) => r.json()),

  getSystemStatus: (): Promise<SystemStatus> =>
    apiFetch("/api/system/status").then((r) => r.json()),

  getAgentRuns: (limit = 50): Promise<{ runs: AgentRun[] }> =>
    apiFetch(`/api/system/agent-runs?limit=${limit}`).then((r) => r.json()),

  // --- Alerts (Phase B) ---
  getAlertStatus: (): Promise<AlertStatus> =>
    apiFetch("/api/alerts/status").then((r) => r.json()),

  getAlertRules: (): Promise<{ rules: AlertRule[] }> =>
    apiFetch("/api/alerts/rules").then((r) => r.json()),

  createAlertRule: (
    rule: Partial<AlertRule>,
  ): Promise<{ success: boolean; rule_id?: number; detail?: string }> =>
    apiFetch("/api/alerts/rules", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(rule),
    }).then((r) => r.json()),

  deleteAlertRule: (id: number): Promise<{ success: boolean }> =>
    apiFetch(`/api/alerts/rules/${id}`, { method: "DELETE" }).then((r) => r.json()),

  updateAlertRule: (id: number, is_active: boolean): Promise<{ success: boolean }> =>
    apiFetch(`/api/alerts/rules/${id}`, {
      method: "PATCH",
      headers: JSON_HEADERS,
      body: JSON.stringify({ is_active }),
    }).then((r) => r.json()),

  sendTestNotification: (): Promise<{ success: boolean; message: string }> =>
    apiFetch("/api/alerts/test", { method: "POST" }).then((r) => r.json()),

  getAlertEvents: (): Promise<{ events: AlertEvent[] }> =>
    apiFetch("/api/alerts/events").then((r) => r.json()),

  // --- MCP (Phase C) ---
  getMcpStatus: (): Promise<McpStatus> =>
    apiFetch("/api/mcp/status").then((r) => r.json()),
};
