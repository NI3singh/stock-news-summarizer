"""QuantMind v2 — async SQLite persistence layer (aiosqlite).

A thin, connection-per-operation data layer: no persistent connection is held —
every method opens its own ``aiosqlite.connect(...)`` context and commits its own
writes. All SQL is restricted to the portable subset shared by SQLite and
PostgreSQL (no ``AUTOINCREMENT``, no SQLite-specific date functions) so the
schema can migrate later. Date filtering is done with Python-computed cutoffs
compared against ISO-8601 timestamp strings.
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone

import aiosqlite

from quantmind.config import settings
from quantmind.schemas import Article, TickerAnalysis
from quantmind.utils import logger


def _utcnow_naive() -> datetime:
    """Current UTC time as a naive datetime (avoids the utcnow() deprecation)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_naive_iso(dt: datetime) -> str:
    """Serialise a datetime to a sortable, naive-UTC ISO-8601 string."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat()


# Portable DDL — INTEGER PRIMARY KEY (no AUTOINCREMENT), CURRENT_TIMESTAMP only.
_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS tickers (
        id INTEGER PRIMARY KEY,
        symbol TEXT UNIQUE NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY,
        ticker TEXT NOT NULL,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        published_at TEXT,
        content TEXT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_selected INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY,
        ticker TEXT NOT NULL,
        analyzed_at TIMESTAMP NOT NULL,
        news_summary TEXT,
        what_changed TEXT,
        quant_interpretation TEXT,
        final_synthesis TEXT,
        sentiment_score REAL,
        articles_used TEXT,
        memory_context TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_runs (
        id INTEGER PRIMARY KEY,
        ticker TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration_seconds REAL,
        success INTEGER DEFAULT 1,
        error_message TEXT
    )
    """,
]


class DatabaseManager:
    """Async data-access layer over a SQLite database file."""

    def __init__(self, db_path: str = settings.db_path) -> None:
        # Store only the path — connections are opened per operation.
        self.db_path = db_path

    async def init_db(self) -> None:
        """Create all tables if they do not already exist."""
        async with aiosqlite.connect(self.db_path) as db:
            for statement in _SCHEMA:
                await db.execute(statement)
            await db.commit()
        logger.debug("Database initialised at {}", self.db_path)

    async def add_ticker(self, symbol: str) -> bool:
        """Insert a ticker. Returns False if it already exists."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("INSERT INTO tickers (symbol) VALUES (?)", (symbol,))
                await db.commit()
            except sqlite3.IntegrityError:
                logger.debug("Ticker {} already exists", symbol)
                return False
        logger.debug("Ticker {} added", symbol)
        return True

    async def get_active_tickers(self) -> list[str]:
        """Return all active ticker symbols, oldest first."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT symbol FROM tickers WHERE is_active = 1 ORDER BY id"
            ) as cursor:
                rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def deactivate_ticker(self, symbol: str) -> None:
        """Soft-delete a ticker (set is_active = 0)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE tickers SET is_active = 0 WHERE symbol = ?", (symbol,)
            )
            await db.commit()
        logger.debug("Ticker {} deactivated", symbol)

    async def save_article(self, article: Article) -> None:
        """Persist a single scraped article."""
        published = article.published_at.isoformat() if article.published_at else None
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO articles (ticker, source, title, url, published_at, content)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    article.ticker,
                    article.source,
                    article.title,
                    article.url,
                    published,
                    article.content,
                ),
            )
            await db.commit()

    async def save_analysis(self, ticker: str, analysis: TickerAnalysis) -> None:
        """Persist a full TickerAnalysis, serialising sub-objects to JSON strings."""
        articles_used = json.dumps(
            [a.model_dump(mode="json") for a in analysis.news.selected_articles]
        )
        memory_context = analysis.memory.model_dump_json()
        quant_interpretation = analysis.quant.interpretation if analysis.quant else None
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO analyses (
                    ticker, analyzed_at, news_summary, what_changed,
                    quant_interpretation, final_synthesis, sentiment_score,
                    articles_used, memory_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticker,
                    _to_naive_iso(analysis.analyzed_at),
                    analysis.news.summary,
                    analysis.news.what_changed,
                    quant_interpretation,
                    analysis.final_synthesis,
                    analysis.news.sentiment_score,
                    articles_used,
                    memory_context,
                ),
            )
            await db.commit()
        logger.debug("Analysis saved for {}", ticker)

    async def get_recent_analyses(self, ticker: str, days: int = 7) -> list[dict]:
        """Return analyses for a ticker within the last ``days``, newest first."""
        cutoff = (_utcnow_naive() - timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM analyses
                WHERE ticker = ? AND analyzed_at >= ?
                ORDER BY analyzed_at DESC
                """,
                (ticker, cutoff),
            ) as cursor:
                rows = await cursor.fetchall()

        results: list[dict] = []
        for row in rows:
            record = dict(row)
            # Best-effort: decode JSON columns back into Python structures.
            for col in ("articles_used", "memory_context"):
                if record.get(col):
                    try:
                        record[col] = json.loads(record[col])
                    except (ValueError, TypeError):
                        pass
            results.append(record)
        return results

    async def log_agent_run(
        self,
        ticker: str,
        agent_name: str,
        duration: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Record one agent execution for observability."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO agent_runs (ticker, agent_name, duration_seconds, success, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ticker, agent_name, duration, int(success), error),
            )
            await db.commit()
        logger.debug(
            "agent_run logged: {}/{} ({}s, success={})",
            ticker,
            agent_name,
            duration,
            success,
        )
