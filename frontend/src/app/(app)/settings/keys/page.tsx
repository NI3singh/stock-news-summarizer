"use client";
import { useState } from "react";
import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
type TestState = "idle" | "testing" | "ok" | "error";

function KeyCard({ title, link }: { title: string; link: string }) {
  const [test, setTest] = useState<TestState>("idle");

  const runTest = async () => {
    setTest("testing");
    try {
      const res = await fetch(`${BASE}/health`);
      setTest(res.ok ? "ok" : "error");
    } catch {
      setTest("error");
    }
  };

  return (
    <div className="rounded-xl border border-qm-border bg-qm-card p-4">
      <h3 className="text-sm font-semibold text-qm-text">{title}</h3>
      <div className="mt-2 flex items-center gap-2">
        <input
          disabled
          value="•••• •••• configured in backend .env"
          className="flex-1 rounded-lg border border-qm-border bg-qm-bg px-3 py-2 text-sm text-qm-text3"
        />
        <Button size="sm" variant="secondary" onClick={runTest} loading={test === "testing"}>
          Test
        </Button>
      </div>
      <div className="mt-2 flex items-center justify-between text-xs">
        <a
          href={link}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-qm-green hover:underline"
        >
          Get a key <ExternalLink className="h-3 w-3" />
        </a>
        {test === "ok" && <span className="text-qm-green">✓ Backend reachable</span>}
        {test === "error" && <span className="text-qm-red">✗ Backend unreachable</span>}
      </div>
    </div>
  );
}

export default function KeysPage() {
  return (
    <div className="space-y-4">
      <p className="rounded-lg border border-qm-border bg-qm-card2 p-3 text-xs text-qm-text3">
        API keys are stored server-side in the backend <code className="text-qm-text2">.env</code> and
        are never sent to the browser. Edit them there and restart the API server. (The Test button
        checks that the backend API is reachable.)
      </p>
      <KeyCard title="Gemini API Key" link="https://ai.google.dev" />
      <KeyCard title="Polygon API Key" link="https://polygon.io" />
    </div>
  );
}
