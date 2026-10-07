"""
Fundamentals data access, backed by yfinance, with a local SQLite cache.

No API key needed -- yfinance pulls from Yahoo Finance's public data.
(We originally planned to use Financial Modeling Prep here instead; see
config.py for why that got deprioritized for v1.)

Each ticker's `.info` dict from yfinance is a large, loosely-typed grab
bag with inconsistent key availability across companies (e.g. a REIT or
a bank often lacks fields a normal operating company has). get_fundamentals()
below extracts just the fields the screener/DCF/risk modules actually need
and normalizes missing values to None rather than letting KeyErrors
propagate -- a stock with incomplete data should show up with blanks,
not crash the whole batch.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import yfinance as yf

from config import FUNDAMENTALS_CACHE_DB, FUNDAMENTALS_CACHE_TTL_HOURS

# yfinance .info key -> our column name. Centralized here so the rest of
# the app works with stable, short names instead of yfinance's raw keys.
_FIELD_MAP = {
    "longName": "name",
    "sector": "sector",
    "industry": "industry",
    "marketCap": "market_cap",
    "trailingPE": "pe",
    "priceToBook": "pb",
    "enterpriseToEbitda": "ev_ebitda",
    "trailingPegRatio": "peg",
    "dividendYield": "dividend_yield",
    "returnOnEquity": "roe",
    "returnOnAssets": "roa",
    "debtToEquity": "debt_to_equity",
    "profitMargins": "profit_margin",
    "beta": "beta",
    "currentPrice": "price",
    "fiftyTwoWeekHigh": "fifty_two_week_high",
    "fiftyTwoWeekLow": "fifty_two_week_low",
}


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fundamentals (
            ticker TEXT PRIMARY KEY,
            name TEXT, sector TEXT, industry TEXT,
            market_cap REAL, pe REAL, pb REAL, ev_ebitda REAL, peg REAL,
            dividend_yield REAL, roe REAL, roa REAL, debt_to_equity REAL,
            profit_margin REAL, beta REAL, price REAL,
            fifty_two_week_high REAL, fifty_two_week_low REAL,
            fetched_at TEXT NOT NULL,
            error TEXT
        )
        """
    )


def _is_stale(fetched_at: str) -> bool:
    fetched = datetime.fromisoformat(fetched_at)
    return datetime.utcnow() - fetched > timedelta(hours=FUNDAMENTALS_CACHE_TTL_HOURS)


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d.pop("fetched_at", None)
    d.pop("error", None)
    return d


def _fetch_from_yfinance(ticker: str) -> dict:
    """Pull and normalize one ticker's fundamentals from yfinance. Never
    raises for a "this stock is just missing a field" situation -- only
    for a genuine network/lookup failure, which the caller handles."""
    info = yf.Ticker(ticker).info
    if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
        raise ValueError(f"No data returned for {ticker} (delisted, invalid ticker, or rate-limited)")

    result = {"ticker": ticker}
    for yf_key, col in _FIELD_MAP.items():
        result[col] = info.get(yf_key)

    # Yahoo's own data is inconsistent about dividendYield's units: usually
    # a fraction (0.021 = 2.1%), but for some tickers it's already a
    # percent-like number (4.71 meaning 4.71%). No real stock has a
    # fraction-form yield above 1.0 (100%), so treat anything over that as
    # already-a-percent and normalize it down to a fraction, so the rest of
    # the app can consistently assume "fraction" everywhere.
    dy = result.get("dividend_yield")
    if dy is not None and dy > 1:
        result["dividend_yield"] = dy / 100

    return result


def get_fundamentals(ticker: str, force_refresh: bool = False) -> dict:
    """Return one ticker's fundamentals as a flat dict, serving from the
    local cache when fresh. On fetch failure, returns a dict of mostly-None
    values with an 'error' key set, rather than raising -- callers building
    a whole-universe table shouldn't have one bad ticker kill the batch."""
    conn = sqlite3.connect(FUNDAMENTALS_CACHE_DB)
    _init_db(conn)
    conn.row_factory = sqlite3.Row

    row = conn.execute("SELECT * FROM fundamentals WHERE ticker = ?", (ticker,)).fetchone()

    if not force_refresh and row and not _is_stale(row["fetched_at"]) and not row["error"]:
        result = _row_to_dict(row)
        conn.close()
        return result

    try:
        data = _fetch_from_yfinance(ticker)
        error = None
    except Exception as e:
        data = {"ticker": ticker, **{col: None for col in _FIELD_MAP.values()}}
        error = str(e)

    columns = ["ticker"] + list(_FIELD_MAP.values()) + ["fetched_at", "error"]
    values = [data.get(c) for c in ["ticker"] + list(_FIELD_MAP.values())] + [
        datetime.utcnow().isoformat(),
        error,
    ]
    placeholders = ", ".join("?" * len(columns))
    conn.execute(
        f"INSERT OR REPLACE INTO fundamentals ({', '.join(columns)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    conn.close()

    data["error"] = error
    return data
