"""StockStalker v2 — vector store (pgvector on Postgres / brute-force on SQLite).

Stores article embeddings in the SAME database the rest of the app uses
(``settings.db_url``), so a Supabase deployment keeps everything in one place:
  • PostgreSQL / Supabase → a ``vector`` column + pgvector's ``<=>`` cosine search.
  • SQLite (local dev)     → embeddings as JSON text + an in-Python cosine scan.

Embeddings are produced by Gemini ``gemini-embedding-001`` (768-dim) — no local
embedding model is shipped, which keeps the deployable image small. Blocking calls
(the embedding HTTP request) are offloaded to a worker thread via ``to_thread``.
"""
import asyncio
import hashlib
import json
import math

from sqlalchemy import text

from stockstalker.config import settings
from stockstalker.memory.database import _get_engine, _normalize_url
from stockstalker.schemas import Article
from stockstalker.utils import logger

EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768


def _embed_sync(texts: list[str], task_type: str) -> list[list[float]]:
    """Synchronously embed texts with Gemini (run off-thread by the callers).

    Uses langchain-google-genai — the same supported client the LLM layer uses.
    (The legacy ``google.generativeai`` package is deprecated and its embed
    endpoint rejects plain API-key auth.)
    """
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    # output_dimensionality is REQUIRED: gemini-embedding-001 defaults to 3072 dims,
    # but the pgvector column (and the SQLite JSON path) are sized to EMBED_DIM. Without
    # this, every insert/query silently fails on Postgres with a dimension mismatch.
    # Cosine search (pgvector '<=>' and the Python _cosine) is scale-invariant, so the
    # truncated (un-normalized) Matryoshka vectors need no extra normalization.
    embedder = GoogleGenerativeAIEmbeddings(
        model=EMBED_MODEL,
        google_api_key=settings.gemini_api_key,
        output_dimensionality=EMBED_DIM,
    )
    if task_type == "retrieval_query":
        return [embedder.embed_query(t) for t in texts]
    return embedder.embed_documents(texts)


async def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    return await asyncio.to_thread(_embed_sync, texts, task_type)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _pgvector_literal(emb: list[float]) -> str:
    """pgvector text input form, e.g. '[0.1,0.2,...]'."""
    return "[" + ",".join(map(str, emb)) + "]"


