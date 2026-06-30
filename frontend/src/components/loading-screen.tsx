"use client";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import LogoMark from "@/components/icons/logo-mark";

interface LoadingScreenProps {
  onComplete?: () => void;
  duration?: number;
}

const LOADING_MESSAGES = [
  "Initializing market data...",
  "Connecting to exchanges...",
  "Analyzing stock patterns...",
  "Loading your portfolio...",
  "Almost ready...",
];

export function LoadingScreen({ onComplete, duration = 2000 }: LoadingScreenProps) {
  const [progress, setProgress] = useState(0);
  const [textIndex, setTextIndex] = useState(0);

  useEffect(() => {
    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressTimer);
          if (onComplete) setTimeout(onComplete, 300);
          return 100;
        }
        return prev + Math.random() * 12 + 4;
      });
    }, duration / 30);

    const textTimer = setInterval(() => {
      setTextIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 600);

    return () => {
      clearInterval(progressTimer);
      clearInterval(textTimer);
    };
  }, [onComplete, duration]);

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center overflow-hidden bg-[#0a0f1a]">
      {/* Soft ambient glow that gently breathes — no rotating rings */}
      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/2 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-market-green-500/10 blur-[120px]"
        animate={{ opacity: [0.35, 0.6, 0.35], scale: [0.95, 1.06, 0.95] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center px-6">
        {/* Logo — gentle float over a soft breathing halo */}
        <motion.div
          className="relative mb-8 flex items-center justify-center"
          initial={{ scale: 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="absolute h-28 w-28 rounded-full bg-market-green-500/20 blur-2xl"
            animate={{ scale: [1, 1.25, 1], opacity: [0.55, 0.9, 0.55] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            <LogoMark className="relative z-10 h-24 w-24" />
          </motion.div>
        </motion.div>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-7 text-center"
        >
          <h1 className="text-3xl font-extrabold tracking-tight text-white">
            Stock<span className="text-market-green-400">Stalker</span>
          </h1>
          <p className="mt-1 text-xs uppercase tracking-[0.4em] text-market-green-500">AI</p>
        </motion.div>

        {/* Progress bar with a moving shimmer */}
        <div className="relative h-1.5 w-72 overflow-hidden rounded-full bg-white/5">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-market-green-600 to-market-green-400"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />
          <motion.div
            className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-white/30 to-transparent"
            animate={{ x: ["-130%", "430%"] }}
            transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>

        {/* Status message + animated dots */}
        <div className="mt-5 flex items-center gap-2 text-sm text-market-dark-400">
          <motion.span key={textIndex} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {LOADING_MESSAGES[textIndex]}
          </motion.span>
          <span className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="h-1 w-1 rounded-full bg-market-green-400"
                animate={{ opacity: [0.2, 1, 0.2] }}
                transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.18 }}
              />
            ))}
          </span>
        </div>

        <p className="mt-3 font-mono text-xs text-market-green-400">{Math.floor(progress)}%</p>
      </div>

      {/* Ticker tape */}
      <div className="absolute bottom-0 left-0 right-0 h-8 overflow-hidden border-t border-white/5 bg-[#0a0f1a]/80">
        <motion.div
          className="flex h-full items-center whitespace-nowrap"
          animate={{ x: ["0%", "-50%"] }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        >
          {[...Array(20)].map((_, i) => (
            <span key={i} className="mx-6 inline-flex items-center gap-3 text-xs">
              <span className="font-semibold text-white">
                {["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"][i % 5]}
              </span>
              <span className={i % 3 === 0 ? "text-market-green-400" : "text-market-red-400"}>
                {i % 3 === 0 ? "+" : "-"}
                {((i % 5) + 1) * 0.45}%
              </span>
            </span>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
