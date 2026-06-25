import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useSystemStatus() {
  return useQuery({ queryKey: ["system-status"], queryFn: api.getSystemStatus });
}

export function useAgentRuns(limit = 8) {
  return useQuery({
    queryKey: ["agent-runs", limit],
    queryFn: () => api.getAgentRuns(limit),
    refetchInterval: 30_000, // live agent activity
    select: (d) => d.runs,
  });
}
