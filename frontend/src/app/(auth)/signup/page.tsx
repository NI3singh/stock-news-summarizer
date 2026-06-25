"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Mail, Lock, Eye, EyeOff, User, ArrowRight, AlertCircle, Check, Target, Zap, Cpu } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import GoogleIcon from "@/components/icons/google-icon";
import LogoMark from "@/components/icons/logo-mark";

export default function SignupPage() {
  const router = useRouter();
  const { signUpEmail, signInGoogle } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [error, setError] = useState("");

  const getPasswordStrength = (pass: string) => {
    let strength = 0;
    if (pass.length >= 8) strength++;
    if (/[A-Z]/.test(pass)) strength++;
    if (/[0-9]/.test(pass)) strength++;
    if (/[^A-Za-z0-9]/.test(pass)) strength++;
    return strength;
  };

  const passwordStrength = getPasswordStrength(password);
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;

  const handleEmailSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirmPassword) { setError("Passwords do not match."); return; }
    if (!agreeToTerms) { setError("You must agree to the terms."); return; }
    setIsLoading(true);
    try {
      await signUpEmail(displayName, email, password);
      router.push("/dashboard");
    } catch {
      setError("Account creation failed. Please try again.");
      setIsLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    setError("");
    setIsLoading(true);
    try {
      await signInGoogle();
      router.push("/dashboard");
    } catch {
      setError("Google sign-up failed. Please try again.");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* ─── LEFT: Signup Form ─── */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12 relative z-10">
        <motion.div className="w-full max-w-md" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}>
          <motion.div className="glass-card rounded-2xl p-8 shadow-card card-border-gradient" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            {/* Logo */}
            <div className="flex items-center justify-center gap-2 mb-8">
              <LogoMark className="w-9 h-9" />
              <span className="text-xl font-bold text-white">
                Stock<span className="text-market-green-400">Stalker</span>{" "}
                <span className="text-market-green-400 text-sm gradient-text">AI</span>
              </span>
            </div>

            <motion.h2 className="text-2xl font-bold text-white mb-2 text-center" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
              Create your account
            </motion.h2>
            <motion.p className="text-market-dark-400 mb-8 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
              Join thousands of smart investors
            </motion.p>

            {error && (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-6 p-4 rounded-lg bg-market-red-500/10 border border-market-red-500/30 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-market-red-400 flex-shrink-0" />
                <p className="text-market-red-400 text-sm">{error}</p>
              </motion.div>
            )}

            <motion.button
              onClick={handleGoogleSignup}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 py-3.5 px-4 rounded-xl border border-market-dark-600 bg-market-dark-800/50 text-white font-medium hover:bg-market-dark-700 hover:border-market-dark-500 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed mb-6 hover-lift"
              whileTap={{ scale: 0.98 }}
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
            >
              <GoogleIcon className="w-5 h-5" />
              Sign up with Google
            </motion.button>

            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-market-dark-600" /></div>
              <div className="relative flex justify-center text-sm"><span className="px-4 bg-market-dark-800 text-market-dark-400">or sign up with email</span></div>
            </div>

            <form onSubmit={handleEmailSignup} className="space-y-4" autoComplete="off">
              <div>
                <label className="block text-sm font-medium text-market-dark-300 mb-2">Full Name</label>
                <div className="relative group">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-market-dark-500 group-focus-within:text-market-green-400 transition-colors" />
                  <input type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Enter your name" autoComplete="off" className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-market-dark-900/50 border border-market-dark-600 text-white placeholder-market-dark-500 input-market transition-all duration-300 focus:border-market-green-500/50" required />
                </div>
              </div>

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
                  <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Create a password" autoComplete="new-password" className="w-full pl-12 pr-12 py-3.5 rounded-xl bg-market-dark-900/50 border border-market-dark-600 text-white placeholder-market-dark-500 input-market transition-all duration-300 focus:border-market-green-500/50" required minLength={6} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-market-dark-500 hover:text-market-dark-300 transition-colors">
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {password.length > 0 && (
                  <motion.div className="mt-2" initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }}>
                    <div className="flex gap-1 mb-1">
                      {[1, 2, 3, 4].map((level) => (
                        <div key={level} className={`h-1 flex-1 rounded-full transition-colors ${
                          passwordStrength >= level
                            ? passwordStrength <= 1 ? "bg-market-red-500" : passwordStrength === 2 ? "bg-yellow-500" : "bg-market-green-500"
                            : "bg-market-dark-700"
                        }`} />
                      ))}
                    </div>
                    <p className={`text-xs ${passwordStrength <= 1 ? "text-market-red-400" : passwordStrength === 2 ? "text-yellow-400" : "text-market-green-400"}`}>
                      {passwordStrength <= 1 ? "Weak" : passwordStrength === 2 ? "Fair" : passwordStrength === 3 ? "Good" : "Strong"}
                    </p>
                  </motion.div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-market-dark-300 mb-2">Confirm Password</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-market-dark-500 group-focus-within:text-market-green-400 transition-colors" />
                  <input type={showConfirmPassword ? "text" : "password"} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Confirm your password" autoComplete="new-password"
                    className={`w-full pl-12 pr-12 py-3.5 rounded-xl bg-market-dark-900/50 border text-white placeholder-market-dark-500 input-market transition-all duration-300 ${
                      confirmPassword.length > 0 ? (passwordsMatch ? "border-market-green-500" : "border-market-red-500") : "border-market-dark-600 focus:border-market-green-500/50"
                    }`} required />
                  <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-market-dark-500 hover:text-market-dark-300 transition-colors">
                    {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                  {confirmPassword.length > 0 && passwordsMatch && (
                    <Check className="absolute right-12 top-1/2 -translate-y-1/2 w-5 h-5 text-market-green-400" />
                  )}
                </div>
                {confirmPassword.length > 0 && !passwordsMatch && (
                  <p className="text-market-red-400 text-xs mt-1">Passwords don&apos;t match</p>
                )}
              </div>

              <label className="flex items-start gap-3 cursor-pointer mt-4">
                <input type="checkbox" checked={agreeToTerms} onChange={(e) => setAgreeToTerms(e.target.checked)} className="w-5 h-5 mt-0.5 rounded border-market-dark-600 bg-market-dark-900 accent-market-green-500 cursor-pointer" required />
                <span className="text-sm text-market-dark-400">
                  I agree to the{" "}
                  <Link href="#" className="text-market-green-400 hover:text-market-green-300 transition-colors hover:underline">Terms of Service</Link>
                  {" "}and{" "}
                  <Link href="#" className="text-market-green-400 hover:text-market-green-300 transition-colors hover:underline">Privacy Policy</Link>
                </span>
              </label>

              <button type="submit" disabled={isLoading || !passwordsMatch || !agreeToTerms} className="w-full py-3.5 px-4 rounded-xl btn-market-green text-white font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-6">
                {isLoading ? "Creating account..." : (<>Create Account <ArrowRight className="w-5 h-5" /></>)}
              </button>
            </form>

            <p className="mt-8 text-center text-market-dark-400">
              Already have an account?{" "}
              <Link href="/login" className="text-market-green-400 hover:text-market-green-300 font-medium transition-colors hover:underline">Sign in</Link>
            </p>
          </motion.div>
        </motion.div>
      </div>

      {/* ─── RIGHT: Benefits ─── */}
      <div className="hidden lg:flex lg:w-1/2 relative items-center justify-center p-12">
        <div className="max-w-lg z-10">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <motion.h2 className="text-4xl font-bold text-white mb-6 leading-tight" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
              Start your journey to
              <br />
              <span className="gradient-text">smarter investing</span>
            </motion.h2>

            <motion.p className="text-market-dark-300 text-lg mb-10" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
              Get instant access to AI-powered market intelligence and never miss a market-moving news event again.
            </motion.p>

            <motion.div className="space-y-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
              <BenefitCard icon={<Cpu className="w-6 h-6" />} title="Real-Time Analysis" description="Get instant AI-powered analysis of breaking market news" color="green" />
              <BenefitCard icon={<Zap className="w-6 h-6" />} title="Sentiment Tracking" description="Understand market sentiment with advanced AI algorithms" color="red" />
              <BenefitCard icon={<Target className="w-6 h-6" />} title="Custom Watchlists" description="Track your favorite stocks and get personalized alerts" color="green" />
            </motion.div>

            <motion.div className="mt-12 grid grid-cols-3 gap-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.6 }}>
              <StatCard value="4" label="AI Agents" />
              <StatCard value="3+" label="News Sources" />
              <StatCard value="Gemini" label="AI Engine" />
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function BenefitCard({ icon, title, description, color }: { icon: React.ReactNode; title: string; description: string; color: "green" | "red" }) {
  return (
    <motion.div className="flex items-start gap-4 glass-card rounded-xl p-4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} whileHover={{ x: 5 }}>
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${color === "green" ? "bg-market-green-500/20 text-market-green-400" : "bg-market-red-500/20 text-market-red-400"}`}>
        {icon}
      </div>
      <div>
        <h3 className="text-white font-semibold mb-1">{title}</h3>
        <p className="text-market-dark-400 text-sm">{description}</p>
      </div>
    </motion.div>
  );
}

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <p className="text-2xl font-bold text-market-green-400 mb-1">{value}</p>
      <p className="text-market-dark-400 text-sm">{label}</p>
    </div>
  );
}
