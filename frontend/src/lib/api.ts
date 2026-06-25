import type {
  AgentRun,
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

  getSummary: (symbol: string): Promise<SummaryResponse> =>
    fetch(`${BASE}/api/summary/${symbol}`).then((r) => r.json()),

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
};
