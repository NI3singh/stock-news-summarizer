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
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-qm-card text-3xl text-qm-text2">
        {icon}
      </div>
      <h2 className="mt-4 text-xl font-bold text-qm-text">{title}</h2>
      <p className="mt-1 max-w-md text-sm text-qm-text3">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
