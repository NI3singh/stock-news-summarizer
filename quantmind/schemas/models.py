"""QuantMind v2 — central data models (Pydantic v2).

The single source of truth for the system's data shapes: every other module
imports its types from here. Models are defined in dependency order — later
models reference earlier ones, so the ordering must be preserved.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Article(BaseModel):
    title: str
    url: str
    source: str
    ticker: str
    published_at: datetime | None = None
    content: str = ""
    credibility_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("title", "url")
    @classmethod
    def _strip_required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty after stripping whitespace")
        return v


class TechnicalSignals(BaseModel):
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    bb_upper: float | None = None
    bb_lower: float | None = None
    volume_ratio: float | None = None
    price_change_pct: float | None = None


class MemoryContext(BaseModel):
    similar_past_events: list[str] = Field(default_factory=list)
    historical_sentiment_trend: str = "No history available"
    days_of_history: int = 0


class NewsAnalysis(BaseModel):
    selected_articles: list[Article] = Field(default_factory=list)
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    key_themes: list[str] = Field(default_factory=list)
    summary: str = ""
    what_changed: str = ""


class QuantAnalysis(BaseModel):
    signals: TechnicalSignals
    interpretation: str = ""
    correlation_note: str = ""


class TickerAnalysis(BaseModel):
    ticker: str
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    news: NewsAnalysis
    quant: QuantAnalysis | None = None
    memory: MemoryContext
    final_synthesis: str = ""


class AgentContext(BaseModel):
    ticker: str
    articles: list[Article] = Field(default_factory=list)
    memory: MemoryContext | None = None
    extra: dict = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent_name: str
    success: bool
    data: Any = None
    error: str | None = None
    duration_seconds: float = 0.0


# --- Alerts (Phase B.4) ------------------------------------------------------

class AlertConditionType(str, Enum):
    """Kinds of conditions an alert rule can watch for."""

    SENTIMENT_BELOW = "sentiment_below"
    SENTIMENT_ABOVE = "sentiment_above"
    NEW_SEC_FILING = "new_sec_filing"
    DAILY_SUMMARY = "daily_summary"


class AlertRule(BaseModel):
    id: int | None = None
    ticker: str | None = None  # None means "any ticker"
    condition_type: AlertConditionType
    threshold: float | None = None  # for sentiment conditions
    is_active: bool = True
    # aware-UTC default (matches TickerAnalysis); avoids the deprecated utcnow.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered_at: datetime | None = None
    delivery_channel: str = "telegram"


class AlertEvent(BaseModel):
    rule_id: int
    ticker: str
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str
    delivered: bool = False
