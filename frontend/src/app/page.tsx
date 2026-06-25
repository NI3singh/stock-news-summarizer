import Link from "next/link";
import { Logo } from "@/components/ui/logo";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-qm-bg flex flex-col items-center justify-center p-8 text-center"
         style={{background: "radial-gradient(ellipse 70% 60% at 50% 100%, rgba(34,197,94,0.10) 0%, transparent 65%)"}}>
      <Logo size="lg" className="justify-center mb-8" />
      <h1 className="text-5xl font-extrabold text-qm-text mb-3">
        Multi-Agent Quant Intelligence
      </h1>
      <p className="text-qm-text2 text-lg max-w-xl mb-8 leading-relaxed">
        AI-powered stock market analysis using 4 specialized agents, vector memory,
        ML signal modeling, and Telegram alerts.
      </p>
      <div className="flex gap-4">
        <Link href="/login">
          <Button size="lg">Sign In →</Button>
        </Link>
        <Link href="/signup">
          <Button size="lg" variant="outline">Create Account</Button>
        </Link>
      </div>
      <p className="text-qm-text3 text-sm mt-12">
        Powered by Gemini AI · Built with Next.js · Open source
      </p>
    </div>
  );
}
