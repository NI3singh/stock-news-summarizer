"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/signals", label: "Overview" },
  { href: "/signals/entity-graph", label: "Entity Graph" },
];

export function SignalsTabs() {
  const path = usePathname() ?? "";
  return (
    <div className="flex gap-1 rounded-lg border border-qm-border bg-qm-card p-1">
      {TABS.map((t) => (
        <Link
          key={t.href}
          href={t.href}
          className={cn(
            "rounded-md px-3 py-1 text-sm transition-colors",
            path === t.href
              ? "bg-qm-green-bg text-qm-green"
              : "text-qm-text2 hover:text-qm-text",
          )}
        >
          {t.label}
        </Link>
      ))}
    </div>
  );
}
