import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const ALERT_STATUS_KEY = ["alert-status"];
export const ALERT_RULES_KEY = ["alert-rules"];

export function useAlertStatus() {
  return useQuery({ queryKey: ALERT_STATUS_KEY, queryFn: api.getAlertStatus });
}

export function useAlertRules() {
  return useQuery({
    queryKey: ALERT_RULES_KEY,
    queryFn: api.getAlertRules,
    select: (d) => d.rules,
  });
}

export function useCreateAlertRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createAlertRule,
    onSuccess: () => qc.invalidateQueries({ queryKey: ALERT_RULES_KEY }),
  });
}

export function useDeleteAlertRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteAlertRule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ALERT_RULES_KEY }),
  });
}

export function useToggleAlertRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      api.updateAlertRule(id, is_active),
    onSuccess: () => qc.invalidateQueries({ queryKey: ALERT_RULES_KEY }),
  });
}

export const ALERT_EVENTS_KEY = ["alert-events"];

export function useAlertEvents() {
  return useQuery({
    queryKey: ALERT_EVENTS_KEY,
    queryFn: api.getAlertEvents,
    select: (d) => d.events,
  });
}
