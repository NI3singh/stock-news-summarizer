"""QuantMind v2 — REST API layer (FastAPI).

Exposes the CLI pipeline over HTTP so the Next.js frontend can drive it. A single
long-lived ``PipelineRunner`` is created once in the lifespan handler and reused
for every request (heavy resources — Chroma, LangChain, scrapers — built once).

Run with:  ``python quantmind/main.py api``  (or ``quantmind api``) → port 8000.
"""
import asyncio
import uuid
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

from quantmind.config import settings
from quantmind.utils import logger

# --- Shared state ---
_runner = None
_jobs: dict = {}
_jobs_lock = Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _runner
    from quantmind.pipeline import PipelineRunner

    _runner = PipelineRunner()
    await _runner.initialize()
    # ML (prediction + entity extraction) is auto-enabled inside the
    # OrchestratorAgent constructor, so there is no separate enable step.
    # Enable Telegram if creds are set (no-op otherwise) + initialize the bot's
    # HTTP client so /api/alerts/test can send. Guarded so a bad/unreachable
    # token can't crash API startup.
    _runner.enable_telegram()
    if _runner.bot is not None:
        try:
            await _runner.bot.app.initialize()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Telegram bot init failed ({}); send disabled.", exc)
            _runner.bot = None
    logger.info("QuantMind API started")
    yield
    if _runner.bot is not None:
        try:
            await _runner.bot.app.shutdown()
        except Exception:  # noqa: BLE001
            pass
    logger.info("QuantMind API shutting down")


app = FastAPI(title="QuantMind API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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


# --- Routes ---

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/api/tickers")
async def get_tickers():
    tickers = await get_runner().db.get_active_tickers()
    return {"success": True, "tickers": tickers}


@app.post("/api/tickers")
async def add_ticker(req: AddTickerRequest, background_tasks: BackgroundTasks):
    symbol = req.symbol.strip().upper()
    if not symbol or len(symbol) > 10:
        raise HTTPException(400, "Invalid symbol")
    success = await get_runner().db.add_ticker(symbol)
    if not success:
        raise HTTPException(400, f"{symbol} already exists")
    background_tasks.add_task(_run_analysis_bg, symbol)
    return {"success": True, "message": f"{symbol} added. Processing..."}


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
    return {
        "tickers": len(tickers),
        "vector_store_size": vs_size,
        "scheduler_time": f"{settings.refresh_time} {settings.timezone}",
        "db_path": runner.db.db_path,
    }


@app.get("/api/system/agent-runs")
async def agent_runs(limit: int = 50):
    runner = get_runner()
    import aiosqlite

    async with aiosqlite.connect(runner.db.db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM agent_runs ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = [dict(r) for r in await cur.fetchall()]
    return {"runs": rows}


# --- Alerts (Phase B) ---

@app.get("/api/alerts/status")
async def telegram_status():
    connected = bool(settings.telegram_chat_id and settings.telegram_bot_token)
    return {"connected": connected, "chat_id": settings.telegram_chat_id or None}


@app.get("/api/alerts/rules")
async def get_alert_rules():
    rules = await get_runner().db.get_active_alert_rules()
    return {"rules": [r.model_dump(mode="json") for r in rules]}


@app.post("/api/alerts/rules")
async def create_alert_rule(rule_data: dict):
    from quantmind.schemas import AlertRule

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
        await runner.bot.send_message("🤖 QuantMind test notification — connection working!")
        return {"success": True, "message": "Test notification sent"}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "message": f"Send failed: {exc}"}


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


async def _run_analysis_bg(symbol: str):
    """Fire-and-forget analysis for a freshly-added ticker (errors are logged)."""
    try:
        await get_runner().analyze_ticker(symbol)
    except Exception as e:  # noqa: BLE001 — background task; just log
        logger.error("Background analysis failed for {}: {}", symbol, e)
