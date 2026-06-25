"use client";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function DashboardStub() {
  const { user, signOut, usingDevFallback } = useAuth();
  const router = useRouter();

  const handleSignOut = async () => {
    await signOut();
    router.replace("/login");
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-8 text-center">
      <div>
        <h1 className="text-2xl font-bold text-qm-text mb-2">Dashboard</h1>
        <p className="text-qm-text3 mb-1">Auth is working! Build the full dashboard in Phase A.</p>
        <p className="text-qm-text3 text-sm mb-6">
          Signed in as{" "}
          <span className="text-qm-text font-medium">{user?.email ?? "—"}</span>
          {usingDevFallback && (
            <span className="block text-qm-amber text-xs mt-1">
              dev fallback active — add Firebase keys to .env.local for real auth
            </span>
          )}
        </p>
        <button onClick={handleSignOut} className="text-qm-green hover:underline text-sm">
          Sign out
        </button>
      </div>
    </div>
  );
}
