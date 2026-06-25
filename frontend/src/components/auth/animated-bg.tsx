"use client";
import { motion } from "framer-motion";

function FloatingStock({ delay }: { delay: number }) {
  const isPositive = delay % 2 === 0;
  return (
    <motion.div
      className="absolute text-xs font-mono px-2 py-1 rounded glass-card"
      style={{
        background: isPositive ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
        top: `${15 + (delay * 13) % 65}%`,
      }}
      initial={{ opacity: 0, x: -100 }}
      animate={{ opacity: [0, 1, 0], x: [0, 80, 220] }}
      transition={{ duration: 8, repeat: Infinity, delay, ease: "linear" }}
    >
      <span className={isPositive ? "text-market-green-400" : "text-market-red-400"}>
        {isPositive ? "+" : "-"}
        {(delay % 5) + 1}%
      </span>
    </motion.div>
  );
}

/** Shared animated background for auth pages: floating orbs + drifting % badges. */
export function AnimatedAuthBg() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      <div className="floating-orb w-96 h-96 bg-market-green-500 top-10 -left-48 opacity-10" />
      <div
        className="floating-orb w-80 h-80 bg-market-red-500 bottom-10 -right-40 opacity-10"
        style={{ animationDelay: "4s" }}
      />
      <div
        className="floating-orb w-64 h-64 bg-market-green-400 top-1/2 left-1/3"
        style={{ animationDelay: "2s" }}
      />
      {[1, 3, 5].map((d) => (
        <FloatingStock key={d} delay={d} />
      ))}
    </div>
  );
}
