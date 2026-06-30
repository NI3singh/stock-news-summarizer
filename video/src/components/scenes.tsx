import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { C, fontFamily } from "../theme";
import { LogoMark } from "./LogoMark";
import { BrowserFrame, Count, GaugeRing, Panel, Sparkline, ramp, useFadeInOut } from "./ui";

// Scene durations (frames @ 30fps). Sum = 1200 = 40s.
export const D = {
  intro: 120,
  value: 160,
  dash: 340,
  agents: 220,
  features: 220,
  outro: 190,
} as const;

const Section: React.FC<{ children: React.ReactNode; op?: number }> = ({ children, op = 1 }) => (
  <div
    style={{
      position: "absolute",
      top: 96,
      width: "100%",
      textAlign: "center",
      opacity: op,
      fontSize: 46,
      fontWeight: 700,
      color: C.text,
      letterSpacing: -0.5,
    }}
  >
    {children}
  </div>
);

/* ─────────────────────────── 1 · INTRO ─────────────────────────── */
export const SceneIntro: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const op = useFadeInOut(D.intro);
  const logoScale = spring({ frame: f, fps, config: { damping: 14, mass: 0.8 } });
  const titleOp = ramp(f, 16, 38);
  const titleY = interpolate(titleOp, [0, 1], [22, 0]);
  const tagOp = ramp(f, 34, 56);

  return (
    <AbsoluteFill
      style={{ opacity: op, alignItems: "center", justifyContent: "center", fontFamily }}
    >
      <div style={{ position: "relative", marginBottom: 26 }}>
        <div
          style={{
            position: "absolute",
            inset: -50,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(34,197,94,0.28), transparent 70%)",
            filter: "blur(22px)",
          }}
        />
        <LogoMark size={156} style={{ transform: `scale(${logoScale})`, position: "relative" }} />
      </div>
      <div
        style={{
          opacity: titleOp,
          transform: `translateY(${titleY}px)`,
          fontSize: 86,
          fontWeight: 800,
          letterSpacing: -2.5,
          color: C.text,
        }}
      >
        Stock<span style={{ color: C.green }}>Stalker</span>
      </div>
      <div
        style={{
          opacity: titleOp,
          transform: `translateY(${titleY}px)`,
          fontSize: 22,
          letterSpacing: 16,
          color: C.green,
          fontWeight: 600,
          marginTop: 6,
          marginLeft: 16,
        }}
      >
        A I
      </div>
      <div style={{ opacity: tagOp, marginTop: 30, fontSize: 28, color: C.text2, fontWeight: 500 }}>
        Multi-Agent Stock News Intelligence
      </div>
    </AbsoluteFill>
  );
};

/* ─────────────────────────── 2 · VALUE FLOW ─────────────────────── */
const FlowCard: React.FC<{ icon: string; title: string; sub: string; appear: number }> = ({
  icon,
  title,
  sub,
  appear,
}) => (
  <Panel
    style={{
      width: 320,
      padding: "30px 26px",
      textAlign: "center",
      opacity: appear,
      transform: `translateY(${interpolate(appear, [0, 1], [26, 0])}px)`,
    }}
  >
    <div style={{ fontSize: 52, marginBottom: 12 }}>{icon}</div>
    <div style={{ fontSize: 26, fontWeight: 700, color: C.text }}>{title}</div>
    <div style={{ fontSize: 17, color: C.text2, marginTop: 8, lineHeight: 1.4 }}>{sub}</div>
  </Panel>
);

const Arrow: React.FC<{ appear: number }> = ({ appear }) => (
  <div style={{ width: 70, display: "flex", alignItems: "center", justifyContent: "center", opacity: appear }}>
    <div style={{ height: 2, width: 44, background: C.green, position: "relative" }}>
      <div
        style={{
          position: "absolute",
          right: -2,
          top: -4,
          width: 10,
          height: 10,
          borderTop: `2px solid ${C.green}`,
          borderRight: `2px solid ${C.green}`,
          transform: "rotate(45deg)",
        }}
      />
    </div>
  </div>
);

export const SceneValue: React.FC = () => {
  const f = useCurrentFrame();
  const op = useFadeInOut(D.value);
  return (
    <AbsoluteFill style={{ opacity: op, fontFamily }}>
      <Section op={ramp(f, 8, 26)}>
        Turn market news into a clear verdict
      </Section>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ display: "flex", alignItems: "center" }}>
          <FlowCard icon="📰" title="Gather" sub="Polygon · Finviz · Yahoo · Google" appear={ramp(f, 26, 46)} />
          <Arrow appear={ramp(f, 46, 60)} />
          <FlowCard icon="🧠" title="Analyze" sub="Memory · News · Quant agents" appear={ramp(f, 58, 78)} />
          <Arrow appear={ramp(f, 78, 92)} />
          <FlowCard icon="📊" title="Synthesize" sub="One AI trading report" appear={ramp(f, 90, 110)} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ─────────────────────────── 3 · DASHBOARD ─────────────────────── */
