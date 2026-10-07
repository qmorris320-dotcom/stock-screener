"""
Price data access, backed by yfinance with a local SQLite cache.

Phase 1 scope: daily adjusted close history, enough for beta/volatility
(Phase 4) and factor regression (Phase 5 stretch). Fundamentals live in
fundamentals.py instead, since they come from FMP and refresh on a much
slower cadence.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from config import PRICE_CACHE_DB, PRICE_CACHE_TTL_HOURS


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            adj_close REAL,
            volume INTEGER,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (ticker, date)
        )
        """
    )


def _is_stale(fetched_at: str) -> bool:
    fetched = datetime.fromisoformat(fetched_at)
    return datetime.utcnow() - fetched > timedelta(hours=PRICE_CACHE_TTL_HOURS)


def get_price_history(ticker: str, period: str = "5y", force_refresh: bool = False) -> pd.DataFrame:
    """Return a DataFrame of [date, adj_close, volume] for one ticker.

    Serves from the local cache when it's fresh; otherwise pulls from
    yfinance and re-populates the cache. TODO (Phase 1): batch-fetch
    multiple tickers at once via yf.download() instead of one at a time,
    once we're screening the full universe rather than a handful of names.
    """
    conn = sqlite3.connect(PRICE_CACHE_DB)
    _init_db(conn)

    cached = pd.read_sql(
        "SELECT date, adj_close, volume, fetched_at FROM prices WHERE ticker = ? ORDER BY date",
        conn,
        params=(ticker,),
    )

    if not force_refresh and not cached.empty and not _is_stale(cached["fetched_at"].iloc[-1]):
        conn.close()
        return cached[["date", "adj_close", "volume"]].set_index("date")

    hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    if hist.empty:
        conn.close()
        return cached[["date", "adj_close", "volume"]].set_index("date") if not cached.empty else hist

    fetched_at = datetime.utcnow().isoformat()
    rows = [
        (ticker, idx.strftime("%Y-%m-%d"), float(row["Close"]), int(row["Volume"]), fetched_at)
        for idx, row in hist.iterrows()
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO prices (ticker, date, adj_close, volume, fetched_at) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()

    return hist.rename(columns={"Close": "adj_close", "Volume": "volume"})[["adj_close", "volume"]]
