"""QuantMind ML — prediction service (Phase D.4).

Loads + caches per-ticker SignalModels and runs predictions, returning a typed
MLPrediction (or None when no model exists / a prediction fails). Models stay in
memory after first load to avoid a disk read on every analysis.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from quantmind.ml.model import SignalModel
from quantmind.schemas import MLPrediction
from quantmind.utils import logger

if TYPE_CHECKING:
    from quantmind.schemas import TickerAnalysis


class PredictionService:
    """Caches trained models per ticker and produces MLPrediction objects."""

    def __init__(self) -> None:
        self._model_cache: dict[str, SignalModel] = {}

    def get_model(self, ticker: str) -> SignalModel | None:
        ticker = ticker.upper()
        if ticker not in self._model_cache:
            model = SignalModel(ticker)
            if not model.load():
                return None
            self._model_cache[ticker] = model
        return self._model_cache[ticker]

    def predict(self, analysis: TickerAnalysis) -> MLPrediction | None:
        model = self.get_model(analysis.ticker)
        if model is None:
            logger.debug("No model for {} — skipping ML prediction", analysis.ticker)
            return None
        try:
            result = model.predict(analysis)
        except Exception as exc:  # noqa: BLE001 — ML must never break the pipeline
            logger.warning("ML prediction error for {}: {}", analysis.ticker, exc)
            return None
        if "error" in result:
            logger.warning("Prediction failed: {}", result["error"])
            return None
        return MLPrediction(
            prediction=result["prediction"],
            confidence=result["confidence"],
            probability_up=result["probability_up"],
            probability_down=result["probability_down"],
            signal_strength=result["signal_strength"],
        )

    def invalidate_cache(self, ticker: str) -> None:
        ticker = ticker.upper()
        if ticker in self._model_cache:
            del self._model_cache[ticker]
            logger.info("Model cache cleared for {}", ticker)
