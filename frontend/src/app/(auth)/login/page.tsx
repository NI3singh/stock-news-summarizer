"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, TrendingUp, Cpu, Bell } from "lucide-react";
import { Logo }            from "@/components/ui/logo";
import { Button }          from "@/components/ui/button";
import { Input }           from "@/components/ui/input";
import { GoogleButton }    from "@/components/ui/google-button";
import { OrDivider }       from "@/components/ui/divider";
import { MarketPreviewCard }  from "@/components/auth/market-preview-card";
import { MarketIndicesBar }   from "@/components/auth/market-indices-bar";
import { useAuth }            from "@/lib/auth-context";

const FEATURES = [
  { icon: <Cpu  className="h-4 w-4" />, color: "bg-qm-green-bg text-qm-green border-qm-green/30", text: "AI-powered news analysis" },
  { icon: <Bell className="h-4 w-4" />, color: "bg-red-500/10 text-red-400 border-red-500/20",   text: "Real-time market alerts" },
  { icon: <TrendingUp className="h-4 w-4" />, color: "bg-qm-green-bg text-qm-green border-qm-green/30", text: "Smart portfolio tracking" },
];

export default function LoginPage() {
  const router = useRouter();
  const { signInEmail, signInGoogle } = useAuth();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signInEmail(email, password);
      router.push("/dashboard");
    } catch {
      setError("Invalid email or password.");
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setError("");
    setLoading(true);
    try {
      await signInGoogle();
      router.push("/dashboard");
    } catch {
      setError("Google sign-in failed. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">

      {/* ─── LEFT: Marketing Panel ─── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-10 xl:p-14">
        <Logo size="md" />

        <div className="space-y-6 animate-fade-in">
          <div>
            <h1 className="text-4xl xl:text-5xl font-extrabold text-qm-text leading-tight">
              Smart Market<br />Intelligence
            </h1>
            <p className="text-2xl xl:text-3xl font-bold text-qm-green mt-1">
              Powered by AI
            </p>
          </div>

          <p className="text-qm-text2 text-base leading-relaxed max-w-md">
            Get real-time AI-powered analysis of stock market news.
            Make informed decisions with intelligent insights and sentiment analysis.
          </p>

          <div className="space-y-3">
            {FEATURES.map((f, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className={`flex items-center justify-center h-8 w-8 rounded-lg border ${f.color} flex-shrink-0`}>
                  {f.icon}
                </div>
                <span className="text-qm-text text-sm font-medium">{f.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Mini stock preview card */}
        <div className="max-w-sm animate-fade-in">
          <MarketPreviewCard />
        </div>
      </div>

      {/* ─── RIGHT: Login Form ─── */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 lg:p-10">

        {/* Mobile logo */}
        <div className="lg:hidden mb-8">
          <Logo size="md" />
        </div>

        <div className="w-full max-w-md">
          <div className="rounded-2xl border border-qm-border bg-qm-card p-8 shadow-2xl animate-fade-in">

            <div className="mb-6">
              <h2 className="text-2xl font-bold text-qm-text">Welcome back</h2>
              <p className="text-qm-text3 text-sm mt-1">Sign in to access your dashboard</p>
            </div>

            <GoogleButton onClick={handleGoogle}>
              Continue with Google
            </GoogleButton>

            <OrDivider />

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                leftIcon={<Mail className="h-4 w-4" />}
                required
              />

              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                leftIcon={<Lock className="h-4 w-4" />}
                required
              />

              {error && (
                <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                  {error}
                </p>
              )}

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={e => setRemember(e.target.checked)}
                    className="h-4 w-4 rounded border-qm-border bg-qm-bg accent-qm-green"
                  />
                  <span className="text-sm text-qm-text2">Remember me</span>
                </label>
                <Link href="/forgot-password" className="text-sm text-qm-green hover:text-qm-green-dim transition-colors">
                  Forgot password?
                </Link>
              </div>

              <Button type="submit" size="lg" loading={loading} className="w-full mt-2">
                Sign In →
              </Button>
            </form>

            <p className="text-center text-sm text-qm-text3 mt-5">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="text-qm-green hover:text-qm-green-dim font-medium transition-colors">
                Sign up free
              </Link>
            </p>

            <MarketIndicesBar />
          </div>
        </div>
      </div>

    </div>
  );
}
