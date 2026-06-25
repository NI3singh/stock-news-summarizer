"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, Mail, Lock, TrendingUp, BarChart3, Bell } from "lucide-react";
import { Logo }          from "@/components/ui/logo";
import { Button }        from "@/components/ui/button";
import { Input }         from "@/components/ui/input";
import { GoogleButton }  from "@/components/ui/google-button";
import { OrDivider }     from "@/components/ui/divider";
import { useAuth }       from "@/lib/auth-context";

const RIGHT_FEATURES = [
  {
    icon: <BarChart3 className="h-5 w-5" />,
    color: "text-qm-green bg-qm-green-bg border-qm-green/20",
    title: "Real-Time Analysis",
    desc: "Get instant AI-powered analysis of breaking market news",
  },
  {
    icon: <TrendingUp className="h-5 w-5" />,
    color: "text-red-400 bg-red-500/10 border-red-500/20",
    title: "Sentiment Tracking",
    desc: "Understand market sentiment with advanced AI algorithms",
  },
  {
    icon: <Bell className="h-5 w-5" />,
    color: "text-qm-green bg-qm-green-bg border-qm-green/20",
    title: "Custom Watchlists",
    desc: "Track your favorite stocks and get personalized alerts",
  },
];

const STATS = [
  { value: "10K+", label: "Active Users" },
  { value: "500+", label: "Stocks Tracked" },
  { value: "24/7", label: "Market Coverage" },
];

function PasswordStrengthBar({ password }: { password: string }) {
  const strength = password.length === 0 ? 0
    : password.length < 6 ? 1
    : password.length < 10 ? 2
    : /[A-Z]/.test(password) && /[0-9]/.test(password) ? 4 : 3;

  const labels  = ["", "Weak", "Fair", "Good", "Strong"];
  const colors  = ["", "bg-red-500", "bg-amber-500", "bg-qm-green", "bg-qm-green"];
  const textClr = ["", "text-red-400", "text-amber-400", "text-qm-green", "text-qm-green"];

  if (!password) return null;

  return (
    <div className="mt-1.5">
      <div className="flex gap-1 mb-1">
        {[1, 2, 3, 4].map(i => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-all duration-300 ${i <= strength ? colors[strength] : "bg-qm-border"}`}
          />
        ))}
      </div>
      <p className={`text-xs font-medium ${textClr[strength]}`}>{labels[strength]}</p>
    </div>
  );
}

export default function SignupPage() {
  const router = useRouter();
  const { signUpEmail, signInGoogle } = useAuth();
  const [name, setName]           = useState("");
  const [email, setEmail]         = useState("");
  const [password, setPassword]   = useState("");
  const [confirm, setConfirm]     = useState("");
  const [agreed, setAgreed]       = useState(false);
  const [loading, setLoading]     = useState(false);
  const [errors, setErrors]       = useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!name.trim())         e.name = "Full name is required";
    if (!email.includes("@")) e.email = "Enter a valid email";
    if (password.length < 6)  e.password = "Password must be at least 6 characters";
    if (password !== confirm)  e.confirm = "Passwords do not match";
    if (!agreed)               e.terms = "You must agree to the terms";
    return e;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setLoading(true);
    try {
      await signUpEmail(name, email, password);
      router.push("/dashboard");
    } catch {
      setLoading(false);
      setErrors({ email: "Account creation failed. Please try again." });
    }
  };

  const handleGoogle = async () => {
    setLoading(true);
    try {
      await signInGoogle();
      router.push("/dashboard");
    } catch {
      setLoading(false);
      setErrors({ email: "Google sign-up failed. Please try again." });
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">

      {/* ─── LEFT: Signup Form ─── */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 lg:p-10 order-2 lg:order-1">
        <div className="w-full max-w-md">

          {/* Logo centered for signup card */}
          <div className="flex justify-center mb-6">
            <Logo size="md" />
          </div>

          <div className="rounded-2xl border border-qm-border bg-qm-card p-8 shadow-2xl animate-fade-in">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-qm-text">Create your account</h2>
              <p className="text-qm-text3 text-sm mt-1">Join thousands of smart investors</p>
            </div>

            <GoogleButton onClick={handleGoogle}>Sign up with Google</GoogleButton>
            <OrDivider text="or sign up with email" />

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Full Name"
                type="text"
                placeholder="Enter your name"
                value={name}
                onChange={e => setName(e.target.value)}
                leftIcon={<User className="h-4 w-4" />}
                error={errors.name}
              />

              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                leftIcon={<Mail className="h-4 w-4" />}
                error={errors.email}
              />

              <div>
                <Input
                  label="Password"
                  type="password"
                  placeholder="Create a strong password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  leftIcon={<Lock className="h-4 w-4" />}
                  error={errors.password}
                />
                <PasswordStrengthBar password={password} />
              </div>

              <Input
                label="Confirm Password"
                type="password"
                placeholder="Confirm your password"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                leftIcon={<Lock className="h-4 w-4" />}
                error={errors.confirm}
              />

              <div>
                <label className="flex items-start gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={agreed}
                    onChange={e => setAgreed(e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-qm-border bg-qm-bg accent-qm-green flex-shrink-0"
                  />
                  <span className="text-sm text-qm-text2">
                    I agree to the{" "}
                    <Link href="#" className="text-qm-green hover:underline">Terms of Service</Link>
                    {" "}and{" "}
                    <Link href="#" className="text-qm-green hover:underline">Privacy Policy</Link>
                  </span>
                </label>
                {errors.terms && <p className="text-xs text-red-400 mt-1">{errors.terms}</p>}
              </div>

              <Button type="submit" size="lg" loading={loading} className="w-full mt-2">
                Create Account →
              </Button>
            </form>

            <p className="text-center text-sm text-qm-text3 mt-5">
              Already have an account?{" "}
              <Link href="/login" className="text-qm-green hover:text-qm-green-dim font-medium transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>

      {/* ─── RIGHT: Marketing Panel ─── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center p-10 xl:p-14 order-1 lg:order-2">
        <div className="max-w-md animate-fade-in">
          <h2 className="text-4xl xl:text-5xl font-extrabold text-qm-text leading-tight">
            Start your journey to
          </h2>
          <p className="text-4xl xl:text-5xl font-extrabold text-qm-green mt-1">
            smarter investing
          </p>
          <p className="text-qm-text2 text-base mt-4 leading-relaxed">
            Get instant access to AI-powered market intelligence and
            never miss a market-moving news event again.
          </p>

          <div className="space-y-3 mt-8">
            {RIGHT_FEATURES.map((f, i) => (
              <div
                key={i}
                className="flex items-start gap-4 p-4 rounded-xl border border-qm-border bg-qm-card/60"
              >
                <div className={`flex items-center justify-center h-10 w-10 rounded-lg border flex-shrink-0 ${f.color}`}>
                  {f.icon}
                </div>
                <div>
                  <div className="font-semibold text-qm-text text-sm">{f.title}</div>
                  <div className="text-qm-text3 text-xs mt-0.5">{f.desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Stats strip */}
          <div className="flex gap-8 mt-8 pt-6 border-t border-qm-border">
            {STATS.map((s, i) => (
              <div key={i}>
                <div className="text-2xl font-extrabold text-qm-green">{s.value}</div>
                <div className="text-xs text-qm-text3 mt-0.5">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}
