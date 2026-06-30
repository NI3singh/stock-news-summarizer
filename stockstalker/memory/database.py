"""StockStalker v2 — async persistence layer (SQLAlchemy 2.0 Core).

Runs on BOTH backends, chosen at runtime by ``settings.db_url``:
  • SQLite (local dev, default)        → sqlite+aiosqlite:///./stockstalker.db
  • PostgreSQL / Supabase (deploy)     → postgresql+asyncpg://...  (set DATABASE_URL)

Storage stays in the portable subset so semantics are identical on both engines:
timestamps as ISO-8601 strings, nested data as JSON strings, booleans as 0/1 ints.
One engine is cached per URL; ``NullPool`` opens a fresh connection per operation —
this matches the original connection-per-op design and is what the Supabase /
PgBouncer transaction pooler needs (no server-side state reused across ops).
"""
import json
import ssl
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    delete,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from stockstalker.config import settings
from stockstalker.schemas import AlertEvent, AlertRule, Article, TickerAnalysis
from stockstalker.utils import logger


def _utcnow_naive() -> datetime:
    """Current UTC time as a naive datetime (avoids the utcnow() deprecation)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_naive_iso(dt: datetime) -> str:
    """Serialise a datetime to a sortable, naive-UTC ISO-8601 string."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat()


def _now_iso() -> str:
    """ISO-8601 'now' — Python-side default for the old CURRENT_TIMESTAMP columns."""
    return _utcnow_naive().isoformat()


# --- Schema (SQLAlchemy Core; create_all emits dialect-correct DDL for each engine,
#     incl. auto-increment PKs as SERIAL/IDENTITY on Postgres, INTEGER on SQLite) ---
metadata = MetaData()

tickers_t = Table(
    "tickers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False, default=""),
    # NOT globally unique anymore — uniqueness is per (user_id, symbol), enforced
    # in add_ticker() so two different users can each track the same ticker.
    Column("symbol", String, nullable=False),
    Column("added_at", String, default=_now_iso),
    Column("is_active", Integer, default=1),
)

articles_t = Table(
    "articles",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ticker", String, nullable=False),
    Column("source", String, nullable=False),
    Column("title", String, nullable=False),
    Column("url", String, nullable=False),
    Column("published_at", String),
    Column("content", Text),
    Column("fetched_at", String, default=_now_iso),
    Column("is_selected", Integer, default=0),
)

analyses_t = Table(
    "analyses",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False, default=""),
    Column("ticker", String, nullable=False),
    Column("analyzed_at", String, nullable=False),
    Column("news_summary", Text),
    Column("what_changed", Text),
    Column("quant_interpretation", Text),
    Column("final_synthesis", Text),
    Column("sentiment_score", Float),
    Column("articles_used", Text),
    Column("memory_context", Text),
    Column("key_themes", Text),
    Column("technical_signals", Text),
    Column("composite_sentiment", Float),
    Column("market_data", Text),
)

agent_runs_t = Table(
    "agent_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False, default=""),
    Column("ticker", String, nullable=False),
    Column("agent_name", String, nullable=False),
    Column("started_at", String, default=_now_iso),
    Column("duration_seconds", Float),
    Column("success", Integer, default=1),
    Column("error_message", Text),
)

alert_rules_t = Table(
    "alert_rules",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False, default=""),
    Column("ticker", String),
    Column("condition_type", String, nullable=False),
    Column("threshold", Float),
    Column("is_active", Integer, default=1),
    Column("created_at", String, default=_now_iso),
    Column("last_triggered_at", String),
    Column("delivery_channel", String, default="telegram"),
)

alert_events_t = Table(
    "alert_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False, default=""),
    Column("rule_id", Integer, nullable=False),
    Column("ticker", String, nullable=False),
    Column("triggered_at", String, default=_now_iso),
    Column("message", Text),
    Column("delivered", Integer, default=0),
)