const WATCH = [
  { t: "AAPL", s: 0.45 },
  { t: "NVDA", s: 0.78 },
  { t: "TSLA", s: 0.2 },
  { t: "AMZN", s: 0.3 },
  { t: "META", s: -0.15 },
  { t: "GOOGL", s: 0.48 },
];
const dot = (s: number) => (s > 0.2 ? C.green : s < -0.2 ? C.red : C.text3);
const SPARK = [0.05, -0.1, 0.08, 0.0, 0.18, 0.12, 0.28, 0.22, 0.34, 0.3, 0.42, 0.45];

const StatRow: React.FC<{ label: string; value: React.ReactNode; tag: string; tagColor?: string }> = ({
  label,
  value,
  tag,
  tagColor = C.text2,
}) => (
  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "12px 0", borderBottom: `1px solid ${C.border}` }}>
    <span style={{ fontSize: 16, color: C.text3, textTransform: "uppercase", letterSpacing: 1 }}>{label}</span>
    <span style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
      <span style={{ fontSize: 24, fontWeight: 700, color: C.text, fontVariantNumeric: "tabular-nums" }}>{value}</span>
      <span style={{ fontSize: 14, color: tagColor }}>{tag}</span>
    </span>
  </div>
);

export const SceneDashboard: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const op = useFadeInOut(D.dash);
  const enter = spring({ frame: f, fps, config: { damping: 18, mass: 0.6 } });
  const scale = interpolate(enter, [0, 1], [0.95, 1]);

  const gauge = ramp(f, 42, 104); // sentiment fill + count
  const sentVal = 0.45;
  const sparkP = ramp(f, 58, 140);
  const statsP = ramp(f, 54, 116);
  const lowerP = ramp(f, 96, 134);

  return (
    <AbsoluteFill style={{ opacity: op, alignItems: "center", justifyContent: "center", fontFamily }}>
      <div style={{ transform: `scale(${scale})`, opacity: enter }}>
        <BrowserFrame width={1580} height={830}>
          <div style={{ display: "flex", height: "100%", background: C.bg2 }}>
            {/* sidebar */}
            <div style={{ width: 272, background: C.sidebar, borderRight: `1px solid ${C.border}`, padding: 18, flexShrink: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
                <LogoMark size={30} />
                <span style={{ fontWeight: 800, fontSize: 20, color: C.text }}>
                  Stock<span style={{ color: C.green }}>Stalker</span>
                </span>
              </div>
              <div style={{ fontSize: 12, letterSpacing: 2, color: C.text3, fontWeight: 600, marginBottom: 12 }}>WATCHLIST</div>
              <div style={{ height: 38, borderRadius: 8, border: `1px solid ${C.border}`, background: C.bg, color: C.text3, display: "flex", alignItems: "center", padding: "0 12px", fontSize: 15, marginBottom: 14 }}>
                + Add ticker…
              </div>
              {WATCH.map((w, i) => {
                const a = ramp(f, 12 + i * 5, 30 + i * 5);
                const active = w.t === "AAPL";
                return (
                  <div
                    key={w.t}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      padding: "11px 12px",
                      borderRadius: 8,
                      marginBottom: 4,
                      opacity: a,
                      transform: `translateX(${interpolate(a, [0, 1], [-16, 0])}px)`,
                      background: active ? C.greenBg : "transparent",
                      borderLeft: active ? `2px solid ${C.green}` : "2px solid transparent",
                    }}
                  >
                    <div style={{ width: 9, height: 9, borderRadius: 5, background: dot(w.s) }} />
                    <span style={{ fontWeight: 600, fontSize: 17, color: C.text }}>{w.t}</span>
                    <span style={{ marginLeft: "auto", fontSize: 15, color: w.s >= 0 ? C.green : C.red, fontVariantNumeric: "tabular-nums" }}>
                      {w.s >= 0 ? "+" : ""}
                      {w.s.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* main */}
            <div style={{ flex: 1, padding: 30, minWidth: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 22 }}>
                <div>
                  <div style={{ fontSize: 44, fontWeight: 800, color: C.text }}>AAPL</div>
                  <div style={{ fontSize: 15, color: C.text3, marginTop: 2 }}>Analyzed: Jun 30, 2026 · 11:14 UTC</div>
                </div>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <div style={{ padding: "8px 16px", borderRadius: 8, background: C.greenBg, color: C.green, fontWeight: 700, fontSize: 16 }}>● Bullish</div>
                  <div style={{ padding: "8px 16px", borderRadius: 8, border: `1px solid ${C.border}`, color: C.text2, fontSize: 16 }}>⟳ Refresh</div>
                </div>
              </div>

              <div style={{ display: "flex", gap: 18, marginBottom: 18 }}>
                {/* sentiment gauge */}
                <Panel style={{ flex: "0 0 300px", padding: 22, display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div style={{ alignSelf: "flex-start", fontSize: 13, letterSpacing: 1.5, color: C.text3, fontWeight: 600, marginBottom: 10 }}>SENTIMENT</div>
                  <GaugeRing size={186} thickness={16} progress={interpolate(gauge, [0, 1], [0, (sentVal + 1) / 2])}>
                    <div style={{ fontSize: 46, fontWeight: 800, color: C.green, fontVariantNumeric: "tabular-nums" }}>
                      <Count to={sentVal} progress={gauge} decimals={2} signed />
                    </div>
                    <div style={{ fontSize: 16, color: C.text2 }}>Bullish</div>
                  </GaugeRing>
                </Panel>

                {/* sparkline */}
                <Panel style={{ flex: 1, padding: 22, display: "flex", flexDirection: "column" }}>
                  <div style={{ fontSize: 13, letterSpacing: 1.5, color: C.text3, fontWeight: 600, marginBottom: 6 }}>30-DAY SENTIMENT</div>
                  <div style={{ flex: 1, display: "flex", alignItems: "flex-end" }}>
                    <Sparkline points={SPARK} width={520} height={196} progress={sparkP} />
                  </div>
                </Panel>

                {/* stat cards */}
                <Panel style={{ flex: "0 0 280px", padding: "8px 22px" }}>
                  <StatRow label="RSI" value={<Count to={49.2} progress={statsP} decimals={1} />} tag="Neutral" />
                  <StatRow label="Volume" value={<><Count to={1.2} progress={statsP} decimals={1} />x</>} tag="Above avg" tagColor={C.green} />
                  <StatRow label="Articles" value={<Count to={24} progress={statsP} />} tag="analyzed" />
                </Panel>
              </div>

              {/* what changed + themes */}
              <div style={{ opacity: lowerP, transform: `translateY(${interpolate(lowerP, [0, 1], [16, 0])}px)` }}>
                <div style={{ background: C.amberBg, border: `1px solid rgba(245,158,11,0.3)`, borderRadius: 12, padding: "16px 20px", marginBottom: 14 }}>
                  <div style={{ color: C.amber, fontWeight: 700, fontSize: 16, marginBottom: 6 }}>⚡ What Changed</div>
                  <div style={{ color: C.text2, fontSize: 18, lineHeight: 1.45 }}>
                    Apple–Intel chip partnership reported; rising memory-cost pressure is offset by strong services momentum.
                  </div>
                </div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  {["Intel Partnership", "AI Strategy", "Services Growth", "Memory Costs"].map((t) => (
                    <span key={t} style={{ padding: "7px 14px", borderRadius: 20, background: C.card2, border: `1px solid ${C.border}`, color: C.text2, fontSize: 15 }}>
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </div>
    </AbsoluteFill>
  );
};

/* ─────────────────────────── 4 · AGENTS ─────────────────────────── */
const AGENTS = [
  { icon: "🧠", name: "Memory", role: "Recalls history (RAG)" },
  { icon: "📰", name: "News", role: "Sentiment & themes" },
  { icon: "📈", name: "Quant", role: "RSI · MACD · trend" },
  { icon: "✨", name: "Orchestrator", role: "Synthesizes it all" },
];

export const SceneAgents: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const op = useFadeInOut(D.agents);

  return (
    <AbsoluteFill style={{ opacity: op, fontFamily }}>
      <Section op={ramp(f, 8, 26)}>Four agents. One synthesis.</Section>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
          {AGENTS.map((ag, i) => {
            const start = 26 + i * 22;
            const sp = spring({ frame: f - start, fps, config: { damping: 16 } });
            const lit = ramp(f, start, start + 14);
            return (
              <React.Fragment key={ag.name}>
                <div
                  style={{
                    width: 230,
                    background: C.card,
                    border: `1px solid ${interpolate(lit, [0, 1], [0, 1]) > 0.5 ? C.green : C.border}`,
                    borderRadius: 16,
                    padding: "26px 18px",
                    textAlign: "center",
                    opacity: sp,
                    transform: `scale(${interpolate(sp, [0, 1], [0.8, 1])})`,
                    boxShadow: lit > 0.5 ? `0 0 28px rgba(34,197,94,0.18)` : "none",
                  }}
                >
                  <div style={{ fontSize: 46, marginBottom: 10 }}>{ag.icon}</div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: C.text }}>{ag.name}</div>
                  <div style={{ fontSize: 15, color: C.text2, marginTop: 6 }}>{ag.role}</div>
                  <div style={{ fontSize: 12, color: C.text3, marginTop: 8 }}>Agent {i + 1}</div>
                </div>
                {i < AGENTS.length - 1 && (
                  <div style={{ width: 46, display: "flex", justifyContent: "center", opacity: ramp(f, start + 10, start + 20) }}>
                    <span style={{ color: C.green, fontSize: 30 }}>→</span>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          bottom: 150,
          width: "100%",
          textAlign: "center",
          opacity: ramp(f, 130, 150),
          fontSize: 22,
          color: C.text2,
        }}
      >
        → produces a typed <span style={{ color: C.green, fontWeight: 700 }}>TickerAnalysis</span> — persisted &amp; indexed for next time
      </div>
    </AbsoluteFill>
  );
};

/* ─────────────────────────── 5 · FEATURES ─────────────────────── */
const FEATS = [
  { icon: "📰", t: "4 News Sources", s: "Polygon · Finviz · Yahoo · Google" },
  { icon: "🧠", t: "Vector Memory (RAG)", s: "pgvector — learns across runs" },
  { icon: "🛡️", t: "Resilient Sentiment", s: "Gemini + VADER fallback" },
  { icon: "🔔", t: "Telegram Bot + Alerts", s: "Commands, summaries, rules" },
  { icon: "🔌", t: "MCP Server", s: "Tools for Claude & Cursor" },
  { icon: "⏰", t: "Daily Scheduler", s: "Auto-refresh + digest" },
];

export const SceneFeatures: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const op = useFadeInOut(D.features);
  return (
    <AbsoluteFill style={{ opacity: op, fontFamily }}>
      <Section op={ramp(f, 8, 26)}>Everything built in</Section>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingTop: 60 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 380px)", gap: 22 }}>
          {FEATS.map((ft, i) => {
            const sp = spring({ frame: f - (24 + i * 8), fps, config: { damping: 16, mass: 0.6 } });
            return (
              <div
                key={ft.t}
                style={{
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: 16,
                  padding: "24px 26px",
                  display: "flex",
                  alignItems: "center",
                  gap: 18,
                  opacity: sp,
                  transform: `translateY(${interpolate(sp, [0, 1], [28, 0])}px)`,
                }}
              >
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 14,
                    background: C.greenBg,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 30,
                    flexShrink: 0,
                  }}
                >
                  {ft.icon}
                </div>
                <div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: C.text }}>{ft.t}</div>
                  <div style={{ fontSize: 16, color: C.text2, marginTop: 4 }}>{ft.s}</div>
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ─────────────────────────── 6 · OUTRO ─────────────────────────── */
export const SceneOutro: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const op = useFadeInOut(D.outro, 16);
  const logoScale = spring({ frame: f, fps, config: { damping: 14 } });
  const pulse = 1 + 0.03 * Math.sin((f / fps) * 2.2);
  const textOp = ramp(f, 18, 40);
  const chipsOp = ramp(f, 40, 64);

  return (
    <AbsoluteFill style={{ opacity: op, alignItems: "center", justifyContent: "center", fontFamily }}>
      <div style={{ position: "relative", marginBottom: 24 }}>
        <div
          style={{
            position: "absolute",
            inset: -60,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(34,197,94,0.3), transparent 70%)",
            filter: "blur(26px)",
          }}
        />
        <LogoMark size={130} style={{ transform: `scale(${logoScale * pulse})`, position: "relative" }} />
      </div>
      <div style={{ opacity: textOp, fontSize: 70, fontWeight: 800, letterSpacing: -2, color: C.text }}>
        Stock<span style={{ color: C.green }}>Stalker</span>{" "}
        <span style={{ color: C.green, fontSize: 36, fontWeight: 700, letterSpacing: 4 }}>AI</span>
      </div>
      <div style={{ opacity: textOp, marginTop: 14, fontSize: 26, color: C.text2 }}>
        Multi-agent quantitative news intelligence
      </div>
      <div style={{ opacity: chipsOp, marginTop: 34, display: "flex", gap: 12 }}>
        {["FastAPI", "Next.js", "Gemini", "pgvector", "Supabase"].map((t) => (
          <span
            key={t}
            style={{
              padding: "9px 18px",
              borderRadius: 22,
              border: `1px solid ${C.border}`,
              background: C.card,
              color: C.text2,
              fontSize: 17,
            }}
          >
            {t}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};
