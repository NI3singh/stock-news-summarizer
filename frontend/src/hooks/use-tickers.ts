import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const TICKERS_KEY = ["tickers"];
export const SUMMARY_KEY = (symbol: string) => ["summary", symbol];

export function useTickers() {
  return useQuery({
    queryKey: TICKERS_KEY,
    queryFn: api.getTickers,
    select: (d) => d.tickers,
  });
}

export function useSummary(symbol: string | null) {
  return useQuery({
    queryKey: SUMMARY_KEY(symbol ?? ""),
    queryFn: () => api.getSummary(symbol!),
    enabled: !!symbol,
  });
}

export function useAddTicker() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => api.addTicker(symbol),
    onSuccess: () => qc.invalidateQueries({ queryKey: TICKERS_KEY }),
  });
}

export function useRemoveTicker() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => api.removeTicker(symbol),
    onSuccess: () => qc.invalidateQueries({ queryKey: TICKERS_KEY }),
  });
}
