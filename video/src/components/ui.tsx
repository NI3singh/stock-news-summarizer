import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, fontFamily } from "../theme";

/** Fade a scene in at the start and out at the end (local Sequence frame). */
export const useFadeInOut = (durationInFrames: number, fade = 12): number => {
  const f = useCurrentFrame();
  return interpolate(
    f,
    [0, fade, durationInFrames - fade, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
};

/** Eased 0→1 ramp between two frames. */
export const ramp = (frame: number, a: number, b: number): number =>
  interpolate(frame, [a, b], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

export const Bg: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ backgroundColor: C.bg, fontFamily }}>
    <AbsoluteFill
      style={{
        backgroundImage:
          "linear-gradient(rgba(148,163,184,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.045) 1px, transparent 1px)",
        backgroundSize: "54px 54px",
        WebkitMaskImage:
          "radial-gradient(ellipse 85% 80% at 50% 42%, black, transparent 100%)",
        maskImage:
          "radial-gradient(ellipse 85% 80% at 50% 42%, black, transparent 100%)",
      }}
    />
    <AbsoluteFill
      style={{
        backgroundImage:
          "radial-gradient(ellipse 70% 45% at 50% -6%, rgba(34,197,94,0.16), transparent 60%)",
      }}
    />
    {children}
  </AbsoluteFill>
);

export const BrowserFrame: React.FC<{
  url?: string;
  width: number;
  height: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ url = "stockstalker.ai", width, height, children, style }) => (
  <div
    style={{
      width,
      height,
      borderRadius: 16,
      overflow: "hidden",
      background: C.bg2,
      border: `1px solid ${C.border}`,
      boxShadow:
        "0 50px 130px rgba(0,0,0,0.65), 0 0 0 1px rgba(34,197,94,0.08)",
      display: "flex",
      flexDirection: "column",
      ...style,
    }}
  >
    <div
      style={{
        height: 46,
        background: "#0e1422",
        borderBottom: `1px solid ${C.border}`,
        display: "flex",
        alignItems: "center",
        padding: "0 18px",
        gap: 10,
        flexShrink: 0,
      }}
    >
      <div style={{ display: "flex", gap: 9 }}>
        {["#ff5f57", "#febc2e", "#28c840"].map((c) => (
          <div key={c} style={{ width: 13, height: 13, borderRadius: 7, background: c }} />
        ))}
      </div>
      <div
        style={{
          marginLeft: 16,
          flex: 1,
          maxWidth: 380,
          height: 26,
          borderRadius: 13,
          background: "#0a0f1a",
          border: `1px solid ${C.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: C.text3,
          fontSize: 13,
        }}
      >
        {url}
      </div>
    </div>
    <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>{children}</div>
  </div>
);

export const GaugeRing: React.FC<{
  size: number;
  progress: number;
  color?: string;
  thickness?: number;
  children?: React.ReactNode;
}> = ({ size, progress, color = C.green, thickness = 10, children }) => {
  const r = (size - thickness) / 2;
  const circ = 2 * Math.PI * r;
  const p = Math.max(0, Math.min(1, progress));
  return (
    <div style={{ width: size, height: size, position: "relative" }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={r} stroke={C.card2} strokeWidth={thickness} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={color}
          strokeWidth={thickness}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - p)}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {children}
      </div>
    </div>
  );
};

export const Sparkline: React.FC<{
  points: number[];
  width: number;
  height: number;
  progress: number;
  color?: string;
  gradId?: string;
}> = ({ points, width, height, progress, color = C.green, gradId = "spark" }) => {
  const min = Math.min(...points);
  const max = Math.max(...points);
  const nx = (i: number) => (i / (points.length - 1)) * width;
  const ny = (v: number) => height - ((v - min) / (max - min || 1)) * height * 0.9 - height * 0.05;
  const line = points
    .map((v, i) => `${i === 0 ? "M" : "L"} ${nx(i).toFixed(1)} ${ny(v).toFixed(1)}`)
    .join(" ");
  const area = `${line} L ${width} ${height} L 0 ${height} Z`;
  return (
    <svg width={width} height={height}>
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.3" />
          <stop offset="1" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradId})`} opacity={progress} />
      <path
        d={line}
        stroke={color}
        strokeWidth={2.5}
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - Math.max(0, Math.min(1, progress))}
      />
    </svg>
  );
};

/** A count-up number driven by a 0→1 progress value. */
export const Count: React.FC<{
  to: number;
  progress: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  signed?: boolean;
}> = ({ to, progress, decimals = 0, prefix = "", suffix = "", signed = false }) => {
  const v = to * Math.max(0, Math.min(1, progress));
  const sign = signed && to >= 0 ? "+" : "";
  return (
    <>
      {prefix}
      {sign}
      {v.toFixed(decimals)}
      {suffix}
    </>
  );
};

export const Panel: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({
  children,
  style,
}) => (
  <div
    style={{
      background: C.card,
      border: `1px solid ${C.border}`,
      borderRadius: 14,
      ...style,
    }}
  >
    {children}
  </div>
);