# Idempotent ALTERs for pre-existing tables (create_all won't alter existing ones).
# Each runs in its own transaction; a "duplicate column" error is caught + ignored.
_MIGRATIONS = [
    "ALTER TABLE analyses ADD COLUMN composite_sentiment FLOAT",
    "ALTER TABLE analyses ADD COLUMN market_data TEXT",
    # Multi-tenancy: add user_id to the per-user tables (idempotent). Pre-existing
    # rows default to '' (unowned) — users start with a fresh, private watchlist.
    "ALTER TABLE tickers ADD COLUMN user_id VARCHAR DEFAULT ''",
    "ALTER TABLE analyses ADD COLUMN user_id VARCHAR DEFAULT ''",
    "ALTER TABLE agent_runs ADD COLUMN user_id VARCHAR DEFAULT ''",
    "ALTER TABLE alert_rules ADD COLUMN user_id VARCHAR DEFAULT ''",
    "ALTER TABLE alert_events ADD COLUMN user_id VARCHAR DEFAULT ''",
    # The old global UNIQUE(symbol) blocks two users tracking the same ticker; drop
    # it (Postgres auto-named it tickers_symbol_key). Uniqueness is now (user_id,
    # symbol), enforced in add_ticker(). No-op on SQLite (caught + ignored).
    "ALTER TABLE tickers DROP CONSTRAINT IF EXISTS tickers_symbol_key",
]


# --- Engine cache (one per URL; loop-agnostic because NullPool holds no connections) ---
_engines: dict[str, AsyncEngine] = {}


