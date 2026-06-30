"""Tests for yfinance market-data enrichment mapping (no network)."""
from stockstalker.agents.quant_agent import _market_data_from_info
from stockstalker.schemas import MarketData


def test_market_data_from_info_maps_fields():
    info = {
        "currentPrice": 195.5,
        "marketCap": 3_050_000_000_000,
        "trailingPE": 31.2,
        "forwardPE": 28.0,
        "beta": 1.25,
        "fiftyTwoWeekHigh": 260.1,
        "fiftyTwoWeekLow": 169.2,
        "shortRatio": 1.8,
        "dividendYield": 0.44,
        "sector": "Technology",
        "industry": "Consumer Electronics",
    }
    md = _market_data_from_info(info, earnings_date="2026-05-01")
    assert isinstance(md, MarketData)
    assert md.current_price == 195.5
    assert md.market_cap == 3_050_000_000_000
    assert md.pe_ratio == 31.2
    assert md.forward_pe == 28.0
    assert md.sector == "Technology"
    assert md.industry == "Consumer Electronics"
    assert md.earnings_date == "2026-05-01"


def test_market_data_falls_back_to_regular_market_price():
    md = _market_data_from_info({"regularMarketPrice": 100.0})
    assert md.current_price == 100.0
    assert md.market_cap is None  # missing -> None
    assert md.earnings_date is None


def test_market_data_empty_info():
    md = _market_data_from_info({})
    assert isinstance(md, MarketData)
    assert md.current_price is None
    assert md.market_cap is None
