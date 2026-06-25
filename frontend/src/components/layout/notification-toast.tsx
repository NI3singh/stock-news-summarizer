"use client";
import { useEffect } from "react";
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useDashboardStore } from "@/stores/dashboard-store";

const STYLES = {
  info: { icon: Info, cls: "border-blue-500/30 bg-blue-500/10 text-blue-300" },
  success: { icon: CheckCircle2, cls: "border-qm-green/30 bg-qm-green-bg text-qm-green" },
  error: { icon: XCircle, cls: "border-red-500/30 bg-red-500/10 text-red-300" },
  warning: { icon: AlertTriangle, cls: "border-amber-500/30 bg-amber-500/10 text-amber-300" },
} as const;

function Toast({
  id,
  message,
  type,
}: {
  id: string;
  message: string;
  type: keyof typeof STYLES;
}) {
  const removeNotification = useDashboardStore((s) => s.removeNotification);

  useEffect(() => {
    const t = setTimeout(() => removeNotification(id), 4000);
    return () => clearTimeout(t);
  }, [id, removeNotification]);

  const { icon: Icon, cls } = STYLES[type];

  return (
    <div
      className={cn(
        "flex animate-slide-up items-center gap-2 rounded-lg border px-3 py-2 text-sm shadow-lg backdrop-blur",
        cls,
      )}
    >
      <Icon className="h-4 w-4 flex-shrink-0" />
      <span className="flex-1">{message}</span>
      <button onClick={() => removeNotification(id)} className="opacity-60 hover:opacity-100">
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export function NotificationToast() {
  const notifications = useDashboardStore((s) => s.notifications);
  return (
    <div className="fixed right-4 top-4 z-50 flex w-72 flex-col gap-2">
      {notifications.map((n) => (
        <Toast key={n.id} id={n.id} message={n.message} type={n.type} />
      ))}
    </div>
  );
}
