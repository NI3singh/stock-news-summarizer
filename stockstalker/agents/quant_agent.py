"""StockStalker v2 — Quant Agent.

Fetches 60d of price data (yfinance, off-thread), computes technical signals
(pandas_ta; each indicator isolated so one failure can't abort the agent), then
asks the LLM to interpret them alongside the news sentiment.
"""
import asyncio

from stockstalker.agents.base import BaseAgent
from stockstalker.llm.client import LLMError
from stockstalker.llm.prompts import quant_interpret_prompt
from stockstalker.schemas import AgentContext, AgentResult, QuantAnalysis, TechnicalSignals
from stockstalker.utils import logger


class QuantAgent(BaseAgent):
    async def run(self, context: AgentContext) -> AgentResult:
        import yfinance as yf

        # --- Step 1: price data (off the event loop) ---
        df = await asyncio.to_thread(
            lambda: yf.download(
                context.ticker,
                period="60d",
                interval="1d",
                progress=False,
                auto_adjust=True,
            )
        )
        if df is None or df.empty:
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=f"No price data for {context.ticker}",
                data=None,
            )

        # yfinance may return MultiIndex columns for a single ticker — flatten so
        # df["Close"] / df["Volume"] resolve to Series, not single-column frames.
        if df.columns.nlevels > 1:
            df.columns = df.columns.get_level_values(0)

        # --- Step 2: technical signals (each isolated; failure -> None) ---
        try:
            import pandas_ta  # noqa: F401 — registers the df.ta accessor
        except Exception as exc:  # noqa: BLE001 — degrade to all-None signals
            logger.warning("[{}] pandas_ta unavailable: {}", self.name, exc)

        def _last(series) -> float:
            return round(float(series.dropna().iloc[-1]), 4)

        rsi = macd = macd_signal = bb_upper = bb_lower = None
        volume_ratio = price_change_pct = None

        try:
            rsi = _last(df.ta.rsi(length=14))
        except Exception:  # noqa: BLE001
            rsi = None
        try:
            macd_df = df.ta.macd(fast=12, slow=26, signal=9)
            macd = _last(macd_df["MACD_12_26_9"])
            macd_signal = _last(macd_df["MACDs_12_26_9"])
        except Exception:  # noqa: BLE001
            macd = macd_signal = None
        try:
            bb = df.ta.bbands(length=20)
            # Column suffix varies by pandas_ta version (e.g. BBU_20_2.0) — match by prefix.
            upper_col = next((c for c in bb.columns if str(c).startswith("BBU")), None)
            lower_col = next((c for c in bb.columns if str(c).startswith("BBL")), None)
            bb_upper = _last(bb[upper_col]) if upper_col else None
            bb_lower = _last(bb[lower_col]) if lower_col else None
        except Exception:  # noqa: BLE001
            bb_upper = bb_lower = None
        try:
            avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
            volume_ratio = round(float(df["Volume"].iloc[-1] / avg_vol), 4)
        except Exception:  # noqa: BLE001
            volume_ratio = None
        try:
            close = df["Close"]
            price_change_pct = round(
                float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100), 4
            )
        except Exception:  # noqa: BLE001
            price_change_pct = None

        signals = TechnicalSignals(
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            bb_upper=bb_upper,
            bb_lower=bb_lower,
            volume_ratio=volume_ratio,
            price_change_pct=price_change_pct,
        )

        # --- Step 3: news sentiment from memory ---
        news_sentiment = 0.0
        if context.memory and context.memory.historical_sentiment_trend:
            trend = context.memory.historical_sentiment_trend.lower()
            if "positive" in trend:
                news_sentiment = 0.5
            if "negative" in trend:
                news_sentiment = -0.5

        # --- Step 4: LLM interpretation (degrade to signals-only if the LLM is down) ---
        try:
            quant_analysis = await self.llm.generate_structured(
                quant_interpret_prompt(context.ticker, signals, news_sentiment),
                QuantAnalysis,
            )
        except LLMError as exc:
            logger.warning(
                "[{}] LLM unavailable ({}) — returning technical signals without interpretation",
                self.name,
                exc,
            )
            quant_analysis = QuantAnalysis(
                signals=signals,
                interpretation="AI interpretation unavailable — technical signals only.",
                correlation_note="",
            )
        # Use the REAL computed signals, not the LLM's reproduced version.
        quant_analysis.signals = signals

        # --- Step 5 ---
        return AgentResult(
            agent_name=self.name,
            success=True,
            data=quant_analysis,
        )
