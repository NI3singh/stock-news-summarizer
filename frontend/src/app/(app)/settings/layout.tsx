"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/settings/profile", label: "Profile" },
  { href: "/settings/keys", label: "API Keys" },
  { href: "/settings/schedule", label: "Schedule" },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname() ?? "";
  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="mb-4 text-2xl font-bold text-qm-text">Settings</h1>
      <div className="mb-6 flex gap-1 border-b border-qm-border">
        {TABS.map((t) => (
          <Link
            key={t.href}
            href={t.href}
            className={cn(
              "border-b-2 px-4 py-2 text-sm transition-colors",
              path === t.href
                ? "border-qm-green text-qm-green"
                : "border-transparent text-qm-text2 hover:text-qm-text",
            )}
          >
            {t.label}
          </Link>
        ))}
      </div>
      {children}
    </div>
  );
}
