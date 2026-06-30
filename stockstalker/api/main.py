"""StockStalker v2 — REST API layer (FastAPI).

Exposes the CLI pipeline over HTTP so the Next.js frontend can drive it. A single
long-lived ``PipelineRunner`` is created once in the lifespan handler and reused
for every request (heavy resources — Chroma, LangChain, scrapers — built once).

Run with:  ``python stockstalker/main.py api``  (or ``stockstalker api``) → port 8000.
"""
import asyncio
import uuid
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ValidationError

from stockstalker.config import settings
from stockstalker.utils import logger

# --- Shared state ---
_runner = None
_scheduler = None  # DailyScheduler instance when ENABLE_BACKGROUND_JOBS runs jobs in-process
_jobs: dict = {}
_jobs_lock = Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _runner, _scheduler
    from stockstalker.pipeline import PipelineRunner

    _runner = PipelineRunner()
    await _runner.initialize()

    # Enable Telegram if creds are set (no-op otherwise). Guarded so a bad or
    # unreachable token can't crash API startup.
    _runner.enable_telegram()
    if _runner.bot is not None:
        try:
            if settings.enable_background_jobs:
                # Single-service mode: this process ALSO polls Telegram, so the bot
                # answers commands here (no separate `run-scheduler` needed).
                await _runner.bot.run_polling()
            else:
                # Web-only mode: just init the HTTP client so alert pushes and the
                # /api/alerts/test button can SEND. Command polling runs separately
                # via `python main.py run-scheduler`.
                await _runner.bot.app.initialize()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Telegram bot startup failed ({}); disabling bot.", exc)
            _runner.bot = None

    # Single-service mode also runs the daily refresh + summary scheduler in-process.
    if settings.enable_background_jobs:
        from stockstalker.pipeline import DailyScheduler

        _scheduler = DailyScheduler(_runner)
        _scheduler.start()
        logger.info("Background jobs enabled — scheduler running inside the API process")

    logger.info("StockStalker API started")
    yield

    if _scheduler is not None:
        try:
            _scheduler.stop()
        except Exception:  # noqa: BLE001
            pass
    if _runner.bot is not None:
        try:
            if settings.enable_background_jobs:
                await _runner.bot.stop()
            else:
                await _runner.bot.app.shutdown()
        except Exception:  # noqa: BLE001
            pass
    logger.info("StockStalker API shutting down")


app = FastAPI(title="StockStalker API", version="2.0.0", lifespan=lifespan)

