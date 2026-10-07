"""
Valuation screener: filters the fundamentals table down to a shortlist.

Operates on the DataFrame produced by data/universe_data.build_fundamentals_table()
-- columns: ticker, name, sector, industry, market_cap, price, pe, pb,
ev_ebitda, peg, dividend_yield, roe, roa, debt_to_equity, profit_margin,
beta, fifty_two_week_high, fifty_two_week_low, error.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class ScreenCriteria:
    """User-facing filter thresholds. All optional -- None means 'no filter'."""

    max_pe: float | None = None
    max_pb: float | None = None
    max_ev_ebitda: float | None = None
    max_peg: float | None = None
    min_dividend_yield: float | None = None  # as a fraction, e.g. 0.02 = 2%
    min_market_cap: float | None = None
    sectors: list[str] | None = None


def apply_filters(universe_df: pd.DataFrame, criteria: ScreenCriteria) -> pd.DataFrame:
    """Filter the fundamentals table down to rows matching criteria.

    Rows with a missing value for a filtered field are excluded by that
    filter (e.g. a company with no P/E because it's unprofitable won't
    pass a max_pe filter) rather than being silently kept or crashing --
    that's a judgment call worth being explicit about, not hiding.
    """
    df = universe_df.copy()

    # A fetch error means we don't trust any of this row's numbers.
    if "error" in df.columns:
        df = df[df["error"].isna()]

    if criteria.max_pe is not None:
        df = df[df["pe"].notna() & (df["pe"] > 0) & (df["pe"] <= criteria.max_pe)]
    if criteria.max_pb is not None:
        df = df[df["pb"].notna() & (df["pb"] > 0) & (df["pb"] <= criteria.max_pb)]
    if criteria.max_ev_ebitda is not None:
        df = df[df["ev_ebitda"].notna() & (df["ev_ebitda"] > 0) & (df["ev_ebitda"] <= criteria.max_ev_ebitda)]
    if criteria.max_peg is not None:
        df = df[df["peg"].notna() & (df["peg"] > 0) & (df["peg"] <= criteria.max_peg)]
    if criteria.min_dividend_yield is not None and criteria.min_dividend_yield > 0:
        df = df[df["dividend_yield"].notna() & (df["dividend_yield"] >= criteria.min_dividend_yield)]
    if criteria.min_market_cap is not None:
        df = df[df["market_cap"].notna() & (df["market_cap"] >= criteria.min_market_cap)]
    if criteria.sectors:
        df = df[df["sector"].isin(criteria.sectors)]

    return df.sort_values("pe", na_position="last")