def _pg_ssl_context() -> ssl.SSLContext:
    """TLS context for Supabase. Encrypts but does NOT verify the chain — some
    networks (corporate MITM proxies, incomplete CA bundles) inject a self-signed
    cert that breaks verification. The connection is still encrypted."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _make_engine(url: str) -> AsyncEngine:
    if url.startswith("postgresql"):
        # asyncpg over the Supabase pooler: TLS + disable the prepared-statement
        # cache (PgBouncer transaction mode can't reuse them).
        return create_async_engine(
            url,
            poolclass=NullPool,
            connect_args={"ssl": _pg_ssl_context(), "statement_cache_size": 0},
        )
    return create_async_engine(url, poolclass=NullPool)


def _get_engine(url: str) -> AsyncEngine:
    eng = _engines.get(url)
    if eng is None:
        eng = _make_engine(url)
        _engines[url] = eng
    return eng


def _normalize_url(value: str) -> str:
    """A bare file path → sqlite URL; an existing URL is returned unchanged."""
    v = value.strip()
    return v if "://" in v else f"sqlite+aiosqlite:///{v}"


class DatabaseManager:
    """Async data-access layer over SQLite (dev) or PostgreSQL/Supabase (prod)."""

    def __init__(self, db_url: str | None = None, db_path: str | None = None) -> None:
        # ``db_path`` kept for backward compatibility (a bare file path → sqlite URL).
        target = db_url or db_path
        self.db_url = _normalize_url(target) if target else settings.db_url

    @property
    def _engine(self) -> AsyncEngine:
        return _get_engine(self.db_url)

    @property
    def db_path(self) -> str:
        """SQLite file path (compat for tests that open a raw aiosqlite connection)."""
        return self.db_url.split(":///", 1)[-1] if self.db_url.startswith("sqlite") else self.db_url

    async def init_db(self) -> None:
        """Create all tables if they do not already exist (idempotent)."""
        async with self._engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
        # Idempotent column additions for pre-existing tables (each in its own
        # transaction so a "column already exists" error can't poison the rest).
        for statement in _MIGRATIONS:
            try:
                async with self._engine.begin() as conn:
                    await conn.execute(text(statement))
            except Exception:  # noqa: BLE001 — column already exists
                pass
        logger.debug("Database initialised ({})", self.db_url.split("@")[-1])

    async def add_ticker(self, user_id: str, symbol: str) -> bool:
        """Add a ticker to a user's watchlist. Returns False if they already track it
        (active); reactivates a previously-removed one instead of duplicating."""
        async with self._engine.begin() as conn:
            row = (
                await conn.execute(
                    select(tickers_t.c.id, tickers_t.c.is_active).where(
                        tickers_t.c.user_id == user_id,
                        tickers_t.c.symbol == symbol,
                    )
                )
            ).first()
            if row is not None:
                if row.is_active == 1:
                    logger.debug("Ticker {} already tracked by {}", symbol, user_id)
                    return False
                await conn.execute(
                    update(tickers_t).where(tickers_t.c.id == row.id).values(is_active=1)
                )
                logger.debug("Ticker {} reactivated for {}", symbol, user_id)
                return True
            await conn.execute(insert(tickers_t).values(user_id=user_id, symbol=symbol))
        logger.debug("Ticker {} added for {}", symbol, user_id)
        return True

    async def get_active_tickers(self, user_id: str) -> list[str]:
        """Return a user's active ticker symbols, oldest first."""
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(tickers_t.c.symbol)
                    .where(tickers_t.c.user_id == user_id, tickers_t.c.is_active == 1)
                    .order_by(tickers_t.c.id)
                )
            ).all()
        return [r[0] for r in rows]

    async def get_all_active_tickers(self) -> list[tuple[str, str]]:
        """Return (user_id, symbol) for EVERY active ticker across all users — used by
        the scheduler to refresh everyone's watchlist."""
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(tickers_t.c.user_id, tickers_t.c.symbol)
                    .where(tickers_t.c.is_active == 1)
                    .order_by(tickers_t.c.id)
                )
            ).all()
        return [(r[0], r[1]) for r in rows]

    async def deactivate_ticker(self, user_id: str, symbol: str) -> None:
        """Soft-delete a ticker from a user's watchlist (set is_active = 0)."""
        async with self._engine.begin() as conn:
            await conn.execute(
                update(tickers_t)
                .where(tickers_t.c.user_id == user_id, tickers_t.c.symbol == symbol)
                .values(is_active=0)
            )
        logger.debug("Ticker {} deactivated for {}", symbol, user_id)

    async def save_article(self, article: Article) -> None:
        """Persist a single scraped article."""
        published = article.published_at.isoformat() if article.published_at else None
        async with self._engine.begin() as conn:
            await conn.execute(
                insert(articles_t).values(
                    ticker=article.ticker,
                    source=article.source,
                    title=article.title,
                    url=article.url,
                    published_at=published,
                    content=article.content,
                )
            )

    async def save_analysis(self, user_id: str, ticker: str, analysis: TickerAnalysis) -> None:
        """Persist a full TickerAnalysis for a user, serialising sub-objects to JSON."""
        articles_used = json.dumps(
            [a.model_dump(mode="json") for a in analysis.news.selected_articles]
        )
        memory_context = analysis.memory.model_dump_json()
        quant_interpretation = analysis.quant.interpretation if analysis.quant else None
        key_themes = json.dumps(analysis.news.key_themes)
        technical_signals = (
            json.dumps(analysis.quant.signals.model_dump(mode="json"))
            if analysis.quant
            else None
        )
        market_data = (
            json.dumps(analysis.quant.market.model_dump(mode="json"))
            if analysis.quant and analysis.quant.market
            else None
        )
        async with self._engine.begin() as conn:
            await conn.execute(
                insert(analyses_t).values(
                    user_id=user_id,
                    ticker=ticker,
                    analyzed_at=_to_naive_iso(analysis.analyzed_at),
                    news_summary=analysis.news.summary,
                    what_changed=analysis.news.what_changed,
                    quant_interpretation=quant_interpretation,
                    final_synthesis=analysis.final_synthesis,
                    sentiment_score=analysis.news.sentiment_score,
                    articles_used=articles_used,
                    memory_context=memory_context,
                    key_themes=key_themes,
                    technical_signals=technical_signals,
                    composite_sentiment=analysis.news.composite_sentiment,
                    market_data=market_data,
                )
            )
        logger.debug("Analysis saved for {}", ticker)

    async def get_all_analyses(self, user_id: str, ticker: str) -> list[dict]:
        """Return ALL of a user's analyses for a ticker, oldest first."""
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(
                        analyses_t.c.id,
                        analyses_t.c.ticker,
                        analyses_t.c.analyzed_at,
                        analyses_t.c.sentiment_score,
                        analyses_t.c.quant_interpretation,
                        analyses_t.c.final_synthesis,
                    )
                    .where(analyses_t.c.user_id == user_id, analyses_t.c.ticker == ticker)
                    .order_by(analyses_t.c.analyzed_at.asc())
                )
            ).mappings().all()
        return [dict(r) for r in rows]

    async def get_recent_analyses(self, user_id: str, ticker: str, days: int = 7) -> list[dict]:
        """Return a user's analyses for a ticker within the last ``days``, newest first."""
        cutoff = (_utcnow_naive() - timedelta(days=days)).isoformat()
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(analyses_t)
                    .where(
                        analyses_t.c.user_id == user_id,
                        analyses_t.c.ticker == ticker,
                        analyses_t.c.analyzed_at >= cutoff,
                    )
                    .order_by(analyses_t.c.analyzed_at.desc())
                )
            ).mappings().all()

        results: list[dict] = []
        for row in rows:
            record = dict(row)
            # Best-effort: decode JSON columns back into Python structures.
            for col in ("articles_used", "memory_context", "key_themes", "technical_signals", "market_data"):
                if record.get(col):
                    try:
                        record[col] = json.loads(record[col])
                    except (ValueError, TypeError):
                        pass
            results.append(record)
        return results

    async def log_agent_run(
        self,
        user_id: str,
        ticker: str,
        agent_name: str,
        duration: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Record one agent execution for observability."""
        async with self._engine.begin() as conn:
            await conn.execute(
                insert(agent_runs_t).values(
                    user_id=user_id,
                    ticker=ticker,
                    agent_name=agent_name,
                    duration_seconds=duration,
                    success=int(success),
                    error_message=error,
                )
            )
        logger.debug(
            "agent_run logged: {}/{} ({}s, success={})",
            ticker,
            agent_name,
            duration,
            success,
        )

    async def get_agent_runs(self, user_id: str, limit: int = 50) -> list[dict]:
        """Return a user's most recent agent runs (newest first) — for the dashboard."""
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(agent_runs_t)
                    .where(agent_runs_t.c.user_id == user_id)
                    .order_by(agent_runs_t.c.id.desc())
                    .limit(limit)
                )
            ).mappings().all()
        return [dict(r) for r in rows]

    # --- Alert rules / events (Phase B.4) ------------------------------------

    async def add_alert_rule(self, rule: AlertRule) -> int:
        """Insert an alert rule; return the new row id."""
        async with self._engine.begin() as conn:
            result = await conn.execute(
                insert(alert_rules_t).values(
                    user_id=rule.user_id,
                    ticker=rule.ticker,
                    condition_type=rule.condition_type.value,
                    threshold=rule.threshold,
                    is_active=int(rule.is_active),
                    last_triggered_at=_to_naive_iso(rule.last_triggered_at)
                    if rule.last_triggered_at
                    else None,
                    delivery_channel=rule.delivery_channel,
                )
            )
            new_id = result.inserted_primary_key[0]
        logger.debug("alert_rule added: id={} ({})", new_id, rule.condition_type.value)
        return new_id

    async def get_active_alert_rules(self, user_id: str) -> list[AlertRule]:
        """Return a user's active alert rules as AlertRule objects."""
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(alert_rules_t)
                    .where(
                        alert_rules_t.c.is_active == 1,
                        alert_rules_t.c.user_id == user_id,
                    )
                    .order_by(alert_rules_t.c.id)
                )
            ).mappings().all()
        return [AlertRule(**dict(r)) for r in rows]

    async def update_alert_last_triggered(self, rule_id: int) -> None:
        """Stamp an alert rule's last_triggered_at to now."""
        async with self._engine.begin() as conn:
            await conn.execute(
                update(alert_rules_t)
                .where(alert_rules_t.c.id == rule_id)
                .values(last_triggered_at=_now_iso())
            )

    async def delete_alert_rule(self, user_id: str, rule_id: int) -> None:
        """Permanently delete one of a user's alert rules (hard delete). Disabling
        without deleting is a separate action — see set_alert_rule_active()."""
        async with self._engine.begin() as conn:
            await conn.execute(
                delete(alert_rules_t).where(
                    alert_rules_t.c.id == rule_id,
                    alert_rules_t.c.user_id == user_id,
                )
            )

    async def get_all_alert_rules(self, user_id: str) -> list[AlertRule]:
        """Return ALL of a user's alert rules (active + inactive), newest first."""
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(alert_rules_t)
                    .where(alert_rules_t.c.user_id == user_id)
                    .order_by(alert_rules_t.c.id.desc())
                )
            ).mappings().all()
        return [AlertRule(**dict(r)) for r in rows]

    async def set_alert_rule_active(self, user_id: str, rule_id: int, active: bool) -> None:
        """Activate / pause one of a user's alert rules (toggle is_active)."""
        async with self._engine.begin() as conn:
            await conn.execute(
                update(alert_rules_t)
                .where(
                    alert_rules_t.c.id == rule_id,
                    alert_rules_t.c.user_id == user_id,
                )
                .values(is_active=int(active))
            )

    async def get_recent_alert_events(self, user_id: str, limit: int = 20) -> list[dict]:
        """Return a user's most recently triggered alert events (newest first)."""
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(alert_events_t)
                    .where(alert_events_t.c.user_id == user_id)
                    .order_by(alert_events_t.c.triggered_at.desc())
                    .limit(limit)
                )
            ).mappings().all()
        return [dict(r) for r in rows]

    async def log_alert_event(self, event: AlertEvent) -> None:
        """Persist a fired alert event."""
        async with self._engine.begin() as conn:
            await conn.execute(
                insert(alert_events_t).values(
                    user_id=event.user_id,
                    rule_id=event.rule_id,
                    ticker=event.ticker,
                    message=event.message,
                    delivered=int(event.delivered),
                )
            )
