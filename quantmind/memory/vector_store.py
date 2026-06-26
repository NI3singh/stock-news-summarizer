"""QuantMind v2 — vector store (ChromaDB wrapper).

ChromaDB's client API is synchronous, which would block the asyncio event loop.
This wrapper exposes an async surface by offloading every blocking ChromaDB call
to a worker thread via ``asyncio.to_thread(...)``. A single persistent collection
(``quantmind_articles``) holds article documents keyed by a hash of their URL.
"""
import asyncio
import hashlib

import chromadb
from chromadb.config import Settings

from quantmind.config import settings
from quantmind.schemas import Article
from quantmind.utils import logger

_COLLECTION_NAME = "quantmind_articles"


class VectorStore:
    """Async wrapper over a persistent ChromaDB collection."""

    def __init__(self, persist_path: str = settings.chroma_persist_path) -> None:
        self.persist_path = persist_path
        # Synchronous, one-time client/collection setup (constructor runs once).
        # Telemetry is disabled to avoid noisy network calls / log spam.
        self._client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(name=_COLLECTION_NAME)
        logger.debug("VectorStore ready at {} (collection: {})", persist_path, _COLLECTION_NAME)

    async def add_articles(self, articles: list[Article]) -> None:
        """Upsert articles into the collection (idempotent on URL hash)."""
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        seen: set[str] = set()  # ChromaDB upsert requires ids unique WITHIN a call
        for article in articles:
            # Skip only if there is genuinely nothing to embed.
            if not article.content and not article.title:
                continue
            article_id = hashlib.md5(article.url.encode()).hexdigest()
            if article_id in seen:  # same URL twice in one batch -> keep the first
                continue
            seen.add(article_id)
            ids.append(article_id)
            documents.append(
                article.content if len(article.content) > 20 else article.title
            )
            metadatas.append(
                {
                    "ticker": article.ticker,
                    "source": article.source,
                    "url": article.url,
                    "date": str(article.published_at or ""),
                }
            )

        if not ids:
            return

        # upsert() (not add()) so duplicate URLs update rather than error.
        await asyncio.to_thread(
            self._collection.upsert,
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        logger.debug("Upserted {} article(s) into vector store", len(ids))

    async def search_similar(self, query: str, ticker: str, n: int = 5) -> list[str]:
        """Return up to ``n`` documents most similar to ``query`` for a ticker."""
        results = await asyncio.to_thread(
            self._collection.query,
            query_texts=[query],
            n_results=min(n, 10),
            where={"ticker": ticker},
        )
        documents = results.get("documents") or []
        return documents[0] if documents else []

    async def get_ticker_history(self, ticker: str, days: int = 30) -> list[str]:
        """Return stored documents for a ticker (most recent up to 50).

        NOTE: uses ``collection.get`` (metadata filter) rather than ``query``,
        since retrieving a ticker's history has no semantic query text. ``days``
        is accepted for API stability but not yet applied as a date filter
        (Chroma stores ``date`` as a string; range filtering is a future task).
        """
        results = await asyncio.to_thread(
            self._collection.get,
            where={"ticker": ticker},
            limit=50,
        )
        return results.get("documents") or []

    async def collection_size(self) -> int:
        """Return the total number of documents in the collection."""
        return await asyncio.to_thread(self._collection.count)
