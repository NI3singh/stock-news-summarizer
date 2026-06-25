"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { NotificationToast } from "@/components/layout/notification-toast";
import { BottomNav } from "@/components/layout/bottom-nav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  // Route guard — redirect unauthenticated users to /login.
  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-qm-bg">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-qm-border border-t-qm-green" />
      </div>
    );
  }

  // Authenticated app shell: sidebar + header + scrollable main.
  return (
    <div className="flex h-screen overflow-hidden bg-qm-bg">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto pb-16 md:pb-0">{children}</main>
      </div>
      <NotificationToast />
      <BottomNav />
    </div>
  );
}