# Local dev origins + any production frontend origin(s) from FRONTEND_ORIGIN.
_cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if settings.frontend_origin:
    _cors_origins += [o.strip() for o in settings.frontend_origin.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_runner():
    if _runner is None:
        raise HTTPException(503, "Runner not initialized")
    return _runner


# --- Request models ---
class AddTickerRequest(BaseModel):
    symbol: str


_FRONTEND_URL = (
    settings.frontend_origin.split(",", 1)[0].strip()
    if settings.frontend_origin
    else "https://stockstalker-frontend.onrender.com"
)
_GITHUB_URL = "https://github.com/NI3singh/StockStalker-AI"

_LANDING_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>StockStalker AI - Backend Live</title>
<meta name="description" content="The StockStalker AI backend is live. Open the frontend dashboard for market intelligence, or star the project on GitHub.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%230d1117'/%3E%3Cpath d='M8 52 L16 45 L25 48 L34 36 L43 40 L56 14' fill='none' stroke='%2322c55e' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/%3E%3Ccircle cx='56' cy='14' r='7' fill='none' stroke='%234ade80' stroke-width='2'/%3E%3Cpath d='M56 4v7M56 17v7M46 14h7M59 14h7' stroke='%234ade80' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0a0f1a;
    --card: rgba(30, 41, 59, 0.72);
    --card-strong: rgba(15, 23, 42, 0.82);
    --border: rgba(71, 85, 105, 0.38);
    --text: #f1f5f9;
    --muted: #94a3b8;
    --dim: #64748b;
    --green: #22c55e;
    --green-2: #4ade80;
    --green-3: #16a34a;
    --red: #ef4444;
    --red-2: #f87171;
  }
  html, body { min-height: 100%; overflow-x: hidden; }
  body {
    min-height: 100vh;
    color: var(--text);
    font-family: "Inter", system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
    background-color: var(--bg);
    background-image:
      radial-gradient(ellipse 90% 60% at 50% -15%, rgba(34, 197, 94, 0.12), transparent 58%),
      radial-gradient(ellipse 70% 55% at 105% 55%, rgba(239, 68, 68, 0.10), transparent 62%),
      linear-gradient(rgba(34, 197, 94, 0.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(34, 197, 94, 0.035) 1px, transparent 1px),
      linear-gradient(rgba(239, 68, 68, 0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(239, 68, 68, 0.02) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 52px 52px, 52px 52px, 26px 26px, 26px 26px;
  }
  body::after {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: 0.34;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  }
  .ambient { position: fixed; inset: 0; pointer-events: none; overflow: hidden; }
  .orb {
    position: absolute;
    border-radius: 999px;
    filter: blur(66px);
    opacity: 0.16;
    animation: float 8s ease-in-out infinite;
  }
  .orb.green { width: 620px; height: 620px; left: -260px; top: -220px; background: var(--green); }
  .orb.red { width: 520px; height: 520px; right: -230px; bottom: -200px; background: var(--red); animation-delay: 2.5s; }
  .orb.lime { width: 360px; height: 360px; left: 48%; bottom: 6%; background: var(--green-2); opacity: 0.11; animation-delay: 4s; }
  .stock {
    position: absolute;
    border: 1px solid rgba(71, 85, 105, 0.32);
    border-radius: 9px;
    padding: 6px 10px;
    background: rgba(15, 23, 42, 0.58);
    backdrop-filter: blur(14px);
    font-size: 12px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--green-2);
    animation: drift 13s linear infinite;
  }
  .stock.red { color: var(--red-2); }
  .stock:nth-child(4) { top: 18%; left: -80px; animation-delay: 0s; }
  .stock:nth-child(5) { top: 36%; left: -100px; animation-delay: 2.5s; }
  .stock:nth-child(6) { top: 56%; left: -90px; animation-delay: 5s; }
  .stock:nth-child(7) { top: 74%; left: -110px; animation-delay: 7.5s; }
  .wrap {
    position: relative;
    z-index: 2;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 56px 22px;
  }
  .panel {
    width: min(100%, 920px);
    display: grid;
    grid-template-columns: minmax(0, 1.08fr) minmax(280px, 0.92fr);
    gap: 28px;
    align-items: center;
  }
  .content { padding: 10px 0; }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    color: var(--text);
    text-decoration: none;
    margin-bottom: 30px;
    animation: rise 0.55s ease both;
  }
  .mark { width: 48px; height: 48px; flex-shrink: 0; }
  .brand-text strong { display: block; font-size: 25px; line-height: 1; letter-spacing: -0.035em; }
  .brand-text span {
    display: inline-block;
    margin-top: 3px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: transparent;
    background: linear-gradient(90deg, var(--green), var(--green-2), var(--green), var(--green-3));
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    animation: shimmer 3s linear infinite;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    padding: 8px 14px;
    border-radius: 999px;
    border: 1px solid rgba(34, 197, 94, 0.3);
    background: rgba(34, 197, 94, 0.08);
    color: var(--green-2);
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 24px;
    animation: rise 0.55s ease both 0.08s;
  }
  .ping { position: relative; display: inline-flex; width: 8px; height: 8px; }
  .ping::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 999px;
    background: var(--green);
    animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
  }
  .ping::after {
    content: "";
    position: relative;
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--green);
  }
  h1 {
    max-width: 690px;
    font-size: clamp(3rem, 7vw, 5.8rem);
    line-height: 0.98;
    letter-spacing: -0.06em;
    margin-bottom: 24px;
    animation: rise 0.55s ease both 0.16s;
  }
  .grad {
    color: transparent;
    background: linear-gradient(90deg, var(--green), var(--green-2), var(--green), var(--green-3));
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    animation: shimmer 3.4s linear infinite;
  }
  .subtitle {
    max-width: 590px;
    color: #cbd5e1;
    font-size: 18px;
    line-height: 1.75;
    margin-bottom: 32px;
    animation: rise 0.55s ease both 0.24s;
  }
  .subtitle strong { color: var(--text); font-weight: 800; }
  .star-anim {
    display: inline-block;
    vertical-align: -0.18em;
    width: 1.1em;
    height: 1.1em;
    margin: 0 0.12em;
    animation: star-spin 3.5s ease-in-out infinite;
    filter: drop-shadow(0 0 4px rgba(245, 158, 11, 0.65));
  }
  .rule {
    width: min(100%, 340px);
    height: 1px;
    background: linear-gradient(90deg, rgba(34, 197, 94, 0), rgba(34, 197, 94, 0.5), rgba(239, 68, 68, 0.35), rgba(34, 197, 94, 0));
    margin-bottom: 32px;
    animation: rise 0.55s ease both 0.3s;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    animation: rise 0.55s ease both 0.36s;
  }
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 9px;
    min-height: 50px;
    padding: 0 24px;
    border-radius: 14px;
    text-decoration: none;
    font-weight: 800;
    font-size: 15px;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
  }
  .btn.primary {
    color: white;
    border: 1px solid rgba(74, 222, 128, 0.55);
    background: linear-gradient(135deg, var(--green), var(--green-3));
    box-shadow: 0 12px 36px rgba(34, 197, 94, 0.28);
  }
  .btn.primary:hover { transform: translateY(-2px); box-shadow: 0 18px 46px rgba(34, 197, 94, 0.38); }
  .btn.ghost {
    color: #e2e8f0;
    border: 1px solid rgba(239, 68, 68, 0.46);
    background: rgba(15, 23, 42, 0.42);
  }
  .btn.ghost:hover { transform: translateY(-2px); border-color: rgba(248, 113, 113, 0.82); background: rgba(239, 68, 68, 0.1); }
  .preview {
    position: relative;
    border-radius: 22px;
    padding: 1px;
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.38), rgba(239, 68, 68, 0.28), rgba(34, 197, 94, 0.28));
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.36);
    animation: rise 0.65s ease both 0.22s;
  }
  .card {
    overflow: hidden;
    border-radius: 22px;
    background: var(--card);
    backdrop-filter: blur(22px);
    border: 1px solid rgba(255, 255, 255, 0.04);
    padding: 22px;
  }
  .card-head, .row, .metric { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
  .ticker { display: flex; align-items: center; gap: 12px; }
  .iconbox {
    width: 46px;
    height: 46px;
    display: grid;
    place-items: center;
    border-radius: 14px;
    color: var(--green-2);
    background: rgba(34, 197, 94, 0.13);
  }
  .ticker strong { display: block; font-size: 20px; }
  .ticker span, .muted { color: var(--muted); font-size: 13px; }
  .price { text-align: right; }
  .price strong { display: block; font-size: 25px; }
  .price span { color: var(--green-2); font-size: 13px; font-weight: 700; }
  .chart { width: 100%; height: 138px; margin: 20px 0 16px; }
  .analysis {
    border: 1px solid rgba(71, 85, 105, 0.4);
    border-radius: 15px;
    padding: 14px;
    background: var(--card-strong);
    margin-bottom: 16px;
  }
  .analysis .row { justify-content: flex-start; margin-bottom: 7px; color: var(--green-2); font-weight: 800; font-size: 13px; }
  .analysis p { color: #cbd5e1; font-size: 13px; line-height: 1.6; }
  .bar {
    height: 8px;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(100, 116, 139, 0.28);
    margin: 8px 0 16px;
  }
  .fill {
    width: 84%;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--green-3), var(--green-2));
    animation: fill 1.1s ease both 0.8s;
  }
  .metric {
    padding: 12px;
    border-radius: 12px;
    background: rgba(15, 23, 42, 0.54);
    margin-top: 10px;
    color: #dbeafe;
    font-size: 13px;
  }
  .metric span:last-child { color: var(--green-2); font-weight: 800; }
  .note {
    margin-top: 26px;
    color: var(--dim);
    font-size: 13px;
    line-height: 1.7;
    animation: rise 0.55s ease both 0.42s;
  }
  .note code {
    color: var(--green-2);
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.18);
    border-radius: 6px;
    padding: 2px 6px;
  }
  @keyframes rise { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes shimmer { from { background-position: 0% center; } to { background-position: 200% center; } }
  @keyframes ping { 75%, 100% { transform: scale(2.4); opacity: 0; } }
  @keyframes float { 0%, 100% { transform: translateY(0) scale(1); } 50% { transform: translateY(-18px) scale(1.04); } }
  @keyframes drift { from { transform: translateX(0); opacity: 0; } 12%, 78% { opacity: 1; } to { transform: translateX(calc(100vw + 220px)); opacity: 0; } }
  @keyframes fill { from { width: 0; } to { width: 84%; } }
  @keyframes star-spin {
    0% { transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 3px rgba(245, 158, 11, 0.55)); }
    25% { transform: scale(1.38) rotate(72deg); filter: drop-shadow(0 0 11px rgba(250, 204, 21, 0.95)); }
    50% { transform: scale(1) rotate(144deg); filter: drop-shadow(0 0 3px rgba(245, 158, 11, 0.55)); }
    75% { transform: scale(1.38) rotate(216deg); filter: drop-shadow(0 0 11px rgba(250, 204, 21, 0.95)); }
    100% { transform: scale(1) rotate(360deg); filter: drop-shadow(0 0 3px rgba(245, 158, 11, 0.55)); }
  }
  @media (max-width: 820px) {
    .panel { grid-template-columns: 1fr; max-width: 620px; }
    .preview { order: -1; }
    .content { text-align: center; }
    .brand, .actions { justify-content: center; }
    .rule { margin-left: auto; margin-right: auto; }
  }
  @media (max-width: 520px) {
    .wrap { padding: 28px 16px; align-items: flex-start; }
    .preview { display: none; }
    .actions { flex-direction: column; }
    .btn { width: 100%; }
    h1 { font-size: 3rem; }
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
  }
