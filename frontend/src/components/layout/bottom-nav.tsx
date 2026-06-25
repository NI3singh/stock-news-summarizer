"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bell,
  Brain,
  Clock,
  Columns2,
  LayoutDashboard,
  Link2,
  MoreHorizontal,
  Settings,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

const PRIMARY = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/history", icon: Clock, label: "History" },
  { href: "/alerts", icon: Bell, label: "Alerts" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

const MORE = [
  { href: "/mcp", icon: Link2, label: "MCP Server" },
  { href: "/signals", icon: Brain, label: "ML Signals" },
  { href: "/backtest", icon: TrendingUp, label: "Backtest" },
  { href: "/system", icon: Activity, label: "System" },
  { href: "/compare", icon: Columns2, label: "Compare" },
];

export function BottomNav() {
  const path = usePathname() ?? "";
  const [moreOpen, setMoreOpen] = useState(false);
  const isActive = (href: string) => path === href || path.startsWith(href + "/");

  return (
    <>
      {moreOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 md:hidden" onClick={() => setMoreOpen(false)}>
          <div
            className="absolute bottom-16 left-0 right-0 m-2 rounded-xl border border-qm-border bg-qm-card p-2"
            onClick={(e) => e.stopPropagation()}
          >
            {MORE.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMoreOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm",
                    isActive(item.href) ? "bg-qm-green-bg text-qm-green" : "text-qm-text2",
                  )}
                >
                  <Icon className="h-4 w-4" /> {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}

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
        <button
          onClick={() => setMoreOpen(!moreOpen)}
          className={cn(
            "flex flex-col items-center gap-0.5 text-[10px]",
            moreOpen ? "text-qm-green" : "text-qm-text3",
          )}
        >
          <MoreHorizontal className="h-5 w-5" /> More
        </button>
      </nav>
    </>
  );
}
