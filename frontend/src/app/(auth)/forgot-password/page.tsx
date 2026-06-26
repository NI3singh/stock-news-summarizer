"use client";
import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Mail, ArrowLeft, AlertCircle } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import LogoMark from "@/components/icons/logo-mark";

export default function ForgotPasswordPage() {
  const { resetPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await resetPassword(email);
    } catch {
      // Always show success — don't reveal whether an email is registered
    }
    setIsLoading(false);
    setSent(true);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <motion.div className="w-full max-w-md relative z-10" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        {/* Logo */}
        <motion.div className="flex items-center justify-center gap-2 mb-8" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
          <LogoMark className="w-10 h-10" />
          <span className="text-2xl font-bold text-white">
            Stock<span className="text-market-green-400">Stalker</span>{" "}
            <span className="text-market-green-400 text-sm gradient-text">AI</span>
          </span>
        </motion.div>

        <motion.div className="glass-card rounded-2xl p-8 shadow-card card-border-gradient" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          {!sent ? (
            <>
              <h2 className="text-2xl font-bold text-white mb-2">Reset password</h2>
              <p className="text-market-dark-400 text-sm mb-8">Enter your email and we&apos;ll send you a reset link.</p>

              {error && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6 p-4 rounded-lg bg-market-red-500/10 border border-market-red-500/30 flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-market-red-400 flex-shrink-0" />
                  <p className="text-market-red-400 text-sm">{error}</p>
                </motion.div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5" autoComplete="off">
                <div>
                  <label className="block text-sm font-medium text-market-dark-300 mb-2">Email address</label>
                  <div className="relative group">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-market-dark-500 group-focus-within:text-market-green-400 transition-colors" />
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Enter your email" autoComplete="off" className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-market-dark-900/50 border border-market-dark-600 text-white placeholder-market-dark-500 input-market transition-all duration-300 focus:border-market-green-500/50" required />
                  </div>
                </div>

                <motion.button type="submit" disabled={isLoading} className="w-full py-3.5 px-4 rounded-xl btn-market-green text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover-lift" whileTap={{ scale: 0.98 }}>
                  {isLoading ? "Sending..." : "Send Reset Link"}
                </motion.button>
              </form>
            </>
          ) : (
            <motion.div className="text-center py-4" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
              <motion.div className="w-16 h-16 rounded-full bg-market-green-500/20 border border-market-green-500/30 flex items-center justify-center mx-auto mb-6" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
                <Mail className="w-8 h-8 text-market-green-400" />
              </motion.div>
              <h3 className="text-xl font-bold text-white mb-2">Check your email</h3>
              <p className="text-market-dark-400">
                We sent a reset link to <span className="text-white font-medium">{email}</span>. Check your inbox and follow the instructions.
              </p>
            </motion.div>
          )}

          <motion.div whileHover={{ x: -5 }} className="mt-6 inline-block">
            <Link href="/login" className="flex items-center gap-2 text-sm text-market-dark-400 hover:text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
              Back to sign in
            </Link>
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  );
}