</style>
</head>
<body>
  <div class="ambient" aria-hidden="true">
    <div class="orb green"></div>
    <div class="orb red"></div>
    <div class="orb lime"></div>
    <div class="stock">NVDA +4.12%</div>
    <div class="stock red">TSLA -1.87%</div>
    <div class="stock">AAPL +2.34%</div>
    <div class="stock red">MSFT -0.42%</div>
  </div>

  <main class="wrap">
    <section class="panel">
      <div class="content">
        <a class="brand" href="__FRONTEND_URL__" target="_blank" rel="noopener" aria-label="Open StockStalker AI frontend">
          <svg class="mark" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <defs>
              <linearGradient id="line" x1="4" y1="52" x2="44" y2="16" gradientUnits="userSpaceOnUse">
                <stop stop-color="#16a34a"/><stop offset="0.65" stop-color="#22c55e"/><stop offset="1" stop-color="#4ade80"/>
              </linearGradient>
              <linearGradient id="area" x1="0" y1="12" x2="0" y2="60" gradientUnits="userSpaceOnUse">
                <stop stop-color="#22c55e" stop-opacity="0.26"/><stop offset="1" stop-color="#22c55e" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path d="M4 52 L10 47 L18 49 L26 39 L34 42 L44 16 L44 58 L4 58Z" fill="url(#area)"/>
            <path d="M4 52 L10 47 L18 49 L26 39 L34 42 L44 16" stroke="url(#line)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="44" cy="16" r="15" stroke="#22c55e" stroke-width="0.5" opacity="0.16"/>
            <path d="M54.83 17.91 A11 11 0 0 1 45.91 26.83M42.09 26.83 A11 11 0 0 1 33.17 17.91M33.17 14.09 A11 11 0 0 1 42.09 5.17M45.91 5.17 A11 11 0 0 1 54.83 14.09" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="44" cy="16" r="5" stroke="#22c55e" stroke-width="1" opacity="0.65"/>
            <circle cx="44" cy="16" r="2" fill="#4ade80"/>
          </svg>
          <span class="brand-text"><strong>StockStalker</strong><span>AI</span></span>
        </a>

        <div class="badge"><span class="ping"></span> Backend Online</div>
        <h1>Thank you for <span class="grad">stopping by.</span></h1>
        <p class="subtitle">
          The StockStalker backend is live and running smoothly.
          <strong>Open the frontend to explore AI-powered market intelligence</strong>,
          sentiment shifts, quant signals, and watchlist alerts. If the project helps you,
          a
          <svg class="star-anim" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-label="star">
            <defs>
              <linearGradient id="starGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#fde68a"/>
                <stop offset="48%" stop-color="#f59e0b"/>
                <stop offset="100%" stop-color="#b45309"/>
              </linearGradient>
            </defs>
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="url(#starGrad)"/>
          </svg>
          on GitHub would mean a lot.
        </p>
        <div class="rule"></div>
        <div class="actions">
          <a class="btn primary" href="__FRONTEND_URL__" target="_blank" rel="noopener">
            Open Frontend
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
              <path d="M2 7.5h10.5M8.5 3.5l4 4-4 4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </a>
          <a class="btn ghost" href="__GITHUB_URL__" target="_blank" rel="noopener">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82A7.67 7.67 0 0 1 8 3.36c.68 0 1.36.09 2 .27 1.53-1.03 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.28.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/>
            </svg>
            Star on GitHub
          </a>
        </div>
        <p class="note">
          Health check: <code>/health</code>. API docs: <code>/docs</code>.
          First visits on Render free tier can take a little time to wake.
        </p>
      </div>

      <aside class="preview" aria-label="StockStalker preview">
        <div class="card">
          <div class="card-head">
            <div class="ticker">
              <div class="iconbox">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M3 17l6-6 4 4 8-9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M15 6h6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div><strong>NVDA</strong><span>NVIDIA Corp</span></div>
            </div>
            <div class="price"><strong>$495.22</strong><span>+4.12%</span></div>
          </div>
          <svg class="chart" viewBox="0 0 360 140" preserveAspectRatio="none" aria-hidden="true">
            <defs>
              <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#22c55e" stop-opacity="0.32"/>
                <stop offset="100%" stop-color="#22c55e" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path d="M0 110 Q36 96 70 100 T142 78 T214 62 T286 70 T360 34 L360 140 L0 140Z" fill="url(#chartFill)"/>
            <path d="M0 110 Q36 96 70 100 T142 78 T214 62 T286 70 T360 34" fill="none" stroke="#22c55e" stroke-width="3" stroke-linecap="round"/>
            <path d="M0 110 Q36 96 70 100 T142 78 T214 62 T286 70 T360 34" fill="none" stroke="#22c55e" stroke-width="7" stroke-linecap="round" opacity="0.17"/>
          </svg>
          <div class="analysis">
            <div class="row">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8Z" fill="currentColor"/>
              </svg>
              AI Analysis
            </div>
            <p>Bullish sentiment across recent coverage, earnings momentum, and analyst upgrades.</p>
          </div>
          <div class="row muted"><span>Market Sentiment</span><strong style="color:#4ade80">Very Bullish</strong></div>
          <div class="bar"><div class="fill"></div></div>
          <div class="metric"><span>Agents</span><span>Memory + News + Quant</span></div>
          <div class="metric"><span>Vector Store</span><span>RAG Ready</span></div>
        </div>
      </aside>
    </section>
  </main>
