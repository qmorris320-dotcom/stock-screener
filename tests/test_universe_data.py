import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.universe_data import build_fundamentals_table


def _fake_get_fundamentals(ticker, force_refresh=False):
    if ticker == "FAIL":
        return {"ticker": ticker, "error": "boom"}
    return {"ticker": ticker, "pe": 15.0, "sector": "Tech", "error": None}


def test_build_fundamentals_table_combines_all_tickers(monkeypatch):
    import data.universe_data as universe_data_module

    monkeypatch.setattr(universe_data_module, "get_fundamentals", _fake_get_fundamentals)

    df = build_fundamentals_table(["AAPL", "MSFT", "FAIL"])

    assert len(df) == 3
    assert set(df["ticker"]) == {"AAPL", "MSFT", "FAIL"}
    assert df[df["ticker"] == "FAIL"]["error"].iloc[0] == "boom"


def test_build_fundamentals_table_progress_callback(monkeypatch):
    import data.universe_data as universe_data_module

    monkeypatch.setattr(universe_data_module, "get_fundamentals", _fake_get_fundamentals)

    calls = []
    build_fundamentals_table(["AAPL", "MSFT"], progress_callback=lambda done, total: calls.append((done, total)))

    assert len(calls) == 2
    assert calls[-1] == (2, 2)
