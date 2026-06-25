"use client";
import { useState } from "react";
import Link from "next/link";
import { Mail, ArrowLeft } from "lucide-react";
import { Logo }   from "@/components/ui/logo";
import { Button } from "@/components/ui/button";
import { Input }  from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";

export default function ForgotPasswordPage() {
  const { resetPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [sent, setSent]   = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await resetPassword(email);
    } catch {
      // Always show the success state — don't reveal whether an email is registered
    }
    setLoading(false);
    setSent(true);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="flex justify-center mb-8">
          <Logo size="md" />
        </div>

        <div className="rounded-2xl border border-qm-border bg-qm-card p-8 shadow-2xl">
          {!sent ? (
            <>
              <h2 className="text-2xl font-bold text-qm-text mb-1">Reset password</h2>
              <p className="text-qm-text3 text-sm mb-6">
                Enter your email and we&apos;ll send you a reset link.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  label="Email address"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  leftIcon={<Mail className="h-4 w-4" />}
                  required
                />
                <Button type="submit" size="lg" loading={loading} className="w-full">
                  Send Reset Link
                </Button>
              </form>
            </>
          ) : (
            <div className="text-center">
              <div className="h-14 w-14 rounded-full bg-qm-green-bg border border-qm-green/30 flex items-center justify-center mx-auto mb-4">
                <Mail className="h-6 w-6 text-qm-green" />
              </div>
              <h2 className="text-xl font-bold text-qm-text mb-2">Check your email</h2>
              <p className="text-qm-text3 text-sm">
                We sent a reset link to <span className="text-qm-text font-medium">{email}</span>.
                Check your inbox and follow the instructions.
              </p>
            </div>
          )}

          <Link
            href="/login"
            className="flex items-center justify-center gap-2 mt-6 text-sm text-qm-text3 hover:text-qm-text2 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