</body>
</html>
"""


# --- Routes ---

@app.get("/", response_class=HTMLResponse, tags=["meta"])
async def home():
    return (
        _LANDING_HTML
        .replace("__FRONTEND_URL__", _FRONTEND_URL)
        .replace("__GITHUB_URL__", _GITHUB_URL)
    )


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/api/tickers")
async def get_tickers():
    tickers = await get_runner().db.get_active_tickers()
    return {"success": True, "tickers": tickers}


@app.post("/api/tickers")
async def add_ticker(req: AddTickerRequest):
    symbol = req.symbol.strip().upper()
    if not symbol or len(symbol) > 10:
        raise HTTPException(400, "Invalid symbol")
    success = await get_runner().db.add_ticker(symbol)
    if not success:
        raise HTTPException(400, f"{symbol} already exists")
    # Kick off the first analysis as a TRACKED job (same mechanism as /api/refresh)
    # so the UI can poll progress and auto-show the result when it completes.
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {"status": "pending", "symbol": symbol, "result": None}
    asyncio.create_task(_run_job(job_id, symbol))
    return {"success": True, "job_id": job_id, "message": f"{symbol} added. Analyzing..."}


@app.delete("/api/tickers/{symbol}")
async def remove_ticker(symbol: str):
    await get_runner().db.deactivate_ticker(symbol.upper())
    return {"success": True, "message": f"{symbol} removed"}


@app.get("/api/summary/{symbol}")
async def get_summary(symbol: str, days: int = 7):
    runner = get_runner()
    symbol = symbol.upper()
    days = max(1, min(days, 90))
    # get_recent_analyses returns newest-first and already JSON-decodes the JSON
    # columns (articles_used / memory_context / key_themes / technical_signals).
    recent = await runner.db.get_recent_analyses(symbol, days=days)
    latest = recent[0] if recent else None
    articles = latest.get("articles_used", []) if latest else []
    return {
        "success": True,
        "symbol": symbol,
        "latest_summary": latest,
        "historical_summaries": recent,
        "articles": articles,
    }


@app.post("/api/refresh/{symbol}")
async def refresh_ticker(symbol: str):
    runner = get_runner()
    symbol = symbol.upper()
    tickers = await runner.db.get_active_tickers()
    if symbol not in tickers:
        raise HTTPException(404, f"{symbol} not found")
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {"status": "pending", "symbol": symbol, "result": None}
    asyncio.create_task(_run_job(job_id, symbol))
    return {"success": True, "job_id": job_id}


@app.post("/api/refresh-all")
async def refresh_all():
    runner = get_runner()
    tickers = await runner.db.get_active_tickers()
    job_map = {}
    for s in tickers:
        job_id = str(uuid.uuid4())
        with _jobs_lock:
            _jobs[job_id] = {"status": "pending", "symbol": s, "result": None}
        asyncio.create_task(_run_job(job_id, s))
        job_map[s] = job_id
    return {"success": True, "job_map": job_map}


@app.get("/api/job/{job_id}")
async def job_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"success": True, "job_id": job_id, **job}


# --- System endpoints (Phase D/E/F dashboards) ---

@app.get("/api/system/status")
async def system_status():
    runner = get_runner()
    tickers = await runner.db.get_active_tickers()
    vs_size = await runner.vector_store.collection_size()
    # Credential-safe DB label (never expose the Postgres password in the URL).
    db_url = runner.db.db_url
    db_label = (
        "postgres://" + db_url.split("@")[-1]
        if db_url.startswith("postgresql")
        else db_url
    )
    return {
        "tickers": len(tickers),
        "vector_store_size": vs_size,
        "scheduler_time": f"{settings.refresh_time} {settings.timezone}",
        "db_path": db_label,
    }


@app.get("/api/system/agent-runs")
async def agent_runs(limit: int = 50):
    runner = get_runner()
    return {"runs": await runner.db.get_agent_runs(limit)}


# --- Alerts (Phase B) ---

@app.get("/api/alerts/status")
async def telegram_status():
    runner = get_runner()
    connected = bool(settings.telegram_chat_id and settings.telegram_bot_token)
    bot_username = None
    if runner.bot is not None:
        try:
            bot_username = runner.bot.app.bot.username
        except Exception:  # noqa: BLE001 — username unavailable until the bot is initialized
            bot_username = None
    return {
        "connected": connected,
        "chat_id": settings.telegram_chat_id or None,
        "bot_username": bot_username,
    }


@app.get("/api/alerts/rules")
async def get_alert_rules():
    rules = await get_runner().db.get_all_alert_rules()
    return {"rules": [r.model_dump(mode="json") for r in rules]}


@app.post("/api/alerts/rules")
async def create_alert_rule(rule_data: dict):
    from stockstalker.schemas import AlertRule

    try:
        rule = AlertRule(**rule_data)
    except (ValidationError, TypeError) as exc:
        raise HTTPException(400, f"Invalid rule: {exc}")
    rule_id = await get_runner().db.add_alert_rule(rule)
    return {"success": True, "rule_id": rule_id}


@app.delete("/api/alerts/rules/{rule_id}")
async def delete_alert_rule(rule_id: int):
    await get_runner().db.deactivate_alert_rule(rule_id)
    return {"success": True}


@app.post("/api/alerts/test")
async def send_test_notification():
    runner = get_runner()
    if runner.bot is None:
        return {
            "success": False,
            "message": "Telegram bot not initialized (set bot token + chat ID, then restart the API).",
        }
    if not settings.telegram_chat_id:
        return {"success": False, "message": "No Telegram chat connected yet."}
    try:
        await runner.bot.send_message("🤖 StockStalker test notification — connection working!")
        return {"success": True, "message": "Test notification sent"}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "message": f"Send failed: {exc}"}


@app.patch("/api/alerts/rules/{rule_id}")
async def update_alert_rule(rule_id: int, payload: dict):
    active = bool(payload.get("is_active", True))
    await get_runner().db.set_alert_rule_active(rule_id, active)
    return {"success": True}


@app.get("/api/alerts/events")
async def get_alert_events():
    events = await get_runner().db.get_recent_alert_events(limit=20)
    return {"events": events}


# --- MCP (Phase C) ---

async def _probe_tcp(host: str, port: int, timeout: float = 0.5) -> bool:
    """Best-effort TCP connect to detect whether something is listening on host:port."""
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass
        return True
    except Exception:  # noqa: BLE001
        return False


async def _list_mcp_tools() -> list[dict]:
    """Real registered MCP tools (name + one-line brief) from the mcp instance."""
    try:
        from stockstalker.integrations.mcp_server import mcp

        tools = await mcp.list_tools()
        result = []
        for t in tools:
            desc = (getattr(t, "description", "") or "").strip()
            brief = next((ln.strip() for ln in desc.splitlines() if ln.strip()), "")
            result.append({"name": t.name, "description": brief})
        return result
    except Exception as exc:  # noqa: BLE001 — never let tool listing break the endpoint
        logger.warning("MCP tool listing failed: {}", exc)
        return []


@app.get("/api/mcp/status")
async def mcp_status():
    host = settings.mcp_server_host
    port = settings.mcp_server_port
    # The MCP server runs as a SEPARATE process — probe the port to detect it.
    probe_host = "127.0.0.1" if host in ("0.0.0.0", "") else host
    return {
        "running": await _probe_tcp(probe_host, port),
        "host": host,
        "port": port,
        "url": f"http://{host}:{port}/mcp",
        "tools": await _list_mcp_tools(),
    }


@app.get("/api/mcp/calls")
async def mcp_recent_calls():
    # The MCP server runs as a separate process, so the API cannot observe its
    # tool calls. Always empty here until cross-process call logging is added.
    return {"calls": []}


# --- Background job helpers ---

async def _run_job(job_id: str, symbol: str):
    with _jobs_lock:
        _jobs[job_id]["status"] = "running"
    try:
        await get_runner().analyze_ticker(symbol)
        recent = await get_runner().db.get_recent_analyses(symbol, days=1)
        latest = recent[0] if recent else None
        with _jobs_lock:
            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["result"] = latest
    except Exception as e:  # noqa: BLE001 — surface failure via job status, never crash the loop
        logger.error("Refresh job failed for {}: {}", symbol, e)
        with _jobs_lock:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["result"] = {"error": str(e)}
