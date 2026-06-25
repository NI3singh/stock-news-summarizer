import Link from "next/link";
import { Logo } from "@/components/ui/logo";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-qm-bg p-8 text-center">
      <Logo size="lg" className="mb-8" />
      <div className="text-6xl font-extrabold text-qm-green">404</div>
      <p className="mt-2 text-qm-text2">This page does not exist.</p>
      <Link
        href="/dashboard"
        className="mt-6 rounded-lg bg-qm-green px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-qm-green-dim"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
