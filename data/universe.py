"""
Stock universe: the S&P 500 constituent list.

We scope v1 to the S&P 500 rather than "any ticker" because both yfinance
and FMP's free tier have solid, reliable coverage for these names, and a
bounded universe keeps caching and rate limits manageable.

The list changes a few times a year (additions/removals), so we pull it
from Wikipedia's maintained table and cache it locally rather than hand
-typing something that goes stale.
"""
from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

# Allow running this file directly (`python data/universe.py`) as well as
# importing it as a package (`from data.universe import ...`).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import PROJECT_ROOT  # noqa: E402

WIKI_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
_CACHE_PATH = PROJECT_ROOT / "data" / "sp500_constituents.csv"

# Wikipedia's servers return 403 Forbidden for requests that don't send a
# real-looking User-Agent (pandas.read_html's default urllib request gets
# blocked). Fetching the page ourselves with a browser-like header first,
# then handing the HTML text to pandas, avoids that.
_REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; stock-screener-project/1.0)"}


def refresh_sp500_list() -> pd.DataFrame:
    """Pull the current S&P 500 constituent table from Wikipedia and cache it.

    Returns a DataFrame with at least ['Symbol', 'Security', 'GICS Sector'].
    Raises whatever requests/pandas raises on network failure -- callers
    should fall back to get_sp500_tickers(), which tolerates that.
    """
    resp = requests.get(WIKI_SP500_URL, headers=_REQUEST_HEADERS, timeout=15)
    resp.raise_for_status()
    tables = pd.read_html(StringIO(resp.text))
    sp500 = tables[0].rename(columns={"Symbol": "Symbol", "Security": "Security"})
    sp500["Symbol"] = sp500["Symbol"].str.replace(".", "-", regex=False)  # yfinance format, e.g. BRK.B -> BRK-B
    sp500.to_csv(_CACHE_PATH, index=False)
    return sp500


def get_sp500_tickers(force_refresh: bool = False) -> list[str]:
    """Return the cached S&P 500 ticker list, refreshing from Wikipedia if needed."""
    if force_refresh or not _CACHE_PATH.exists():
        try:
            df = refresh_sp500_list()
        except Exception:
            if _CACHE_PATH.exists():
                df = pd.read_csv(_CACHE_PATH)
            else:
                raise
    else:
        df = pd.read_csv(_CACHE_PATH)
    return sorted(df["Symbol"].dropna().unique().tolist())


if __name__ == "__main__":
    tickers = get_sp500_tickers(force_refresh=True)
    print(f"Cached {len(tickers)} S&P 500 tickers to {_CACHE_PATH}")
