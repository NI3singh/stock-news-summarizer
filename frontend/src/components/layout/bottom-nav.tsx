"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Clock, LayoutDashboard, Link2, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const PRIMARY = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/history", icon: Clock, label: "History" },
  { href: "/alerts", icon: Bell, label: "Alerts" },
  { href: "/mcp", icon: Link2, label: "MCP" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

export function BottomNav() {
  const path = usePathname() ?? "";
  const isActive = (href: string) => path === href || path.startsWith(href + "/");

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 flex h-16 items-center justify-around border-t border-qm-border bg-qm-sidebar md:hidden">
      {PRIMARY.map((item) => {
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-0.5 text-[10px]",
              isActive(item.href) ? "text-qm-green" : "text-qm-text3",
            )}
          >
            <Icon className="h-5 w-5" /> {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
