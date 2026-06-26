"use client";
import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-qm-bg p-8 text-center">
      <div className="text-5xl" aria-hidden>
        ⚠️
      </div>
      <h1 className="mt-4 text-2xl font-bold text-qm-text">Something went wrong</h1>
      <p className="mt-2 max-w-md text-sm text-qm-text3">
        {error.message || "An unexpected error occurred."}
      </p>
      <button
        onClick={reset}
        className="mt-6 rounded-lg bg-qm-green px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-qm-green-dim"
      >
        Try again
      </button>
    </div>
  );
}
