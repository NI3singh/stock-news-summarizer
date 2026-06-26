"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bell,
  ChevronLeft,
  ChevronRight,
  Clock,
  LayoutDashboard,
  Link2,
  Loader2,
  Plus,
  RefreshCw,
  Settings,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useAddTicker,
  useRemoveTicker,
  useSummary,
  useTickers,
} from "@/hooks/use-tickers";
import { useRefreshTicker } from "@/hooks/use-refresh";
import { useDashboardStore } from "@/stores/dashboard-store";

const NAV_ITEMS = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/history", icon: Clock, label: "History" },
  { href: "/alerts", icon: Bell, label: "Alerts", badge: "B", badgeClass: "bg-blue-500" },
  { href: "/mcp", icon: Link2, label: "MCP Server", badge: "C", badgeClass: "bg-purple-500" },
];

function sentimentDot(score: number | null | undefined): string {
  if (score == null) return "bg-qm-text3";
  if (score > 0.2) return "bg-qm-green";
  if (score < -0.2) return "bg-qm-red";
  return "bg-qm-text3";
}

function TickerRow({ symbol, collapsed }: { symbol: string; collapsed: boolean }) {
  const router = useRouter();
  const { data } = useSummary(symbol);
  const score = data?.latest_summary?.sentiment_score ?? null;
  const selectedTicker = useDashboardStore((s) => s.selectedTicker);
  const setSelectedTicker = useDashboardStore((s) => s.setSelectedTicker);
  const processing = useDashboardStore((s) => s.processingTickers.has(symbol));
  const refreshTicker = useRefreshTicker();
  const removeTicker = useRemoveTicker();
  const active = selectedTicker === symbol;

  const select = () => {
    setSelectedTicker(symbol);
    router.push("/dashboard");
  };

  if (collapsed) {
    return (
      <button
        onClick={select}
        title={symbol}
        className={cn(
          "flex w-full items-center justify-center rounded-md py-2",
          active && "bg-qm-green-bg",
        )}
      >
        <span className={cn("h-2 w-2 rounded-full", sentimentDot(score))} />
      </button>
    );
  }

  return (
    <div
      onClick={select}
      className={cn(
        "group flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm",
        active
          ? "border-l-2 border-qm-green bg-qm-green-bg"
          : "border-l-2 border-transparent hover:bg-qm-card",
      )}
    >
      <span className={cn("h-2 w-2 flex-shrink-0 rounded-full", sentimentDot(score))} />
      <span className="font-semibold text-qm-text">{symbol}</span>
      {processing ? (
        <span className="ml-auto animate-pulse rounded bg-amber-500/20 px-1.5 text-xs font-medium text-amber-400">
          …
        </span>
      ) : (
        <>
          <span
            className={cn(
              "ml-auto text-xs tabular-nums",
              score == null ? "text-qm-text3" : score >= 0 ? "text-qm-green" : "text-qm-red",
            )}
          >
            {score == null ? "—" : `${score >= 0 ? "+" : ""}${score.toFixed(2)}`}
          </span>
          <div className="hidden items-center gap-1 group-hover:flex">
            <button
              onClick={(e) => {
                e.stopPropagation();
                refreshTicker(symbol);
              }}
              className="text-qm-text3 hover:text-qm-green"
              title="Refresh"
            >
              <RefreshCw className="h-3 w-3" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                removeTicker.mutate(symbol);
              }}
              className="text-qm-text3 hover:text-qm-red"
              title="Remove"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export function Sidebar() {
  const path = usePathname() ?? "";
  const collapsed = useDashboardStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useDashboardStore((s) => s.toggleSidebar);
  const { data: tickers } = useTickers();
  const addTicker = useAddTicker();
  const [newTicker, setNewTicker] = useState("");

  const handleAdd = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    const symbol = newTicker.trim().toUpperCase();
    if (/^[A-Z]{1,10}$/.test(symbol)) {
      addTicker.mutate(symbol);
      setNewTicker("");
    }
  };

  const isActive = (href: string) => path === href || path.startsWith(href + "/");

  return (
    <aside
      className={cn(
        "hidden flex-col border-r border-qm-border bg-qm-sidebar transition-all duration-200 md:flex",
        collapsed ? "w-[60px]" : "w-[260px]",
      )}
    >
      {/* Watchlist + add */}
      <div className="flex-shrink-0 p-3">
        {!collapsed && (
          <div className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-qm-text3">
            Watchlist
          </div>
        )}
        {!collapsed ? (
          <div className="relative">
            <Plus className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-qm-text3" />
            <input
              value={newTicker}
              onChange={(e) => setNewTicker(e.target.value)}
              onKeyDown={handleAdd}
              placeholder="Add ticker..."
              className="w-full rounded-md border border-qm-border bg-qm-bg py-1.5 pl-8 pr-8 text-sm text-qm-text placeholder:text-qm-text3 focus:border-qm-green focus:outline-none"
            />
            {addTicker.isPending && (
              <Loader2 className="absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 animate-spin text-qm-green" />
            )}
          </div>
        ) : (
          <div className="flex justify-center">
            <Plus className="h-4 w-4 text-qm-text3" />
          </div>
        )}
      </div>

      {/* Ticker list */}
      <div className="flex-1 space-y-0.5 overflow-y-auto px-2">
        {(tickers ?? []).map((t) => (
          <TickerRow key={t} symbol={t} collapsed={collapsed} />
        ))}
      </div>

      {/* Navigation */}
      <nav className="flex-shrink-0 space-y-0.5 border-t border-qm-border p-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                "flex items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors",
                isActive(item.href)
                  ? "bg-qm-green-bg text-qm-green"
                  : "text-qm-text2 hover:bg-qm-card hover:text-qm-text",
                collapsed && "justify-center",
              )}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
              {!collapsed && item.badge && (
                <span
                  className={cn(
                    "ml-auto rounded px-1.5 text-[10px] font-bold text-white",
                    item.badgeClass,
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}

        <div className="my-1 h-px bg-qm-border" />

        <Link
          href="/settings"
          title={collapsed ? "Settings" : undefined}
          className={cn(
            "flex items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors",
            isActive("/settings")
              ? "bg-qm-green-bg text-qm-green"
              : "text-qm-text2 hover:bg-qm-card hover:text-qm-text",
            collapsed && "justify-center",
          )}
        >
          <Settings className="h-4 w-4 flex-shrink-0" />
          {!collapsed && <span>Settings</span>}
        </Link>
      </nav>

      {/* Collapse toggle */}
      <div className="flex-shrink-0 border-t border-qm-border p-2">
        <button
          onClick={toggleSidebar}
          className={cn(
            "flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-qm-text3 hover:bg-qm-card hover:text-qm-text",
            collapsed && "justify-center",
          )}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
