import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useDashboardStore } from "@/stores/dashboard-store";
import { SUMMARY_PREFIX } from "@/hooks/use-tickers";

/**
 * Returns a callback that refreshes a ticker: fires the analysis job, marks the
 * ticker as "processing", then polls the job until it finishes (or times out
 * after 2 minutes), invalidating its cached summary on success.
 */
export function useRefreshTicker() {
  const qc = useQueryClient();
  // Select only the (stable) actions so this hook never re-renders on store changes.
  const addProcessingTicker = useDashboardStore((s) => s.addProcessingTicker);
  const removeProcessingTicker = useDashboardStore((s) => s.removeProcessingTicker);
  const addNotification = useDashboardStore((s) => s.addNotification);

  return async (symbol: string) => {
    addProcessingTicker(symbol);
    addNotification(`Refreshing ${symbol}...`, "info");

    let jobId: string;
    try {
      const res = await api.refreshTicker(symbol);
      jobId = res.job_id;
    } catch {
      removeProcessingTicker(symbol);
      addNotification(`${symbol} refresh failed to start`, "error");
      return;
    }

    // Poll until done / failed.
    const poll = setInterval(async () => {
      try {
        const job = await api.getJob(jobId);
        if (job.status === "done") {
          clearInterval(poll);
          removeProcessingTicker(symbol);
          qc.invalidateQueries({ queryKey: SUMMARY_PREFIX(symbol) });
          addNotification(`${symbol} updated`, "success");
        } else if (job.status === "failed") {
          clearInterval(poll);
          removeProcessingTicker(symbol);
          addNotification(`${symbol} refresh failed`, "error");
        }
      } catch {
        // transient poll error — keep trying until the timeout below
      }
    }, 2000);

    // Safety timeout after 2 minutes — stop polling and clear the processing flag.
    setTimeout(() => {
      clearInterval(poll);
      removeProcessingTicker(symbol);
    }, 120000);
  };
}

/**
 * Returns a callback that refreshes EVERY watchlist ticker via /api/refresh-all,
 * marks each as processing, and polls all jobs until they finish (or time out).
 */
export function useRefreshAll() {
  const qc = useQueryClient();
  const addProcessingTicker = useDashboardStore((s) => s.addProcessingTicker);
  const removeProcessingTicker = useDashboardStore((s) => s.removeProcessingTicker);
  const addNotification = useDashboardStore((s) => s.addNotification);

  return async () => {
    addNotification("Refreshing all tickers...", "info");

    let jobMap: Record<string, string>;
    try {
      const res = await api.refreshAll();
      jobMap = res.job_map;
    } catch {
      addNotification("Refresh-all failed to start", "error");
      return;
    }

    const entries = Object.entries(jobMap); // [symbol, jobId][]
    if (entries.length === 0) {
      addNotification("No tickers to refresh", "warning");
      return;
    }
    entries.forEach(([symbol]) => addProcessingTicker(symbol));
    const remaining = new Set(entries.map(([s]) => s));

    const poll = setInterval(async () => {
      await Promise.all(
        entries.map(async ([symbol, jobId]) => {
          if (!remaining.has(symbol)) return;
          try {
            const job = await api.getJob(jobId);
            if (job.status === "done" || job.status === "failed") {
              remaining.delete(symbol);
              removeProcessingTicker(symbol);
              if (job.status === "done") {
                qc.invalidateQueries({ queryKey: SUMMARY_PREFIX(symbol) });
              }
            }
          } catch {
            /* transient — retry next tick */
          }
        }),
      );
      if (remaining.size === 0) {
        clearInterval(poll);
        addNotification("All tickers updated", "success");
      }
    }, 2000);

    setTimeout(() => {
      clearInterval(poll);
      remaining.forEach((s) => removeProcessingTicker(s));
    }, 180000);
  };
}
