"use client";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface Props {
  score: number; // -1 .. +1
  size?: "sm" | "md" | "lg";
}

const R = 90;
const CX = 100;
const CY = 100;
const ARC_LEN = Math.PI * R; // length of the semicircle

function styleFor(score: number): { color: string; label: string } {
  if (score > 0.3) return { color: "#22c55e", label: "Bullish" };
  if (score > 0) return { color: "#84cc16", label: "Mildly Bullish" };
  if (score > -0.3) return { color: "#94a3b8", label: "Neutral" };
  if (score > -0.6) return { color: "#f59e0b", label: "Mildly Bearish" };
  return { color: "#ef4444", label: "Bearish" };
}

const SIZES = {
  sm: { w: "w-32", score: "text-lg", label: "text-[10px]" },
  md: { w: "w-48", score: "text-2xl", label: "text-xs" },
  lg: { w: "w-64", score: "text-3xl", label: "text-sm" },
};

export function SentimentGauge({ score, size = "md" }: Props) {
  const clamped = Math.max(-1, Math.min(1, score));
  const frac = (clamped + 1) / 2; // 0 (=-1) .. 1 (=+1)
  const { color, label } = styleFor(clamped);
  const sz = SIZES[size];

  // Animate the fill from 0 → frac on mount / score change.
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const id = requestAnimationFrame(() => setShown(frac));
    return () => cancelAnimationFrame(id);
  }, [frac]);

  const dashoffset = ARC_LEN * (1 - shown);
  const theta = (1 - shown) * Math.PI; // π (left) → 0 (right)
  const nx = CX + R * Math.cos(theta);
  const ny = CY - R * Math.sin(theta);

  return (
    <div className={cn("flex flex-col items-center", sz.w)}>
      <svg viewBox="0 0 200 110" className="w-full">
        <path
          d="M 10,100 A 90,90 0 0,1 190,100"
          fill="none"
          stroke="#334155"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <path
          d="M 10,100 A 90,90 0 0,1 190,100"
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={ARC_LEN}
          strokeDashoffset={dashoffset}
          style={{ transition: "stroke-dashoffset 0.7s ease-out" }}
        />
        <circle
          cx={nx}
          cy={ny}
          r="7"
          fill="#fff"
          stroke={color}
          strokeWidth="3"
          style={{ transition: "cx 0.7s ease-out, cy 0.7s ease-out" }}
        />
      </svg>
      <div className={cn("font-bold tabular-nums", sz.score)} style={{ color }}>
        {clamped >= 0 ? "+" : ""}
        {clamped.toFixed(2)}
      </div>
      <div className={cn("font-medium text-qm-text2", sz.label)}>{label}</div>
    </div>
  );
}
