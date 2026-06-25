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
    <div className="fixed inset-0 bg-market-dark-900 z-[9999] flex items-center justify-center">
      {/* Rotating crosshair rings */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative w-64 h-64">
            {[0, 1, 2, 3].map((i) => (
              <motion.div
                key={i}
                className="absolute border border-market-green-500/20 rounded-full"
                style={{
                  width: `${100 + i * 50}px`,
                  height: `${100 + i * 50}px`,
                  top: "50%",
                  left: "50%",
                  transform: "translate(-50%, -50%)",
                }}
                animate={{ rotate: i % 2 === 0 ? 360 : -360 }}
                transition={{ duration: 10 + i * 2, repeat: Infinity, ease: "linear" }}
              />
            ))}
          </div>
        </div>
        {/* Scanning line */}
        <motion.div
          className="absolute inset-0 bg-gradient-to-b from-transparent via-market-green-500/5 to-transparent"
          animate={{ y: ["-100%", "100%"] }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        />
      </div>

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center">
        <motion.div
          className="relative mb-8"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="absolute inset-0 rounded-full bg-market-green-500/20"
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <motion.div
            className="absolute inset-0 rounded-full bg-market-green-500/10"
            animate={{ scale: [1, 2, 1], opacity: [0.3, 0, 0.3] }}
            transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
          />

          <LogoMark className="w-24 h-24 relative z-10" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-center mb-6"
        >
          <h1 className="text-3xl font-bold text-white mb-1">
            Stock<span className="text-market-green-400">Stalker</span>
          </h1>
          <p className="text-market-green-500 text-sm tracking-widest uppercase">AI</p>
        </motion.div>

        <div className="w-64 h-1 bg-market-dark-700 rounded-full overflow-hidden mb-4">
          <motion.div
            className="h-full bg-gradient-to-r from-market-green-500 via-market-green-300 to-market-green-500"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        <div className="flex items-center gap-2 mb-4">
          <motion.div
            className="w-3 h-3 border border-market-green-400 rounded-full relative"
            animate={{ borderColor: ["#22c55e", "#4ade80", "#22c55e"] }}
            transition={{ duration: 1, repeat: Infinity }}
          >
            <motion.div
              className="absolute top-1/2 left-1/2 w-1 h-1 bg-market-green-400 rounded-full -translate-x-1/2 -translate-y-1/2"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 0.5, repeat: Infinity }}
            />
          </motion.div>
          <p className="text-market-dark-400 text-sm">{LOADING_MESSAGES[textIndex]}</p>
        </div>

        <p className="text-market-green-400 text-xs font-mono">{Math.floor(progress)}%</p>
      </div>

      {/* Ticker tape */}
      <div className="absolute bottom-0 left-0 right-0 h-8 bg-market-dark-900/80 overflow-hidden">
        <motion.div
          className="flex items-center h-full whitespace-nowrap"
          animate={{ x: ["0%", "-50%"] }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        >
          {[...Array(20)].map((_, i) => (
            <span key={i} className="inline-flex items-center gap-4 mx-6 text-xs">
              <span className="text-white font-semibold">{["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"][i % 5]}</span>
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
