"""QuantMind ML — feature engineering (Phase D.2).

Turns raw analysis rows (from MLDataCollector) or a live TickerAnalysis into the
fixed feature matrix the signal model trains/predicts on. Missing numeric columns
fall back to neutral defaults — important because historical quant signals are
NOT persisted (see data_collector), so the training frame only has sentiment.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from quantmind.schemas import TickerAnalysis


def _series(df: pd.DataFrame, name: str, default: float) -> pd.Series:
    """df[name] coerced to numeric + NaN-filled, or a default-filled Series if absent.

    The spec's ``df.get(name, default).fillna(...)`` breaks when the column is
    missing (df.get returns the scalar default, which has no .fillna) — and the
    collector frame is missing rsi/macd/volume/price, so that's the common case.
    """
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index, dtype="float64")


class FeatureEngineer:
    """Builds the model feature matrix from analysis data."""

    FEATURE_COLUMNS = [
        "sentiment_score",
        "sentiment_abs",
        "sentiment_positive",
        "sentiment_negative",
        "rsi",
        "rsi_overbought",
        "rsi_oversold",
        "macd",
        "macd_positive",
        "volume_ratio",
        "high_volume",
        "price_change_pct",
        "sentiment_x_volume",
        "sentiment_x_rsi",
    ]

    def build_features(self, df: pd.DataFrame) -> tuple[pd.DataFrame, "pd.Series | None"]:
        """Return (X, y). y is None when no 'label' column is present (predict mode)."""
        features = pd.DataFrame(index=df.index)

        features["sentiment_score"] = _series(df, "sentiment_score", 0.0)
        features["sentiment_abs"] = features["sentiment_score"].abs()
        features["sentiment_positive"] = (features["sentiment_score"] > 0.3).astype(int)
        features["sentiment_negative"] = (features["sentiment_score"] < -0.3).astype(int)

        features["rsi"] = _series(df, "rsi", 50.0)
        features["rsi_overbought"] = (features["rsi"] > 70).astype(int)
        features["rsi_oversold"] = (features["rsi"] < 30).astype(int)

        features["macd"] = _series(df, "macd", 0.0)
        features["macd_positive"] = (features["macd"] > 0).astype(int)

        features["volume_ratio"] = _series(df, "volume_ratio", 1.0)
        features["high_volume"] = (features["volume_ratio"] > 1.5).astype(int)

        features["price_change_pct"] = _series(df, "price_change_pct", 0.0)

        # Interaction features
        features["sentiment_x_volume"] = (
            features["sentiment_score"] * features["volume_ratio"]
        )
        features["sentiment_x_rsi"] = features["sentiment_score"] * (
            features["rsi"] / 100.0
        )

        features = features.fillna(0)  # final safety net
        y = df["label"] if "label" in df.columns else None
        return features[self.FEATURE_COLUMNS], y

    def features_from_analysis(self, analysis: TickerAnalysis) -> pd.DataFrame:
        """One-row feature frame from a live TickerAnalysis (prediction mode)."""
        q = analysis.quant.signals if analysis.quant else None
        row = {
            "sentiment_score": analysis.news.sentiment_score,
            "rsi": q.rsi if q and q.rsi is not None else 50.0,
            "macd": q.macd if q and q.macd is not None else 0.0,
            "volume_ratio": q.volume_ratio if q and q.volume_ratio is not None else 1.0,
            "price_change_pct": (
                q.price_change_pct if q and q.price_change_pct is not None else 0.0
            ),
        }
        X, _ = self.build_features(pd.DataFrame([row]))
        return X
