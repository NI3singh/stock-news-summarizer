import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useDashboardStore } from "@/stores/dashboard-store";
import { SUMMARY_PREFIX, useAddTicker } from "@/hooks/use-tickers";

/**
 * Returns a callback that tracks a running analysis job: marks the ticker as
 * "processing", polls the job every 2s until it finishes (or times out after 2
 * minutes), and invalidates the ticker's cached summary on success so the result
 * appears automatically. Shared by add + refresh so both behave identically.
 */
export function useTrackJob() {
  const qc = useQueryClient();
  const addProcessingTicker = useDashboardStore((s) => s.addProcessingTicker);
  const removeProcessingTicker = useDashboardStore((s) => s.removeProcessingTicker);
  const addNotification = useDashboardStore((s) => s.addNotification);

  return (symbol: string, jobId: string, doneMsg?: string) => {
    addProcessingTicker(symbol);

    const poll = setInterval(async () => {
      try {
        const job = await api.getJob(jobId);
        if (job.status === "done") {
          clearInterval(poll);
          removeProcessingTicker(symbol);
          qc.invalidateQueries({ queryKey: SUMMARY_PREFIX(symbol) });
          addNotification(doneMsg ?? `${symbol} updated`, "success");
        } else if (job.status === "failed") {
          clearInterval(poll);
          removeProcessingTicker(symbol);
          addNotification(`${symbol} analysis failed`, "error");
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
 * Fallback tracker for when the backend doesn't return a job id (e.g. an older
 * build): mark the ticker processing and poll its SUMMARY until the analysis
 * lands, then show it. Keeps the progress screen working without a backend
 * restart and also survives a browser reload mid-analysis.
 */
export function useTrackSummary() {
  const qc = useQueryClient();
  const addProcessingTicker = useDashboardStore((s) => s.addProcessingTicker);
  const removeProcessingTicker = useDashboardStore((s) => s.removeProcessingTicker);
  const addNotification = useDashboardStore((s) => s.addNotification);

  return (symbol: string) => {
    addProcessingTicker(symbol);
    const poll = setInterval(async () => {
      try {
        const res = await api.getSummary(symbol, 1);
        if (res.latest_summary) {
          clearInterval(poll);
          removeProcessingTicker(symbol);
          qc.invalidateQueries({ queryKey: SUMMARY_PREFIX(symbol) });
          addNotification(`${symbol} analysis ready`, "success");
        }
      } catch {
        // transient poll error — keep trying until the timeout below
      }
    }, 3000);
    setTimeout(() => {
      clearInterval(poll);
      removeProcessingTicker(symbol);
    }, 120000);
  };
}

/**
 * Returns a callback that refreshes a ticker: fires the analysis job, marks the
 * ticker as "processing", then polls until it finishes.
 */
export function useRefreshTicker() {
  const trackJob = useTrackJob();
  const addProcessingTicker = useDashboardStore((s) => s.addProcessingTicker);
  const removeProcessingTicker = useDashboardStore((s) => s.removeProcessingTicker);
  const addNotification = useDashboardStore((s) => s.addNotification);

  return async (symbol: string) => {
    addProcessingTicker(symbol);
    addNotification(`Refreshing ${symbol}...`, "info");
    try {
      const res = await api.refreshTicker(symbol);
      trackJob(symbol, res.job_id);
    } catch {
      removeProcessingTicker(symbol);
      addNotification(`${symbol} refresh failed to start`, "error");
    }
  };
}

/**
 * Adds a ticker to the watchlist AND immediately tracks its first analysis:
 * selects the ticker, routes to the dashboard, marks it processing, and polls
 * the job the backend started — so the user sees a live progress screen and the
 * result appears automatically. Returns the watchlist mutation's pending state
 * for the input spinner.
 */
export function useAddAndAnalyze() {
  const trackJob = useTrackJob();
  const trackSummary = useTrackSummary();
  const addTicker = useAddTicker();
  const router = useRouter();
  const setSelectedTicker = useDashboardStore((s) => s.setSelectedTicker);
  const addProcessingTicker = useDashboardStore((s) => s.addProcessingTicker);
  const removeProcessingTicker = useDashboardStore((s) => s.removeProcessingTicker);
  const addNotification = useDashboardStore((s) => s.addNotification);

  const add = async (symbol: string) => {
    // Guard against a double-submit (e.g. a fast double Enter) racing into a
    // spurious "already exists".
    if (useDashboardStore.getState().processingTickers.has(symbol)) return;

    // Optimistically jump to the ticker and show the progress screen with no flash.
    addProcessingTicker(symbol);
    setSelectedTicker(symbol);
    router.push("/dashboard");

    let res;
    try {
      res = await addTicker.mutateAsync(symbol);
    } catch {
      removeProcessingTicker(symbol);
      addNotification(`Could not add ${symbol}`, "error");
      return;
    }

    // Only an actual HTTP error (e.g. 400) means duplicate / bad symbol.
    if (!res.ok) {
      removeProcessingTicker(symbol);
      const dup = /already|exist/i.test(res.detail ?? "");
      addNotification(
        dup ? `${symbol} is already in your watchlist` : res.detail || `Could not add ${symbol}`,
        dup ? "warning" : "error",
      );
      return;
    }

    // Added OK — track the analysis the backend started so it shows automatically.
    // job_id = current backend; no job_id = older backend → poll the summary.
    if (res.job_id) {
      trackJob(symbol, res.job_id, `${symbol} analysis ready`);
    } else {
      trackSummary(symbol);
    }
    addNotification(`Analyzing ${symbol}...`, "info");
  };

  return { add, isPending: addTicker.isPending };
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
