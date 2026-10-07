"""
Builds the full screening table: fundamentals for every ticker in the
universe, fetched concurrently since yfinance has no batch endpoint for
`.info`.

This is the thing app/main.py calls once per session (then caches in
Streamlit's session state) rather than re-fetching on every filter change.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

import pandas as pd

from config import FUNDAMENTALS_FETCH_WORKERS
from data.fundamentals import get_fundamentals


def build_fundamentals_table(
    tickers: list[str],
    force_refresh: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> pd.DataFrame:
    """Fetch fundamentals for every ticker and return one combined DataFrame.

    Runs requests concurrently (see FUNDAMENTALS_FETCH_WORKERS in config.py).
    Tickers that fail to fetch still get a row (mostly-null, with an
    'error' column set) rather than being silently dropped, so the UI can
    show the user how much data coverage they actually have.

    progress_callback(done, total), if given, is called after each ticker
    completes -- app/main.py uses this to drive a Streamlit progress bar.
    """
    rows = []
    total = len(tickers)
    done = 0

    with ThreadPoolExecutor(max_workers=FUNDAMENTALS_FETCH_WORKERS) as executor:
        futures = {
            executor.submit(get_fundamentals, ticker, force_refresh): ticker
            for ticker in tickers
        }
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                rows.append(future.result())
            except Exception as e:
                # get_fundamentals() already catches fetch errors internally;
                # this is a last-resort guard against something unexpected
                # (e.g. a corrupt cache row) so one ticker can't kill the run.
                rows.append({"ticker": ticker, "error": str(e)})
            done += 1
            if progress_callback:
                progress_callback(done, total)

    df = pd.DataFrame(rows)
    # Keep a stable column order regardless of fetch completion order.
    preferred_order = [
        "ticker", "name", "sector", "industry", "market_cap", "price",
        "pe", "pb", "ev_ebitda", "peg", "dividend_yield",
        "roe", "roa", "debt_to_equity", "profit_margin", "beta",
        "fifty_two_week_high", "fifty_two_week_low", "error",
    ]
    cols = [c for c in preferred_order if c in df.columns]
    return df[cols].sort_values("ticker").reset_index(drop=True)
