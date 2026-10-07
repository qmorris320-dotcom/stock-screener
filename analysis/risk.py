"""
Phase 4: risk and quality overlay.

Metrics that sit alongside valuation and DCF to answer "is this actually
a good business, and how risky is it" -- not just "is it cheap".

TODO (Phase 4):
- beta: regress the stock's daily returns against a market proxy (e.g.
  SPY) over a trailing window (use data/prices.py for both series).
- volatility: annualized stdev of daily returns.
- sharpe_ratio: (mean return - risk-free rate) / volatility, annualized.
- quality metrics (ROE, ROIC, debt/equity, margins) pulled from
  data/fundamentals.py -- mostly plumbing once that module is wired up.
"""
from __future__ import annotations


def beta(ticker: str, market_ticker: str = "SPY", period: str = "3y") -> float:
    raise NotImplementedError("Beta calculation lands in Phase 4")


def annualized_volatility(ticker: str, period: str = "1y") -> float:
    raise NotImplementedError("Volatility calculation lands in Phase 4")


def sharpe_ratio(ticker: str, risk_free_rate: float = 0.045, period: str = "3y") -> float:
    raise NotImplementedError("Sharpe ratio calculation lands in Phase 4")


def quality_snapshot(ticker: str) -> dict:
    """Return ROE, ROIC, debt/equity, and margins for a ticker in one dict."""
    raise NotImplementedError("Quality snapshot lands in Phase 4")
