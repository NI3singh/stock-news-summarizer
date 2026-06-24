"""QuantMind ML — training-data collector (Phase D.1).

Pairs each historical analysis (from the DB) with the actual next-trading-day
price move (via yfinance) to build a labeled dataset for the signal model:
``sentiment_score -> did the stock go up the next day?``

NOTE: the ``analyses`` table stores ``quant_interpretation`` as LLM prose, NOT
the numeric quant signals — so historical RSI/MACD are not recoverable here. The
feature layer (D.2) therefore engineers sentiment-derived features.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pandas as pd
import yfinance as yf

from quantmind.utils import logger

if TYPE_CHECKING:
    from quantmind.memory import DatabaseManager


def _to_naive_normalized(value) -> pd.Timestamp | None:
    """Parse a datetime-ish value to a tz-naive, date-normalized Timestamp."""
    try:
        ts = pd.to_datetime(value)
    except (ValueError, TypeError):
        return None
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)
    return ts.normalize()


class MLDataCollector:
    """Builds a labeled (sentiment -> next-day move) dataset from stored analyses."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    async def collect_training_data(
        self, ticker: str, min_samples: int = 10
    ) -> pd.DataFrame:
        ticker = ticker.upper().strip()

        analyses = await self.db.get_all_analyses(ticker)
        if not analyses:
            logger.warning("No analyses in DB for {} — nothing to collect", ticker)
            return pd.DataFrame()

        df_price = await asyncio.to_thread(
            lambda: yf.download(ticker, period="90d", progress=False, auto_adjust=True)
        )
        if df_price is None or df_price.empty:
            logger.warning("No price data for {} — cannot label samples", ticker)
            return pd.DataFrame()

        # yfinance returns MultiIndex columns even for a single ticker — flatten.
        if isinstance(df_price.columns, pd.MultiIndex):
            df_price.columns = df_price.columns.get_level_values(0)
        close = df_price["Close"].dropna()

        # Normalize the price index to tz-naive dates for clean alignment.
        idx = close.index
        if getattr(idx, "tz", None) is not None:
            idx = idx.tz_localize(None)
        close.index = idx.normalize()
        dates = close.index

        rows: list[dict] = []
        for a in analyses:
            adate = _to_naive_normalized(a.get("analyzed_at"))
            if adate is None:
                continue
            # entry = last trading day on/before the analysis date; label by the
            # NEXT trading day's move. searchsorted gives the insertion point.
            pos = dates.searchsorted(adate, side="right") - 1
            if pos < 0 or pos + 1 >= len(dates):
                continue  # no price on/before the date, or no next trading day yet
            entry_close = float(close.iloc[pos])
            next_close = float(close.iloc[pos + 1])
            if entry_close == 0 or pd.isna(entry_close) or pd.isna(next_close):
                continue
            next_day_return = (next_close - entry_close) / entry_close * 100.0
            rows.append(
                {
                    "ticker": ticker,
                    "analysis_date": adate.date().isoformat(),
                    "sentiment_score": a.get("sentiment_score"),
                    # quant signals are not persisted (prose-only) -> unavailable.
                    "next_day_return": round(next_day_return, 4),
                    "label": 1 if next_day_return > 0 else 0,
                }
            )

        df = pd.DataFrame(rows)
        if len(df) < min_samples:
            logger.warning(
                "Only {} samples for {} — need at least {} for reliable training",
                len(df),
                ticker,
                min_samples,
            )
        logger.info("Collected {} training samples for {}", len(df), ticker)
        return df
