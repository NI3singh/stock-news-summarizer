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
        from quantmind.integrations.mcp_server import mcp

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


# --- ML signals (Phase D) ---

def _signal_accuracy(df) -> dict:
    """Directional accuracy of sentiment signals vs the actual next-day move."""

    def bucket(mask, correct_mask) -> dict:
        occ = int(mask.sum())
        cor = int((mask & correct_mask).sum())
        return {"occurrences": occ, "correct": cor, "accuracy": round(cor / occ, 4) if occ else None}

    s = df["sentiment_score"].fillna(0)
    ret = df["next_day_return"]
    pos = s > 0.3
    neg = s < -0.3
    neu = ~pos & ~neg
    return {
        "positive": bucket(pos, ret > 0),
        "negative": bucket(neg, ret < 0),
        "neutral": bucket(neu, ret.abs() < 1.0),
    }


def _corr_label_interp(corr, n: int, accuracy: dict | None) -> tuple[str, str]:
    if corr is None:
        return (
            "Insufficient data",
            f"Not enough varied samples to compute a correlation ({n} points).",
        )
    a = abs(corr)
    strength = (
        "Negligible" if a < 0.2
        else "Weak" if a < 0.4
        else "Moderate" if a < 0.6
        else "Strong" if a < 0.8
        else "Very Strong"
    )
    sign = "Positive" if corr > 0 else "Negative"
    pos = (accuracy or {}).get("positive") or {}
    pct = f"{pos['accuracy'] * 100:.0f}%" if pos.get("accuracy") is not None else "n/a"
    interp = (
        f"Sentiment shows a {strength.lower()} {sign.lower()} correlation (r={corr:+.2f}) with "
        f"next-day returns over {n} samples. Positive-sentiment days were followed by gains {pct} of the time."
    )
    return f"{strength} {sign}", interp


async def _train_model_bg(ticker: str) -> None:
    try:
        from quantmind.ml.model import SignalModel

        result = await SignalModel(ticker).train(get_runner().db)
        logger.info("[ML] train {} -> {}", ticker, result.get("status"))
    except Exception as exc:  # noqa: BLE001
        logger.error("[ML] training failed for {}: {}", ticker, exc)


@app.get("/api/ml/status")
async def ml_status():
    import json

    from quantmind.ml.model import MODEL_SAVE_DIR

    runner = get_runner()
    tickers = await runner.db.get_active_tickers()
    models = []
    for t in tickers:
        analyses = await runner.db.get_all_analyses(t)
        meta: dict = {}
        metrics_file = MODEL_SAVE_DIR / f"{t}_metrics.json"
        if metrics_file.exists():
            try:
                meta = json.loads(metrics_file.read_text())
            except Exception:  # noqa: BLE001
                meta = {}
        models.append(
            {
                "ticker": t,
                "trained": (MODEL_SAVE_DIR / f"{t}_model.joblib").exists(),
                "analyses_count": len(analyses),
                "trained_at": meta.get("trained_at"),
                "cv_accuracy": meta.get("cv_accuracy_mean"),
                "samples_trained": meta.get("samples_trained"),
                "beats_baseline": meta.get("beats_baseline"),
            }
        )
    return {
        "models": models,
        "trained_count": sum(1 for m in models if m["trained"]),
        "total": len(models),
    }


@app.get("/api/ml/correlation/{ticker}")
async def ml_correlation(ticker: str, days: int = 30):
    import pandas as pd

    from quantmind.ml.data_collector import MLDataCollector

    ticker = ticker.upper()
    df = await MLDataCollector(get_runner().db).collect_training_data(ticker, min_samples=1)
    if df.empty:
        return {
            "ticker": ticker,
            "days": days,
            "sample_count": 0,
            "samples": [],
            "correlation": None,
            "correlation_label": "No data",
            "interpretation": "No analyses with matching price data yet.",
            "accuracy": None,
        }

    df["_d"] = pd.to_datetime(df["analysis_date"])
    cutoff = df["_d"].max() - pd.Timedelta(days=days)
    fdf = df[df["_d"] >= cutoff]
    if fdf.empty:
        fdf = df

    samples = []
    for _, row in fdf.iterrows():
        sval = row["sentiment_score"]
        samples.append(
            {
                "date": row["analysis_date"],
                "sentiment_score": None if pd.isna(sval) else round(float(sval), 4),
                "next_day_return_pct": round(float(row["next_day_return"]), 4),
            }
        )

    corr = None
    if (
        len(fdf) >= 2
        and fdf["sentiment_score"].nunique() > 1
        and fdf["next_day_return"].nunique() > 1
    ):
        c = float(fdf["sentiment_score"].corr(fdf["next_day_return"]))
        corr = None if pd.isna(c) else c

    accuracy = _signal_accuracy(fdf)
    label, interp = _corr_label_interp(corr, len(fdf), accuracy)
    return {
        "ticker": ticker,
        "days": days,
        "sample_count": int(len(fdf)),
        "samples": samples,
        "correlation": round(corr, 4) if corr is not None else None,
        "correlation_label": label,
        "interpretation": interp,
        "accuracy": accuracy,
    }


@app.post("/api/ml/train")
async def trigger_ml_training(payload: dict | None = None):
    ticker = (payload or {}).get("ticker") if isinstance(payload, dict) else None
    if not ticker:
        raise HTTPException(400, "ticker is required")
    asyncio.create_task(_train_model_bg(ticker.upper()))
    return {"success": True, "message": f"Training started for {ticker.upper()} (check back in ~30s)"}


@app.get("/api/ml/entity-graph")
async def entity_graph(ticker: str | None = None):
    data = await get_runner().db.get_entity_graph(ticker.upper() if ticker else None)
    nodes = [
        {"name": n["id"], "type": n["type"], "mention_count": n["weight"]}
        for n in data["nodes"]
    ]
    edges = [
        {
            "source": e["source"],
            "target": e["target"],
            "type": e["relationship"],
            "confidence": e["confidence"],
            "count": e["weight"],
        }
        for e in data["edges"]
    ]
    type_counts: dict = {}
    for node in nodes:
        type_counts[node["type"]] = type_counts.get(node["type"], 0) + 1
    degree: dict = {}
    for e in edges:
        degree[e["source"]] = degree.get(e["source"], 0) + 1
        degree[e["target"]] = degree.get(e["target"], 0) + 1
    most_connected = sorted(degree.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return {
        "ticker": ticker.upper() if ticker else None,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "entity_types": type_counts,
        "most_connected": [{"entity": e, "degree": d} for e, d in most_connected],
    }


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
