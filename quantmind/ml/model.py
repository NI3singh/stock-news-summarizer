"""QuantMind ML — sentiment signal model (Phase D.3).

A deliberately simple, interpretable binary classifier: given an analysis, will
the next trading day close up? Uses LogisticRegression (interpretable ``coef_``)
inside a scaling Pipeline, with cross-validation when there's enough data. It is
honest about small samples — returns ``insufficient_data`` rather than a fake
model — and reports whether it beats a majority-class baseline.

(The phase overview mentions GradientBoosting, but the per-step spec and good
practice for tiny datasets call for LogisticRegression + coefficients.)
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from quantmind.ml.data_collector import MLDataCollector
from quantmind.ml.features import FeatureEngineer
from quantmind.utils import logger

if TYPE_CHECKING:
    from quantmind.memory import DatabaseManager
    from quantmind.schemas import TickerAnalysis

MODEL_SAVE_DIR = Path("./quantmind_models")


def _interpret(cv_mean: float | None, baseline: float, n: int) -> str:
    """An honest one-line read of the result (the phase asks for this explicitly)."""
    if cv_mean is None:
        return (
            f"Trained on {n} samples — too few for cross-validation; "
            "treat as indicative only, not a validated edge."
        )
    edge = cv_mean - baseline
    if n < 30:
        conf = "NOT statistically meaningful (tiny sample)"
    elif n < 100:
        conf = "weak evidence (small sample)"
    else:
        conf = "a reasonable sample"
    verdict = "beats" if edge > 0.01 else "matches" if abs(edge) <= 0.01 else "trails"
    return (
        f"CV accuracy {cv_mean:.3f} vs {baseline:.3f} majority baseline "
        f"({verdict} baseline by {edge:+.3f}) on {conf}."
    )


class SignalModel:
    """Trains/loads a per-ticker next-day-direction classifier."""

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker.upper()
        self.model_path = MODEL_SAVE_DIR / f"{self.ticker}_model.joblib"
        self.pipeline: Pipeline | None = None
        self.metrics: dict = {}
        self.feature_engineer = FeatureEngineer()
        MODEL_SAVE_DIR.mkdir(exist_ok=True)

    async def train(self, db: DatabaseManager) -> dict:
        collector = MLDataCollector(db)
        df = await collector.collect_training_data(self.ticker, min_samples=10)

        if df.empty or len(df) < 10:
            return {
                "status": "insufficient_data",
                "samples": len(df),
                "required": 10,
                "message": (
                    f"Need at least 10 analyses to train. Currently have {len(df)}. "
                    "Keep running daily analyses."
                ),
            }

        X, y = self.feature_engineer.build_features(df)

        self.pipeline = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        C=1.0,
                        max_iter=1000,
                        random_state=42,
                        class_weight="balanced",  # handle imbalanced up/down days
                    ),
                ),
            ]
        )

        if len(X) >= 20:
            cv_scores = cross_val_score(self.pipeline, X, y, cv=5, scoring="accuracy")
            cv_mean = float(cv_scores.mean())
            cv_std = float(cv_scores.std())
        else:
            cv_mean = None
            cv_std = None
            logger.warning("Too few samples for 5-fold CV ({} rows)", len(X))

        self.pipeline.fit(X, y)

        classifier = self.pipeline.named_steps["classifier"]
        importances = dict(zip(FeatureEngineer.FEATURE_COLUMNS, classifier.coef_[0]))
        top_features = sorted(
            importances.items(), key=lambda kv: abs(kv[1]), reverse=True
        )[:5]

        pos, neg = int(y.sum()), int((y == 0).sum())
        baseline = max(pos, neg) / len(y)  # majority-class accuracy

        self.metrics = {
            "ticker": self.ticker,
            "samples_trained": len(X),
            "cv_accuracy_mean": round(cv_mean, 4) if cv_mean is not None else None,
            "cv_accuracy_std": round(cv_std, 4) if cv_std is not None else None,
            "baseline_accuracy": round(baseline, 4),
            "beats_baseline": bool(cv_mean is not None and cv_mean > baseline),
            "interpretation": _interpret(cv_mean, baseline, len(X)),
            "top_features": [
                {"feature": f, "coefficient": round(float(c), 4)} for f, c in top_features
            ],
            "label_distribution": {"positive_days": pos, "negative_days": neg},
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }

        joblib.dump(self.pipeline, self.model_path)
        logger.info("Model saved to {}", self.model_path)
        if cv_mean is not None:
            logger.info("CV Accuracy: {:.3f} +/- {:.3f}", cv_mean, cv_std)
        else:
            logger.info("Model trained (no CV — too few samples)")

        return {"status": "trained", **self.metrics}

    def load(self) -> bool:
        if self.model_path.exists():
            self.pipeline = joblib.load(self.model_path)
            logger.info("Model loaded from {}", self.model_path)
            return True
        return False

    def predict(self, analysis: TickerAnalysis) -> dict:
        if self.pipeline is None and not self.load():
            return {
                "error": f"No trained model for {self.ticker}. Run train first.",
                "prediction": None,
            }

        X = self.feature_engineer.features_from_analysis(analysis)
        prob = self.pipeline.predict_proba(X)[0]
        prediction = int(self.pipeline.predict(X)[0])
        confidence = float(max(prob))

        return {
            "ticker": self.ticker,
            "prediction": "UP" if prediction == 1 else "DOWN",
            "confidence": round(confidence, 4),
            "probability_up": round(float(prob[1]), 4),
            "probability_down": round(float(prob[0]), 4),
            "signal_strength": (
                "strong"
                if confidence > 0.7
                else "moderate"
                if confidence > 0.55
                else "weak"
            ),
        }
