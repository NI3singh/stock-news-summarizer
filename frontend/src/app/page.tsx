"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, useInView, useScroll, useTransform } from "framer-motion";
import {
  TrendingUp, TrendingDown, ArrowRight, BarChart3, Bell, Cpu,
  LineChart, Database, Target, ChevronRight, ChevronDown, Zap,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { LoadingScreen } from "@/components/loading-screen";
import LogoMark from "@/components/icons/logo-mark";

function AnimatedCounter({ value, suffix = "", duration = 2 }: { value: number; suffix?: string; duration?: number }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;
    const startTime = Date.now();
    const animate = () => {
      const elapsed = (Date.now() - startTime) / 1000;
      const progress = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(easeOut * value));
      if (progress < 1) requestAnimationFrame(animate);
    };
    animate();
  }, [isInView, value, duration]);

  return <span ref={ref}>{count}{suffix}</span>;
}

function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useTransform(scrollYProgress, [0, 1], [0, 1]);
  return (
    <motion.div
      className="fixed top-0 left-0 right-0 h-1 bg-gradient-to-r from-market-red-500 via-market-green-500 to-market-red-500 origin-left z-[55]"
      style={{ scaleX }}
    />
  );
}

function FloatingStock({ delay, index }: { delay: number; index: number }) {
  const isPositive = index % 2 === 0;
  const percent = (index % 5) + 1;
  return (
    <motion.div
      className="absolute text-xs font-mono px-2 py-1 rounded glass-card"
      style={{ background: isPositive ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)", top: `${20 + (index * 15) % 60}%` }}
      initial={{ opacity: 0, x: -100 }}
      animate={{ opacity: [0, 1, 0], x: [0, 100, 300] }}
      transition={{ duration: 10, repeat: Infinity, delay, ease: "linear" }}
    >
      <span className={isPositive ? "text-market-green-400" : "text-market-red-400"}>
        {isPositive ? "+" : "-"}{percent}%
      </span>
    </motion.div>
  );
}

const TICKERS = [
  { symbol: "AAPL", price: "178.72", change: "+2.34%", isUp: true },
  { symbol: "GOOGL", price: "141.80", change: "+1.56%", isUp: true },
  { symbol: "MSFT", price: "378.91", change: "-0.42%", isUp: false },
  { symbol: "AMZN", price: "178.35", change: "+3.21%", isUp: true },
  { symbol: "TSLA", price: "248.50", change: "-1.87%", isUp: false },
  { symbol: "NVDA", price: "495.22", change: "+4.12%", isUp: true },
  { symbol: "META", price: "335.12", change: "+1.89%", isUp: true },
  { symbol: "AMD", price: "142.30", change: "+2.45%", isUp: true },
  { symbol: "NFLX", price: "485.60", change: "-0.89%", isUp: false },
  { symbol: "DIS", price: "112.45", change: "+0.78%", isUp: true },
];

const FEATURES = [
  { icon: <Cpu className="w-7 h-7" />, title: "Multi-Agent Analysis", description: "Four specialized agents — memory, news, quant, and orchestrator — analyze every ticker with Google Gemini.", color: "green" as const, delay: 0 },
  { icon: <LineChart className="w-7 h-7" />, title: "Sentiment Tracking", description: "Per-ticker sentiment scores and a daily “what changed” summary of the news.", color: "red" as const, delay: 0.1 },
  { icon: <BarChart3 className="w-7 h-7" />, title: "Quant Signals", description: "RSI, MACD, and Bollinger Bands computed alongside the news for each ticker.", color: "green" as const, delay: 0.2 },
  { icon: <Bell className="w-7 h-7" />, title: "Telegram Alerts", description: "Get a message on Telegram when sentiment shifts on your watchlist.", color: "red" as const, delay: 0.3 },
  { icon: <Database className="w-7 h-7" />, title: "Vector Memory", description: "Remembers past analyses and learns across runs with retrieval-augmented memory.", color: "green" as const, delay: 0.4 },
  { icon: <Target className="w-7 h-7" />, title: "ML Signal Model", description: "A per-ticker model that flags likely up/down moves from your analysis history.", color: "red" as const, delay: 0.5 },
];

const STEPS = [
  { step: "01", title: "Add Your Watchlist", description: "Add the stock tickers you want to track — no brokerage account needed.", icon: <BarChart3 className="w-8 h-8" />, iconBg: "bg-market-green-500/20", iconText: "text-market-green-400", corner: "from-market-green-500/10" },
  { step: "02", title: "AI Runs the Pipeline", description: "Agents gather news, score sentiment, compute quant signals, and synthesize an analysis.", icon: <Cpu className="w-8 h-8" />, iconBg: "bg-market-red-500/20", iconText: "text-market-red-400", corner: "from-market-red-500/10" },
  { step: "03", title: "Get Insights & Alerts", description: "Read the daily synthesis and receive Telegram alerts when sentiment shifts.", icon: <Bell className="w-8 h-8" />, iconBg: "bg-market-green-500/20", iconText: "text-market-green-400", corner: "from-market-green-500/10" },
];

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!loading && user) router.push("/dashboard");
  }, [user, loading, router]);

  return (
    <>
      {isLoading && <LoadingScreen onComplete={() => setIsLoading(false)} duration={2000} />}
      <ScrollProgress />

      <div className={`min-h-screen stock-grid-bg relative overflow-hidden ${isLoading ? "hidden" : ""}`}>
        {/* Animated Background */}
        <div className="fixed inset-0 pointer-events-none">
          <div className="floating-orb w-[600px] h-[600px] bg-market-green-500 -top-64 -left-64 opacity-10" />
          <div className="floating-orb w-[500px] h-[500px] bg-market-red-500 top-1/2 -right-64 opacity-10" style={{ animationDelay: "3s" }} />
          <div className="floating-orb w-[400px] h-[400px] bg-market-green-400 bottom-0 left-1/3" style={{ animationDelay: "5s" }} />
          <div className="floating-orb w-[300px] h-[300px] bg-market-red-400 top-1/4 left-1/2" style={{ animationDelay: "7s" }} />
          {[...Array(6)].map((_, i) => (
            <FloatingStock key={i} delay={i} index={i} />
          ))}
        </div>

        {/* Header */}
        <header className="relative z-50">
          <nav className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
              <Link href="/" className="flex items-center gap-3">
                <LogoMark className="w-10 h-10" />
                <div>
                  <h1 className="text-2xl font-bold text-white leading-none">StockStalker</h1>
                  <span className="text-market-green-400 font-semibold text-sm gradient-text">AI</span>
                </div>
              </Link>
            </motion.div>

            <motion.div className="flex items-center gap-4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
              <Link href="/login" className="px-5 py-2.5 rounded-lg btn-market-red-outline font-medium hover-lift">Sign In</Link>
              <Link href="/signup" className="px-5 py-2.5 rounded-xl btn-market-green text-white font-semibold flex items-center gap-2 hover-lift">
                Get Started <ArrowRight className="w-4 h-4" />
              </Link>
            </motion.div>
          </nav>
        </header>

        {/* Hero */}
        <section className="relative z-10 max-w-7xl mx-auto px-6 pt-16 pb-24">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
              <motion.div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-market-green-500/10 border border-market-green-500/30 mb-8 cursor-pointer" whileHover={{ scale: 1.05 }}>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-market-green-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-market-green-500" />
                </span>
                <span className="text-market-green-400 text-sm font-medium">Powered by Google Gemini</span>
              </motion.div>

              <motion.h1 className="text-5xl lg:text-7xl font-bold text-white mb-6 leading-tight" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                Smart Stock Market
                <br />
                <span className="gradient-text">Intelligence</span>
              </motion.h1>

              <motion.p className="text-xl text-market-dark-300 mb-10 max-w-xl leading-relaxed" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                A multi-agent AI system that analyzes market news, tracks sentiment, computes quant signals, and alerts you — for the tickers you choose.
              </motion.p>

              <motion.div className="flex flex-col sm:flex-row gap-4" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                <Link href="/signup" className="px-8 py-4 rounded-xl btn-market-green text-white font-semibold text-lg flex items-center justify-center gap-2 shadow-green-lg hover-lift">
                  Get Started <ArrowRight className="w-5 h-5" />
                </Link>
                <Link href="/login" className="px-8 py-4 rounded-xl btn-market-red-outline font-semibold text-lg flex items-center justify-center gap-2 hover-lift">
                  Sign In
                </Link>
              </motion.div>

              <motion.div className="mt-12 grid grid-cols-3 gap-8" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                <div className="text-center">
                  <p className="text-3xl font-bold text-white"><AnimatedCounter value={4} /></p>
                  <p className="text-market-dark-400 text-sm">AI Agents</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-market-green-400"><AnimatedCounter value={3} />+</p>
                  <p className="text-market-dark-400 text-sm">News Sources</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-white">Gemini</p>
                  <p className="text-market-dark-400 text-sm">AI Engine</p>
                </div>
              </motion.div>

              <motion.div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-market-dark-400" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
                <span className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-market-green-500" /> Open source
                </span>
                <span>Self-hostable</span>
                <span>Vector memory &amp; ML signals</span>
              </motion.div>
            </motion.div>

            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.2 }} className="relative">
              <HeroCard />
            </motion.div>
          </div>
        </section>

        {/* Live Ticker */}
        <section className="relative z-10 border-y border-market-dark-700/50 bg-market-dark-900/50 backdrop-blur-sm">
          <div className="ticker-wrapper py-4">
            <div className="ticker-content">
              {[...TICKERS, ...TICKERS].map((t, i) => (
                <TickerItem key={i} {...t} />
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="relative z-10 max-w-7xl mx-auto px-6 py-24">
          <motion.div className="text-center mb-16" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <h2 className="text-4xl lg:text-5xl font-bold text-white mb-4">Everything you need to <span className="gradient-text">stay ahead</span></h2>
            <p className="text-market-dark-400 text-lg max-w-2xl mx-auto">A complete pipeline — from raw market news to sentiment, signals, and alerts.</p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {FEATURES.map((f, i) => (
              <FeatureCard key={i} {...f} />
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section className="relative z-10 max-w-7xl mx-auto px-6 py-24">
          <motion.div className="text-center mb-16" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <h2 className="text-4xl lg:text-5xl font-bold text-white mb-4">How It <span className="gradient-text">Works</span></h2>
            <p className="text-market-dark-400 text-lg max-w-2xl mx-auto">From watchlist to insight in three steps</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {STEPS.map((item, index) => (
              <motion.div key={index} className="glass-card rounded-2xl p-8 relative overflow-hidden hover-lift" initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: index * 0.2 }}>
                <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${item.corner} to-transparent rounded-bl-full`} />
                <div className={`w-16 h-16 rounded-2xl ${item.iconBg} ${item.iconText} flex items-center justify-center mb-6`}>{item.icon}</div>
                <p className="text-market-dark-400 text-sm font-mono mb-2">Step {item.step}</p>
                <h3 className="text-xl font-bold text-white mb-3">{item.title}</h3>
                <p className="text-market-dark-300">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="relative z-10 max-w-7xl mx-auto px-6 pb-24">
          <motion.div className="glass-card rounded-3xl p-12 text-center relative overflow-hidden card-border-gradient" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <div className="absolute inset-0 bg-gradient-to-r from-market-green-500/5 via-transparent to-market-red-500/5" />
            <div className="relative z-10">
              <motion.h2 className="text-4xl lg:text-5xl font-bold text-white mb-4" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
                Ready to make <span className="text-market-green-400">smarter decisions?</span>
              </motion.h2>
              <p className="text-market-dark-300 text-lg mb-8 max-w-xl mx-auto">Start analyzing your watchlist with multi-agent AI.</p>
              <motion.div className="flex flex-col sm:flex-row gap-4 justify-center" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }}>
                <Link href="/signup" className="px-8 py-4 rounded-xl btn-market-green text-white font-semibold text-lg flex items-center justify-center gap-2 shadow-green-lg hover-lift">
                  Get Started <ArrowRight className="w-5 h-5" />
                </Link>
                <Link href="/login" className="px-8 py-4 rounded-xl btn-market-red-outline font-semibold text-lg flex items-center justify-center gap-2 hover-lift">Sign In</Link>
              </motion.div>
              <p className="mt-6 text-market-dark-400 text-sm">Free &amp; open source</p>
            </div>
          </motion.div>
        </section>

        {/* Footer */}
        <footer className="relative z-10 border-t border-market-dark-700/50 py-8">
          <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <LogoMark className="w-6 h-6" />
              <span className="text-market-dark-400">© 2026 StockStalker AI. All rights reserved.</span>
            </div>
            <div className="flex items-center gap-6">
              <Link href="#" className="text-market-dark-400 hover:text-white transition-colors text-sm">Terms</Link>
              <Link href="#" className="text-market-dark-400 hover:text-white transition-colors text-sm">Privacy</Link>
              <Link href="#" className="text-market-dark-400 hover:text-white transition-colors text-sm">Contact</Link>
            </div>
          </div>
        </footer>

        <motion.button
          className="fixed bottom-8 right-8 w-12 h-12 rounded-full bg-market-dark-800 border border-market-red-500/30 flex items-center justify-center text-market-red-400 hover:bg-market-dark-700 transition-colors glass-card z-[60]"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        >
          <ChevronDown className="w-5 h-5 rotate-180" />
        </motion.button>
      </div>
    </>
  );
}

function HeroCard() {
  return (
    <motion.div className="glass-card rounded-2xl p-6 shadow-card card-border-gradient" whileHover={{ scale: 1.02 }} transition={{ type: "spring", stiffness: 300 }}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <motion.div className="w-12 h-12 rounded-xl bg-market-green-500/20 flex items-center justify-center" whileHover={{ rotate: 10 }}>
            <TrendingUp className="w-6 h-6 text-market-green-400" />
          </motion.div>
          <div>
            <p className="text-white font-bold text-lg">NVDA</p>
            <p className="text-market-dark-400 text-sm">NVIDIA Corp</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-white font-bold text-2xl">$495.22</p>
          <p className="text-market-green-400 text-sm flex items-center gap-1 font-medium justify-end">
            <TrendingUp className="w-4 h-4" /> +4.12%
          </p>
        </div>
      </div>

      <div className="h-32 mb-4 relative">
        <svg className="w-full h-full" viewBox="0 0 200 80" preserveAspectRatio="none">
          <defs>
            <linearGradient id="heroChartGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
            </linearGradient>
          </defs>
          <motion.path d="M0,60 Q20,55 40,50 T80,45 T120,35 T160,40 T200,20 L200,80 L0,80 Z" fill="url(#heroChartGradient)" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1, delay: 0.5 }} />
          <motion.path d="M0,60 Q20,55 40,50 T80,45 T120,35 T160,40 T200,20" fill="none" stroke="#22c55e" strokeWidth="2" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 2, ease: "easeOut" }} />
        </svg>
      </div>

      <div className="bg-market-dark-900/50 rounded-xl p-4 mb-4 border border-market-dark-700/50">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="w-4 h-4 text-market-green-400 animate-pulse" />
          <span className="text-market-green-400 text-sm font-medium">AI Analysis</span>
          <span className="ml-auto text-xs text-market-dark-400">example</span>
        </div>
        <p className="text-market-dark-200 text-sm leading-relaxed">Bullish sentiment across recent coverage — earnings beats and analyst upgrades. Sentiment has trended positive over the last few days.</p>
      </div>

      <div className="mb-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-market-dark-400">Market Sentiment</span>
          <span className="text-market-green-400 font-medium">Very Bullish</span>
        </div>
        <div className="h-2 bg-market-dark-700 rounded-full overflow-hidden">
          <motion.div className="h-full bg-gradient-to-r from-market-green-600 to-market-green-400" initial={{ width: 0 }} animate={{ width: "85%" }} transition={{ duration: 1, delay: 0.5, ease: "easeOut" }} />
        </div>
      </div>

      <div className="space-y-3">
        <NewsItem title="NVIDIA Reports Record Quarterly Revenue" time="2h ago" />
        <NewsItem title="AI Chip Demand Continues to Surge" time="4h ago" />
        <NewsItem title="Analysts Raise Price Targets" time="6h ago" />
      </div>

      <motion.button className="w-full mt-4 py-3 rounded-xl bg-market-green-500/10 text-market-green-400 font-medium hover:bg-market-green-500/20 transition-colors flex items-center justify-center gap-2" whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
        View Detailed Analysis <ArrowRight className="w-4 h-4" />
      </motion.button>
    </motion.div>
  );
}

function NewsItem({ title, time }: { title: string; time: string }) {
  return (
    <motion.div className="flex items-center gap-3 p-3 rounded-lg bg-market-dark-800/50 hover:bg-market-dark-700/50 transition-colors cursor-pointer group" whileHover={{ x: 5 }}>
      <motion.div className="w-3 h-3 rounded-full bg-market-green-400" animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }} />
      <p className="text-market-dark-200 text-sm flex-1 truncate group-hover:text-white transition-colors">{title}</p>
      <span className="text-market-dark-500 text-xs">{time}</span>
    </motion.div>
  );
}

function TickerItem({ symbol, price, change, isUp }: { symbol: string; price: string; change: string; isUp: boolean }) {
  return (
    <motion.span className="inline-flex items-center gap-4 mx-8 py-2 cursor-pointer" whileHover={{ scale: 1.05 }}>
      <span className="text-white font-bold">{symbol}</span>
      <span className="text-market-dark-300">${price}</span>
      <span className={`flex items-center gap-1 ${isUp ? "text-market-green-400" : "text-market-red-400"}`}>
        {isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
        <span className="font-medium">{change}</span>
      </span>
    </motion.span>
  );
}

function FeatureCard({ icon, title, description, color, delay }: { icon: React.ReactNode; title: string; description: string; color: "green" | "red"; delay: number }) {
  return (
    <motion.div
      className="glass-card rounded-xl p-6 hover-lift card-border-gradient group"
      initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
      transition={{ opacity: { delay, duration: 0.5 }, y: { delay, duration: 0.5 } }}
      whileHover={{ y: -10, transition: { duration: 0.3, delay: 0 } }}
    >
      <div className={`w-14 h-14 rounded-xl flex items-center justify-center mb-4 ${color === "green" ? "bg-market-green-500/20 text-market-green-400" : "bg-market-red-500/20 text-market-red-400"}`}>
        {icon}
      </div>
      <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
      <p className="text-market-dark-400 leading-relaxed">{description}</p>
      <div className={`mt-4 flex items-center gap-2 text-sm font-medium cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity ${color === "green" ? "text-market-green-400" : "text-market-red-400"}`}>
        Learn more <ChevronRight className="w-4 h-4" />
      </div>
    </motion.div>
  );
}
