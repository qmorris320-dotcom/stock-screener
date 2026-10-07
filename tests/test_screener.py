import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from analysis.screener import ScreenCriteria, apply_filters


def _sample_df():
    return pd.DataFrame(
        [
            {"ticker": "CHEAP", "sector": "Tech", "market_cap": 50e9, "pe": 10, "pb": 2,
             "ev_ebitda": 8, "peg": 1.0, "dividend_yield": 0.01, "error": None},
            {"ticker": "PRICEY", "sector": "Tech", "market_cap": 200e9, "pe": 60, "pb": 15,
             "ev_ebitda": 40, "peg": 3.0, "dividend_yield": 0.0, "error": None},
            {"ticker": "NODATA", "sector": "Energy", "market_cap": 10e9, "pe": None, "pb": None,
             "ev_ebitda": None, "peg": None, "dividend_yield": None, "error": None},
            {"ticker": "BROKEN", "sector": "Energy", "market_cap": 10e9, "pe": 5, "pb": 1,
             "ev_ebitda": 5, "peg": 0.5, "dividend_yield": 0.03, "error": "fetch failed"},
        ]
    )


def test_no_filters_drops_only_errored_rows():
    result = apply_filters(_sample_df(), ScreenCriteria())
    assert set(result["ticker"]) == {"CHEAP", "PRICEY", "NODATA"}


def test_max_pe_excludes_expensive_and_missing():
    result = apply_filters(_sample_df(), ScreenCriteria(max_pe=30))
    assert list(result["ticker"]) == ["CHEAP"]


def test_min_market_cap_filter():
    result = apply_filters(_sample_df(), ScreenCriteria(min_market_cap=100e9))
    assert set(result["ticker"]) == {"PRICEY"}


def test_sector_filter():
    result = apply_filters(_sample_df(), ScreenCriteria(sectors=["Energy"]))
    assert set(result["ticker"]) == {"NODATA"}


def test_min_dividend_yield():
    result = apply_filters(_sample_df(), ScreenCriteria(min_dividend_yield=0.005))
    assert set(result["ticker"]) == {"CHEAP"}


def test_combined_filters():
    result = apply_filters(_sample_df(), ScreenCriteria(max_pe=70, max_pb=20, min_market_cap=100e9))
    assert set(result["ticker"]) == {"PRICEY"}
