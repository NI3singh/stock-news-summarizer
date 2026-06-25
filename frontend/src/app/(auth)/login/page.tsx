"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Mail, Lock, Eye, EyeOff, ArrowRight, AlertCircle, Target, Zap, Cpu } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import StockChart from "@/components/stock-chart";
import GoogleIcon from "@/components/icons/google-icon";
import LogoMark from "@/components/icons/logo-mark";

export default function LoginPage() {
  const router = useRouter();
  const { signInEmail, signInGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await signInEmail(email, password);
      router.push("/dashboard");
    } catch {
      setError("Invalid email or password.");
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError("");
    setIsLoading(true);
    try {
      await signInGoogle();
      router.push("/dashboard");
    } catch {
      setError("Google sign-in failed. Please try again.");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* ─── LEFT: Branding ─── */}
      <div className="hidden lg:flex lg:w-1/2 relative items-center justify-center p-12">
        <div className="max-w-lg z-10">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <motion.div className="flex items-center gap-3 mb-8" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
              <LogoMark className="w-12 h-12" />
              <div>
                <h1 className="text-3xl font-bold text-white leading-none">StockStalker</h1>
                <span className="text-market-green-400 font-semibold gradient-text">AI</span>
              </div>
            </motion.div>

            <motion.h2 className="text-4xl font-bold text-white mb-4 leading-tight" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
              Smart Market Intelligence
              <br />
              <span className="gradient-text">Powered by AI</span>
            </motion.h2>

            <motion.p className="text-market-dark-300 text-lg mb-8" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
              Get real-time AI-powered analysis of stock market news. Make informed decisions with intelligent insights and sentiment analysis.
            </motion.p>

            <motion.div className="space-y-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
              <FeatureItem icon={<Cpu className="w-5 h-5" />} text="AI-powered news analysis" color="green" />
              <FeatureItem icon={<Zap className="w-5 h-5" />} text="Real-time market alerts" color="red" />
              <FeatureItem icon={<Target className="w-5 h-5" />} text="Smart watchlist tracking" color="green" />
            </motion.div>
          </motion.div>

          <motion.div className="mt-12" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.6 }}>
            <StockChart />
          </motion.div>
        </div>
      </div>

      {/* ─── RIGHT: Form ─── */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12 relative z-10">
        <motion.div className="w-full max-w-md" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}>
          <motion.div className="glass-card rounded-2xl p-8 shadow-card card-border-gradient" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            {/* Mobile logo */}
            <div className="lg:hidden flex items-center justify-center gap-2 mb-8">
              <LogoMark className="w-9 h-9" />
              <span className="text-xl font-bold text-white">
                Stock<span className="text-market-green-400">Stalker</span>{" "}
                <span className="text-market-green-400 text-sm gradient-text">AI</span>
              </span>
            </div>

            <motion.h2 className="text-2xl font-bold text-white mb-2 text-center lg:text-left" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
              Welcome back
            </motion.h2>
            <motion.p className="text-market-dark-400 mb-8 text-center lg:text-left" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
              Sign in to access your dashboard
            </motion.p>

            {error && (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6 p-4 rounded-lg bg-market-red-500/10 border border-market-red-500/30 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-market-red-400 flex-shrink-0" />
                <p className="text-market-red-400 text-sm">{error}</p>
              </motion.div>
            )}

            <motion.button
              onClick={handleGoogleLogin}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 py-3.5 px-4 rounded-xl border border-market-dark-600 bg-market-dark-800/50 text-white font-medium hover:bg-market-dark-700 hover:border-market-dark-500 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed mb-6 hover-lift"
              whileTap={{ scale: 0.98 }}
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
            >
              <GoogleIcon className="w-5 h-5" />
              Continue with Google
            </motion.button>

            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-market-dark-600" /></div>
              <div className="relative flex justify-center text-sm"><span className="px-4 bg-market-dark-800 text-market-dark-400">or continue with email</span></div>
            </div>

            <form onSubmit={handleEmailLogin} className="space-y-5" autoComplete="off">
              <div>
                <label className="block text-sm font-medium text-market-dark-300 mb-2">Email</label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-market-dark-500 group-focus-within:text-market-green-400 transition-colors" />
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Enter your email" autoComplete="off" className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-market-dark-900/50 border border-market-dark-600 text-white placeholder-market-dark-500 input-market transition-all duration-300 focus:border-market-green-500/50" required />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-market-dark-300 mb-2">Password</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-market-dark-500 group-focus-within:text-market-green-400 transition-colors" />
                  <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" autoComplete="new-password" className="w-full pl-12 pr-12 py-3.5 rounded-xl bg-market-dark-900/50 border border-market-dark-600 text-white placeholder-market-dark-500 input-market transition-all duration-300 focus:border-market-green-500/50" required />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-market-dark-500 hover:text-market-dark-300 transition-colors">
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded border-market-dark-600 bg-market-dark-900 accent-market-green-500 cursor-pointer" />
                  <span className="text-sm text-market-dark-400">Remember me</span>
                </label>
                <Link href="/forgot-password" className="text-sm text-market-green-400 hover:text-market-green-300 transition-colors hover:underline">Forgot password?</Link>
              </div>

              <button type="submit" disabled={isLoading} className="w-full py-3.5 px-4 rounded-xl btn-market-green text-white font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
                {isLoading ? "Signing in..." : (<>Sign In <ArrowRight className="w-5 h-5" /></>)}
              </button>
            </form>

            <p className="mt-8 text-center text-market-dark-400">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="text-market-green-400 hover:text-market-green-300 font-medium transition-colors hover:underline">Sign up free</Link>
            </p>
          </motion.div>

          {/* Market Stats Footer */}
          <motion.div className="mt-8 grid grid-cols-3 gap-4" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
            <MarketStat label="S&P 500" value="+1.24%" isPositive />
            <MarketStat label="NASDAQ" value="+0.87%" isPositive />
            <MarketStat label="DOW" value="-0.32%" isPositive={false} />
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

function FeatureItem({ icon, text, color }: { icon: React.ReactNode; text: string; color: "green" | "red" }) {
  return (
    <motion.div className="flex items-center gap-3" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} whileHover={{ x: 5 }}>
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color === "green" ? "bg-market-green-500/20 text-market-green-400" : "bg-market-red-500/20 text-market-red-400"}`}>
        {icon}
      </div>
      <span className="text-market-dark-200">{text}</span>
    </motion.div>
  );
}

function MarketStat({ label, value, isPositive }: { label: string; value: string; isPositive: boolean }) {
  return (
    <motion.div className="glass-card rounded-lg p-3 text-center hover-lift cursor-pointer" whileHover={{ scale: 1.05 }}>
      <p className="text-market-dark-400 text-xs mb-1">{label}</p>
      <p className={`font-semibold ${isPositive ? "text-market-green-400" : "text-market-red-400"}`}>{value}</p>
    </motion.div>
  );
}