class VectorStore:
    """Async embedding store backed by the configured DB (pgvector or SQLite)."""

    def __init__(self, db_url: str | None = None) -> None:
        self.db_url = _normalize_url(db_url) if db_url else settings.db_url
        self._is_pg = self.db_url.startswith("postgresql")
        self._ready = False

    @property
    def _engine(self):
        return _get_engine(self.db_url)

    async def ensure_schema(self) -> None:
        """Create the article_vectors table (and pgvector extension) once. Idempotent."""
        if self._ready:
            return
        if self._is_pg:
            try:
                async with self._engine.begin() as conn:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception as exc:  # noqa: BLE001 — surface a clear, actionable hint
                logger.warning(
                    "Could not create the 'vector' extension ({}). Enable it in "
                    "Supabase: Dashboard -> Database -> Extensions -> 'vector'.",
                    exc,
                )
            ddl = (
                f"CREATE TABLE IF NOT EXISTS article_vectors ("
                f"id TEXT PRIMARY KEY, ticker TEXT, document TEXT, source TEXT, "
                f"url TEXT, date TEXT, embedding vector({EMBED_DIM}))"
            )
        else:
            ddl = (
                "CREATE TABLE IF NOT EXISTS article_vectors ("
                "id TEXT PRIMARY KEY, ticker TEXT, document TEXT, source TEXT, "
                "url TEXT, date TEXT, embedding TEXT)"
            )
        async with self._engine.begin() as conn:
            await conn.execute(text(ddl))
        self._ready = True
        logger.debug("VectorStore schema ready ({})", "pgvector" if self._is_pg else "sqlite")

    async def add_articles(self, articles: list[Article]) -> None:
        """Embed + upsert articles (idempotent on a hash of the URL)."""
        await self.ensure_schema()
        rows: list[dict] = []
        seen: set[str] = set()
        for article in articles:
            if not article.content and not article.title:
                continue
            article_id = hashlib.md5(article.url.encode()).hexdigest()
            if article_id in seen:  # same URL twice in one batch -> keep the first
                continue
            seen.add(article_id)
            document = article.content if len(article.content) > 20 else article.title
            rows.append(
                {
                    "id": article_id,
                    "ticker": article.ticker,
                    "document": document,
                    "source": article.source,
                    "url": article.url,
                    "date": str(article.published_at or ""),
                }
            )
        if not rows:
            return

        embeddings = await _embed([r["document"] for r in rows], "retrieval_document")
        for r, emb in zip(rows, embeddings):
            r["embedding"] = _pgvector_literal(emb) if self._is_pg else json.dumps(emb)

        if self._is_pg:
            sql = text(
                "INSERT INTO article_vectors (id, ticker, document, source, url, date, embedding) "
                "VALUES (:id, :ticker, :document, :source, :url, :date, CAST(:embedding AS vector)) "
                "ON CONFLICT (id) DO UPDATE SET ticker=EXCLUDED.ticker, document=EXCLUDED.document, "
                "source=EXCLUDED.source, url=EXCLUDED.url, date=EXCLUDED.date, embedding=EXCLUDED.embedding"
            )
        else:
            sql = text(
                "INSERT INTO article_vectors (id, ticker, document, source, url, date, embedding) "
                "VALUES (:id, :ticker, :document, :source, :url, :date, :embedding) "
                "ON CONFLICT (id) DO UPDATE SET ticker=EXCLUDED.ticker, document=EXCLUDED.document, "
                "source=EXCLUDED.source, url=EXCLUDED.url, date=EXCLUDED.date, embedding=EXCLUDED.embedding"
            )
        async with self._engine.begin() as conn:
            await conn.execute(sql, rows)
        logger.debug("Upserted {} article(s) into vector store", len(rows))

    async def search_similar(self, query: str, ticker: str, n: int = 5) -> list[str]:
        """Return up to ``n`` documents most similar to ``query`` for a ticker."""
        await self.ensure_schema()
        n = min(n, 10)
        query_emb = (await _embed([query], "retrieval_query"))[0]

        if self._is_pg:
            async with self._engine.connect() as conn:
                rows = (
                    await conn.execute(
                        text(
                            "SELECT document FROM article_vectors WHERE ticker = :t "
                            "ORDER BY embedding <=> CAST(:q AS vector) LIMIT :n"
                        ),
                        {"t": ticker, "q": _pgvector_literal(query_emb), "n": n},
                    )
                ).all()
            return [r[0] for r in rows]

        # SQLite: brute-force cosine in Python (fine for local dev data volumes).
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    text("SELECT document, embedding FROM article_vectors WHERE ticker = :t"),
                    {"t": ticker},
                )
            ).all()
        scored: list[tuple[float, str]] = []
        for document, emb_json in rows:
            try:
                emb = json.loads(emb_json)
            except (ValueError, TypeError):
                continue
            scored.append((_cosine(query_emb, emb), document))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:n]]

    async def get_ticker_history(self, ticker: str, days: int = 30) -> list[str]:
        """Return stored documents for a ticker (most recent up to 50)."""
        await self.ensure_schema()
        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    text("SELECT document FROM article_vectors WHERE ticker = :t LIMIT 50"),
                    {"t": ticker},
                )
            ).all()
        return [r[0] for r in rows]

    async def collection_size(self) -> int:
        """Return the total number of stored article embeddings."""
        await self.ensure_schema()
        async with self._engine.connect() as conn:
            count = (await conn.execute(text("SELECT COUNT(*) FROM article_vectors"))).scalar_one()
        return int(count)
