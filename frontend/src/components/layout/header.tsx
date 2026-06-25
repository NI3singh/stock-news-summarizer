"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Bell, LogOut, RefreshCw, Search } from "lucide-react";
import { Logo } from "@/components/ui/logo";
import { useAuth } from "@/lib/auth-context";
import { useDashboardStore } from "@/stores/dashboard-store";
import { useRefreshAll } from "@/hooks/use-refresh";

export function Header() {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const setSelectedTicker = useDashboardStore((s) => s.setSelectedTicker);
  const refreshAll = useRefreshAll();
  const [query, setQuery] = useState("");

  const handleSignOut = async () => {
    await signOut();
    router.push("/login");
  };

  const initial = (user?.displayName || user?.email || "U").trim().charAt(0).toUpperCase();

  const handleSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    const symbol = query.trim().toUpperCase();
    if (/^[A-Z]{2,5}$/.test(symbol)) {
      setSelectedTicker(symbol);
      setQuery("");
      router.push("/dashboard");
    }
  };

  return (
    <header className="sticky top-0 z-20 flex h-14 flex-shrink-0 items-center gap-4 border-b border-qm-border bg-qm-card px-4">
      <Logo size="sm" />

      <div className="relative mx-auto w-full max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-qm-text3" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleSearch}
          placeholder="Search ticker or company..."
          className="w-full rounded-lg border border-qm-border bg-qm-bg py-2 pl-9 pr-3 text-sm text-qm-text placeholder:text-qm-text3 focus:border-qm-green focus:outline-none focus:ring-1 focus:ring-qm-green"
        />
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => refreshAll()}
          className="hidden items-center gap-1.5 rounded-lg border border-qm-green bg-qm-green-bg px-3 py-1.5 text-sm font-medium text-qm-green transition-colors hover:bg-qm-green/15 sm:flex"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh All
        </button>
        <button
          className="text-qm-text3 transition-colors hover:text-qm-text2"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
        </button>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-qm-green text-sm font-bold text-white">
          {initial}
        </div>
        <button
          onClick={handleSignOut}
          className="text-qm-text3 transition-colors hover:text-qm-red"
          title="Sign out"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
