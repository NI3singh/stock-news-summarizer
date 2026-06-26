"""StockStalker v2 — abstract async scraper base.

Provides a shared ``httpx.AsyncClient``, browser-like headers with a rotating
User-Agent, a rate-limited GET that degrades gracefully on blocks (403/429), and
an async-context-manager lifecycle. Concrete scrapers implement ``scrape()``.
"""
from abc import ABC, abstractmethod

import httpx
from fake_useragent import UserAgent

from stockstalker.schemas import Article
from stockstalker.utils import logger, scraper_limiter


class BaseScraper(ABC):
    """Abstract base for all async news scrapers."""

    def __init__(self) -> None:
        self._ua = UserAgent()
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    def get_headers(self) -> dict:
        """Return browser-like request headers with a random User-Agent."""
        return {
            "User-Agent": self._ua.random,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }

    async def async_get(
        self, url: str, params: dict | None = None
    ) -> httpx.Response | None:
        """Rate-limited GET. Returns None on 403/429 (blocked); raises on errors."""
        async with scraper_limiter:
            try:
                response = await self.client.get(
                    url, params=params, headers=self.get_headers()
                )
            except httpx.TimeoutException:
                logger.warning("Timeout fetching {}", url)
                raise
            except httpx.HTTPError as exc:
                logger.error("HTTP error fetching {}: {}", url, exc)
                raise

        if response.status_code in (403, 429):
            logger.warning("Blocked fetching {} — HTTP {}", url, response.status_code)
            return None
        return response

    @abstractmethod
    async def scrape(self, ticker: str) -> list[Article]:
        ...

    async def __aenter__(self) -> "BaseScraper":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.client.aclose()
