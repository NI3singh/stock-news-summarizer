"use client";
import { motion } from "framer-motion";

// Deterministic upward path (no Math.random → no SSR hydration mismatch)
const CHART_PATH =
  "M0,118 Q40,108 70,112 Q110,116 140,92 Q175,66 210,78 Q245,88 280,58 Q315,40 350,52 Q380,60 400,34";

export default function StockChart() {
  return (
    <div className="glass-card rounded-xl p-6 relative overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-white font-semibold">AAPL</span>
            <span className="px-2 py-0.5 rounded text-xs bg-market-green-500/20 text-market-green-400">+2.34%</span>
          </div>
          <p className="text-market-dark-400 text-sm">Apple Inc.</p>
        </div>
        <div className="text-right">
          <p className="text-white font-bold text-xl">$178.72</p>
          <p className="text-market-green-400 text-sm">+$4.08</p>
        </div>
      </div>

      {/* Chart */}
      <svg viewBox="0 0 400 150" className="w-full h-32" preserveAspectRatio="none">
        <defs>
          <linearGradient id="stockChartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22c55e" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {[0, 1, 2, 3, 4].map((i) => (
          <line key={i} x1="0" y1={30 * i + 15} x2="400" y2={30 * i + 15} stroke="#1e293b" strokeWidth="1" />
        ))}

        {/* Area fill */}
        <motion.path
          d={`${CHART_PATH} L 400 150 L 0 150 Z`}
          fill="url(#stockChartGradient)"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
        />

        {/* Line */}
        <motion.path
          d={CHART_PATH}
          fill="none"
          stroke="#22c55e"
          strokeWidth="2"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 2, ease: "easeInOut" }}
        />

        {/* Glow */}
        <motion.path
          d={CHART_PATH}
          fill="none"
          stroke="#22c55e"
          strokeWidth="4"
          strokeLinecap="round"
          opacity="0.3"
          style={{ filter: "blur(4px)" }}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 2, ease: "easeInOut" }}
        />
      </svg>

      {/* Time labels */}
      <div className="flex justify-between text-xs text-market-dark-500 mt-2">
        <span>9:30</span>
        <span>11:00</span>
        <span>12:30</span>
        <span>2:00</span>
        <span>4:00</span>
      </div>

      {/* Live indicator */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-market-green-400 animate-pulse" />
        <span className="text-xs text-market-dark-400">LIVE</span>
      </div>
    </div>
  );
}
