import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useMlStatus() {
  return useQuery({ queryKey: ["ml-status"], queryFn: api.getMlStatus });
}

export function useMlCorrelation(ticker: string | null, days: number) {
  return useQuery({
    queryKey: ["ml-correlation", ticker, days],
    queryFn: () => api.getMlCorrelation(ticker!, days),
    enabled: !!ticker,
    // Correlation triggers a yfinance download server-side — don't auto-refetch.
    refetchInterval: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useTrainModel() {
  return useMutation({ mutationFn: (ticker: string) => api.triggerMlTraining(ticker) });
}
