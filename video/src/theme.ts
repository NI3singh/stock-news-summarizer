import { loadFont } from "@remotion/google-fonts/Inter";

export const { fontFamily } = loadFont("normal", {
  weights: ["400", "500", "600", "700", "800"],
  subsets: ["latin"],
});

// StockStalker AI palette (mirrors the app's qm-* tokens).
export const C = {
  bg: "#0a0f1a",
  bg2: "#0d1117",
  card: "#161b2e",
  card2: "#1a2236",
  sidebar: "#16203a",
  border: "#2d3748",
  green: "#22c55e",
  greenDim: "#16a34a",
  greenLite: "#4ade80",
  greenBg: "rgba(34,197,94,0.10)",
  red: "#ef4444",
  redBg: "rgba(239,68,68,0.10)",
  amber: "#f59e0b",
  amberBg: "rgba(245,158,11,0.10)",
  text: "#f1f5f9",
  text2: "#94a3b8",
  text3: "#64748b",
} as const;
