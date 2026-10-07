"""
Tests the caching and error-handling logic in data/fundamentals.py without
hitting the network -- yf.Ticker is monkeypatched so these run offline.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import data.fundamentals as fundamentals_module


class _FakeTicker:
    def __init__(self, ticker: str):
        self.ticker = ticker

    @property
    def info(self):
        if self.ticker == "BADTICKER":
            return {}
        return {
            "longName": f"{self.ticker} Inc.",
            "sector": "Technology",
            "marketCap": 1_000_000_000,
            "trailingPE": 22.5,
            "priceToBook": 4.1,
            "dividendYield": 0.012,
            "currentPrice": 150.0,
        }


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    """Point the module at a throwaway SQLite file so tests don't touch
    the real cache or leak state between test runs."""
    monkeypatch.setattr(fundamentals_module, "FUNDAMENTALS_CACHE_DB", tmp_path / "test_fundamentals.sqlite3")
    monkeypatch.setattr(fundamentals_module.yf, "Ticker", _FakeTicker)
    yield


def test_get_fundamentals_happy_path(isolated_cache):
    result = fundamentals_module.get_fundamentals("AAPL")
    assert result["ticker"] == "AAPL"
    assert result["pe"] == 22.5
    assert result["sector"] == "Technology"
    assert result["error"] is None


def test_get_fundamentals_handles_missing_data(isolated_cache):
    result = fundamentals_module.get_fundamentals("BADTICKER")
    assert result["error"] is not None
    assert result["pe"] is None


def test_get_fundamentals_uses_cache_on_second_call(isolated_cache, monkeypatch):
    calls = {"count": 0}
    real_fetch = fundamentals_module._fetch_from_yfinance

    def _counting_fetch(ticker):
        calls["count"] += 1
        return real_fetch(ticker)

    monkeypatch.setattr(fundamentals_module, "_fetch_from_yfinance", _counting_fetch)

    fundamentals_module.get_fundamentals("AAPL")
    fundamentals_module.get_fundamentals("AAPL")  # should be served from cache
    assert calls["count"] == 1


def test_force_refresh_bypasses_cache(isolated_cache, monkeypatch):
    calls = {"count": 0}
    real_fetch = fundamentals_module._fetch_from_yfinance

    def _counting_fetch(ticker):
        calls["count"] += 1
        return real_fetch(ticker)

    monkeypatch.setattr(fundamentals_module, "_fetch_from_yfinance", _counting_fetch)

    fundamentals_module.get_fundamentals("AAPL")
    fundamentals_module.get_fundamentals("AAPL", force_refresh=True)
    assert calls["count"] == 2
