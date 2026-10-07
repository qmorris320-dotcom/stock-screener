# Stock Screener

A from-scratch stock evaluator combining a valuation screener, a DCF
intrinsic-value model, a risk/quality overlay, and (stretch goals) a
Fama-French factor regression and an efficient-frontier portfolio
optimizer. Built as a personal project to sharpen financial-analysis
skills and to demonstrate them for job interviews.

**Status: working valuation screener.** Load real S&P 500 fundamentals and
filter by P/E, P/B, EV/EBITDA, dividend yield, market cap, and sector; see
the phase roadmap below for what's done vs. planned. Follow the commit
history for the running story of what got built each week.

## Why these particular models

The valuation screen answers "is this cheap on the numbers." The DCF
answers "what's it actually worth," with an explicit sensitivity view
rather than a single point estimate, since any DCF is only as good as its
assumptions. The risk/quality overlay answers "is this actually a good,
survivable business." The Fama-French factor regression (stretch) ties
each stock back to the standard academic risk factors (market, size,
value, profitability, investment) -- a lens that lines up with a
factor-tilted, evidence-based approach to investing rather than picking
stocks on vibes.

## Tech stack

- **UI:** [Streamlit](https://streamlit.io/) -- chosen over a
  React/FastAPI split to keep the project shippable solo on a tight
  timeline, while still being a real, deployable data app (not a toy).
- **Data:** [yfinance](https://github.com/ranaroussi/yfinance) for both
  price history and fundamentals -- no API key or signup required, which
  matters for a project meant to be clonable and runnable by anyone
  reviewing it. Fundamentals are fetched concurrently (one HTTP request
  per ticker; yfinance has no batch endpoint for `.info`) and cached
  locally in SQLite so repeat runs don't re-fetch. (Financial Modeling
  Prep is still wired into config.py as an opt-in upgrade path -- its data
  is cleaner -- but isn't required for v1.)
- **Universe:** S&P 500 constituents (pulled from Wikipedia's maintained
  table), not "any ticker" -- bounded scope, reliable data coverage on
  both free-tier data sources.
- **Analysis:** pandas/numpy/scipy for the core math; statsmodels
  (factor regression) and PyPortfolioOpt (efficient frontier) join later,
  once the core screener/DCF/risk pieces are solid.

## Setup

```bash
git clone <this-repo-url>
cd stock-screener
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python data/universe.py  # caches the current S&P 500 list
streamlit run app/main.py
```

No API keys needed. In the app, pick how many tickers to load (start
small -- the full S&P 500 takes a few minutes the first time since
yfinance fetches one ticker at a time) and click "Load / refresh data."

## Phase roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Repo scaffold, data layer stubs, Streamlit shell | Done |
| 1 | Real data layer: concurrent fundamentals pulls, SQLite caching | Done |
| 2 | Valuation screener (P/E, P/B, EV/EBITDA, dividend yield, market cap, sector) + results table/chart | Done |
| 3 | DCF intrinsic value model with assumption sensitivity | Planned |
| 4 | Risk/quality overlay (beta, volatility, Sharpe, ROE/ROIC, debt ratios) | Planned |
| 5 (stretch) | Fama-French 5-factor regression per stock | Planned |
| 6 (stretch) | Efficient-frontier portfolio optimizer over the shortlist | Planned |

Target: a polished, deployed v1 (phases 0-4) by mid-November 2026, with
phases 5-6 as stretch goals if time allows before finals.

## Project layout

```
data/          data access: universe list, fundamentals (cached), concurrent batch fetcher
analysis/      the actual math: screener (done), DCF, risk/quality
app/           Streamlit UI
tests/         pytest suite -- offline, no network needed (yfinance is mocked)
config.py      paths, cache settings, API key loading
```

## Disclaimer

This is an educational/portfolio project, not investment advice. The
data comes from free-tier APIs and may be delayed, incomplete, or wrong;
don't make real trading decisions based on it.
