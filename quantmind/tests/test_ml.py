"""QuantMind — ML layer unit tests (mocked; no live LLM / network).

Covers feature engineering, the signal model (train/predict), the prediction
service, the entity extractor, and the entity-graph DB round-trip.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
import pandas as pd

from quantmind.memory import DatabaseManager
from quantmind.ml.entity_extractor import EntityExtractor
from quantmind.ml.features import FeatureEngineer
from quantmind.ml.model import SignalModel
from quantmind.ml.prediction_service import PredictionService
from quantmind.schemas import (
    Article,
    EntityExtractionResult,
    EntityRelationship,
    EntityType,
    ExtractedEntity,
)

_COLLECT = "quantmind.ml.data_collector.MLDataCollector.collect_training_data"


def _synth_df(n: int) -> pd.DataFrame:
    """n rows of (sentiment_score, label) with both classes guaranteed present."""
    rng = np.random.default_rng(0)
    sent = rng.uniform(-1, 1, n)
    label = ((sent + rng.normal(0, 0.3, n)) > 0).astype(int)
    label[0], label[1] = 0, 1  # ensure both classes
    return pd.DataFrame({"sentiment_score": sent, "label": label})


# Test 1 — feature engineering shape
def test_feature_shape():
    df = pd.DataFrame(
        [
            {"sentiment_score": s, "rsi": 50.0, "macd": 0.0, "volume_ratio": 1.0,
             "price_change_pct": 0.0, "label": i % 2}
            for i, s in enumerate([0.7, -0.4, 0.1, -0.8, 0.3])
        ]
    )
    X, y = FeatureEngineer().build_features(df)
    assert X.shape == (5, 14)  # 14 features (spec said 15 — miscount, see D.2)
    assert not X.isnull().any().any()
    assert y is not None and int(y.sum()) >= 0  # numpy int -> coerce for the check


# Test 2 — interaction feature computed correctly
def test_interaction_feature():
    df = pd.DataFrame([{"sentiment_score": 0.8, "volume_ratio": 2.0, "label": 1}])
    X, _ = FeatureEngineer().build_features(df)
    assert abs(X["sentiment_x_volume"].iloc[0] - 1.6) < 1e-9  # 0.8 * 2.0


# Test 3 — SignalModel training with mock data
async def test_signal_model_train(monkeypatch):
    monkeypatch.setattr(_COLLECT, AsyncMock(return_value=_synth_df(15)))
    model = SignalModel("TESTML")
    try:
        result = await model.train(db=None)
        assert result["status"] == "trained"
        assert result["samples_trained"] == 15
        assert model.pipeline is not None
    finally:
        Path(model.model_path).unlink(missing_ok=True)


# Test 4 — SignalModel predict structure
async def test_signal_model_predict(monkeypatch):
    monkeypatch.setattr(_COLLECT, AsyncMock(return_value=_synth_df(15)))
    model = SignalModel("TESTML")
    try:
        await model.train(db=None)
        ta = SimpleNamespace(
            ticker="TESTML", news=SimpleNamespace(sentiment_score=0.7), quant=None
        )
        result = model.predict(ta)
        assert "prediction" in result
        assert result["prediction"] in ["UP", "DOWN"]
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["signal_strength"] in ["strong", "moderate", "weak"]
    finally:
        Path(model.model_path).unlink(missing_ok=True)


# Test 5 — PredictionService returns None when no model saved
def test_prediction_service_no_model():
    svc = PredictionService()
    analysis = SimpleNamespace(
        ticker="NOMODEL123", news=SimpleNamespace(sentiment_score=0.5), quant=None
    )
    assert svc.predict(analysis) is None


# Test 6 — entity extraction structure
async def test_entity_extraction():
    sample = EntityExtractionResult(
        entities=[
            ExtractedEntity(name="Intel", entity_type=EntityType.COMPANY),
            ExtractedEntity(name="Tim Cook", entity_type=EntityType.PERSON),
        ],
        relationships=[
            EntityRelationship(
                source_entity="Apple", target_entity="Intel",
                relationship="partners_with", confidence=0.9,
            )
        ],
    )
    llm = SimpleNamespace(generate_structured=AsyncMock(return_value=sample))
    articles = [
        Article(title="Apple-Intel deal", url="https://x", source="Polygon",
                ticker="AAPL", content="Apple and Intel announced a partnership.")
    ]
    result = await EntityExtractor(llm).extract("AAPL", articles)
    assert isinstance(result, EntityExtractionResult)
    assert len(result.entities) == 2
    assert result.entities[0].ticker == "AAPL"


# Test 7 — entity graph DB round-trip (tmp file DB, NOT :memory: — see note above)
async def test_entity_graph_roundtrip(tmp_path):
    db = DatabaseManager(db_path=str(tmp_path / "ml_test.db"))
    await db.init_db()
    await db.save_entities(
        [
            ExtractedEntity(name="Intel", entity_type=EntityType.COMPANY, ticker="AAPL"),
            ExtractedEntity(name="Nvidia", entity_type=EntityType.COMPANY, ticker="AAPL"),
        ]
    )
    await db.save_relationships(
        [
            EntityRelationship(
                source_entity="Apple", target_entity="Intel",
                relationship="partners_with", confidence=0.9,
            )
        ],
        "AAPL",
    )
    graph = await db.get_entity_graph()
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1
