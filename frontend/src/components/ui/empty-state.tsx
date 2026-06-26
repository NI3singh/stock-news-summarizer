import type { ReactNode } from "react";

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-qm-green-bg to-qm-card text-4xl shadow-[0_0_40px_rgba(34,197,94,0.18)] ring-1 ring-qm-green/20">
        {icon}
      </div>
      <h2 className="mt-5 text-xl font-bold text-qm-text">{title}</h2>
      <p className="mt-1 max-w-md text-sm text-qm-text3">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
