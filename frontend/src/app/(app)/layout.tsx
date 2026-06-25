"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  // While checking auth (or redirecting unauthenticated users) show a spinner
  if (loading || !user) {
    return (
      <div className="min-h-screen bg-qm-bg flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-qm-border border-t-qm-green animate-spin" />
      </div>
    );
  }

  return <div className="min-h-screen bg-qm-bg">{children}</div>;
}
