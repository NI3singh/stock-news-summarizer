"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Copy, Loader2, Send } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { useAlertStatus } from "@/hooks/use-alerts";
import { useDashboardStore } from "@/stores/dashboard-store";
import { Button } from "@/components/ui/button";

const STEPS = ["Open Bot", "Send Command", "Verify"];

function StepIndicator({ step }: { step: number }) {
  return (
    <div className="mb-8 flex items-center justify-center">
      {STEPS.map((label, i) => {
        const n = i + 1;
        const done = step > n;
        const active = step === n;
        return (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-full border-2 text-sm font-bold",
                  done
                    ? "border-qm-green bg-qm-green text-white"
                    : active
                      ? "border-qm-green text-qm-green"
                      : "border-qm-border text-qm-text3",
                )}
              >
                {done ? <Check className="h-4 w-4" /> : n}
              </div>
              <span
                className={cn(
                  "mt-1.5 text-[10px]",
                  active || done ? "text-qm-text2" : "text-qm-text3",
                )}
              >
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={cn("mx-2 h-0.5 w-12", step > n ? "bg-qm-green" : "bg-qm-border")} />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function TelegramSetupPage() {
  const router = useRouter();
  const { data: status } = useAlertStatus();
  const addNotification = useDashboardStore((s) => s.addNotification);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [token, setToken] = useState("");
  const [copied, setCopied] = useState(false);
  const [connected, setConnected] = useState(false);
  const [timedOut, setTimedOut] = useState(false);

  const botUsername = status?.bot_username || "StockStalkerBot";
  const command = `/start ${token}`;

  // Generate the display token client-side to avoid an SSR hydration mismatch.
  useEffect(() => {
    setToken(crypto.randomUUID().slice(0, 8).toUpperCase());
  }, []);

  // If the backend already reports connected, jump straight to success.
  useEffect(() => {
    if (status?.connected) setConnected(true);
  }, [status?.connected]);

  // Poll every 3s while on step 3; give up after 30s.
  useEffect(() => {
    if (step !== 3 || connected) return;
    setTimedOut(false);
    let elapsed = 0;
    const poll = setInterval(async () => {
      elapsed += 3;
      try {
        const s = await api.getAlertStatus();
        if (s.connected) {
          clearInterval(poll);
          setConnected(true);
          return;
        }
      } catch {
        /* transient — keep polling */
      }
      if (elapsed >= 30) {
        clearInterval(poll);
        setTimedOut(true);
      }
    }, 3000);
    return () => clearInterval(poll);
  }, [step, connected]);

  // Auto-redirect to /alerts shortly after a successful connection.
  useEffect(() => {
    if (!connected) return;
    const t = setTimeout(() => router.push("/alerts"), 2000);
    return () => clearTimeout(t);
  }, [connected, router]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  const sendTest = async () => {
    const res = await api.sendTestNotification();
    addNotification(res.message, res.success ? "success" : "error");
  };

  const checkNow = async () => {
    const s = await api.getAlertStatus();
    if (s.connected) setConnected(true);
  };

  return (
    <div className="mx-auto max-w-md p-6">
      <h1 className="mb-6 text-center text-2xl font-bold text-qm-text">Connect Telegram</h1>
      <StepIndicator step={connected ? 4 : step} />

      <div className="rounded-2xl border border-qm-border bg-qm-card p-6">
        {/* Step 1 */}
        {step === 1 && !connected && (
          <div className="space-y-4 text-center">
            <h2 className="text-lg font-semibold text-qm-text">Step 1 — Open your StockStalker bot</h2>
            <p className="text-sm text-qm-text3">First, open the StockStalker bot in Telegram.</p>
            <a
              href={`https://t.me/${botUsername}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-qm-green px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-qm-green-dim"
            >
              Open @{botUsername} in Telegram →
            </a>
            <p className="text-xs text-qm-text3">
              Or search for <span className="font-mono text-qm-text2">@{botUsername}</span> in your
              Telegram app.
            </p>
            <Button className="w-full" onClick={() => setStep(2)}>
              Next: I&apos;ve opened it →
            </Button>
          </div>
        )}

        {/* Step 2 */}
        {step === 2 && !connected && (
          <div className="space-y-4">
            <h2 className="text-center text-lg font-semibold text-qm-text">
              Step 2 — Send the start command
            </h2>
            <p className="text-center text-sm text-qm-text3">
              In the bot chat, send this exact command:
            </p>
            <div className="flex items-center gap-2 rounded-lg border border-qm-border bg-qm-bg p-3">
              <code className="flex-1 break-all font-mono text-sm text-qm-green">{command}</code>
              <button onClick={copy} className="text-qm-text3 hover:text-qm-text2" title="Copy">
                {copied ? <Check className="h-4 w-4 text-qm-green" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" className="flex-1" onClick={() => setStep(1)}>
                ← Back
              </Button>
              <Button className="flex-1" onClick={() => setStep(3)}>
                I&apos;ve sent it →
              </Button>
            </div>
          </div>
        )}

        {/* Step 3 */}
        {(step === 3 || connected) && (
          <div className="space-y-4 text-center">
            <h2 className="text-lg font-semibold text-qm-text">Step 3 — Verify connection</h2>
            {connected ? (
              <div className="space-y-3">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-qm-green-bg">
                  <Check className="h-7 w-7 text-qm-green" />
                </div>
                <p className="font-semibold text-qm-green">Successfully connected!</p>
                {status?.chat_id && (
                  <p className="text-xs text-qm-text3">Chat ID: {status.chat_id}</p>
                )}
                <Button variant="outline" onClick={sendTest}>
                  <Send className="h-3.5 w-3.5" /> Send Test Notification
                </Button>
                <p className="text-xs text-qm-text3">Redirecting to Alerts…</p>
              </div>
            ) : timedOut ? (
              <div className="space-y-3">
                <p className="text-sm text-qm-text2">
                  Connection not detected. Make sure you sent the command to the correct bot.
                </p>
                <Button
                  onClick={() => {
                    setTimedOut(false);
                    setStep(1);
                  }}
                >
                  Try Again
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <Loader2 className="mx-auto h-8 w-8 animate-spin text-qm-green" />
                <p className="text-sm text-qm-text3">Waiting for your message to the bot…</p>
                <Button variant="secondary" size="sm" onClick={checkNow}>
                  Check Connection
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      <p className="mt-4 text-center text-xs text-qm-text3">
        Note: the bot must be running (<span className="font-mono">stockstalker run-scheduler</span>) to
        receive your message.
      </p>
    </div>
  );
}
