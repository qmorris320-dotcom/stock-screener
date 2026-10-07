"""
Streamlit entry point.

Run with: streamlit run app/main.py

The fundamentals table is fetched once per session and stored in
st.session_state -- adjusting a filter re-runs the whole script (that's
how Streamlit works), but it only re-filters the already-fetched
DataFrame in memory rather than re-hitting yfinance for 500 tickers on
every slider nudge. Use "Refresh data" to force a real re-fetch.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Allow `streamlit run app/main.py` to import sibling packages (data/, analysis/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.universe import get_sp500_tickers  # noqa: E402
from data.universe_data import build_fundamentals_table  # noqa: E402
from analysis.screener import ScreenCriteria, apply_filters  # noqa: E402

st.set_page_config(page_title="Stock Screener", layout="wide")

st.title("Stock Screener")
st.caption(
    "A from-scratch stock evaluator combining valuation screening, DCF, "
    "and risk/quality metrics. Data: yfinance, S&P 500 universe. "
    "Educational project, not investment advice."
)

# --- Load the ticker universe -------------------------------------------
try:
    tickers = get_sp500_tickers()
except Exception as e:
    st.error(
        f"Couldn't load the S&P 500 ticker list ({e}). Run "
        "`python data/universe.py` from a terminal with internet access first."
    )
    st.stop()

# --- Sidebar filters -------------------------------------------------------
with st.sidebar:
    st.header("Universe")
    sample_size = st.slider(
        "How many tickers to pull data for",
        min_value=25,
        max_value=len(tickers),
        value=min(100, len(tickers)),
        step=25,
        help=(
            "yfinance fetches one request per ticker, so the full S&P 500 "
            "takes a few minutes the first time. Start smaller while you're "
            "testing, then run the full universe once you're ready."
        ),
    )
    fetch_clicked = st.button("Load / refresh data", type="primary")

    st.divider()
    st.header("Filters")
    max_pe = st.number_input("Max P/E", min_value=0.0, value=30.0, step=1.0)
    max_pb = st.number_input("Max P/B", min_value=0.0, value=8.0, step=0.5)
    max_ev_ebitda = st.number_input("Max EV/EBITDA", min_value=0.0, value=20.0, step=1.0)
    min_div_yield = st.number_input("Min dividend yield (%)", min_value=0.0, value=0.0, step=0.1)
    min_market_cap_b = st.number_input("Min market cap ($B)", min_value=0.0, value=0.0, step=1.0)

# --- Fetch (only on button click, or first load) ---------------------------
if fetch_clicked or "fundamentals_df" not in st.session_state:
    subset = tickers[:sample_size]
    progress_bar = st.progress(0.0, text=f"Fetching fundamentals for {len(subset)} tickers...")

    def _update_progress(done: int, total: int) -> None:
        progress_bar.progress(done / total, text=f"Fetched {done}/{total} tickers...")

    df = build_fundamentals_table(subset, force_refresh=fetch_clicked, progress_callback=_update_progress)
    progress_bar.empty()

    st.session_state["fundamentals_df"] = df
    n_errors = df["error"].notna().sum() if "error" in df.columns else 0
    if n_errors:
        st.warning(f"Loaded {len(df)} tickers; {n_errors} failed to fetch (rate-limited or no data).")
    else:
        st.success(f"Loaded fundamentals for {len(df)} tickers.")

df = st.session_state.get("fundamentals_df")

# --- Filter + display --------------------------------------------------
if df is not None and not df.empty:
    criteria = ScreenCriteria(
        max_pe=max_pe or None,
        max_pb=max_pb or None,
        max_ev_ebitda=max_ev_ebitda or None,
        min_dividend_yield=(min_div_yield / 100) if min_div_yield else None,
        min_market_cap=(min_market_cap_b * 1e9) if min_market_cap_b else None,
    )
    results = apply_filters(df, criteria)

    st.subheader(f"Results ({len(results)} of {len(df)} loaded tickers match)")

    display_cols = {
        "ticker": "Ticker", "name": "Name", "sector": "Sector",
        "market_cap": "Market Cap", "price": "Price", "pe": "P/E", "pb": "P/B",
        "ev_ebitda": "EV/EBITDA", "dividend_yield": "Div Yield", "roe": "ROE",
    }
    display_df = results[[c for c in display_cols if c in results.columns]].rename(columns=display_cols)
    if "Market Cap" in display_df.columns:
        display_df["Market Cap"] = display_df["Market Cap"].apply(
            lambda v: f"${v / 1e9:,.1f}B" if pd.notna(v) else "—"
        )
    if "Div Yield" in display_df.columns:
        display_df["Div Yield"] = display_df["Div Yield"].apply(
            lambda v: f"{v * 100:.2f}%" if pd.notna(v) else "—"
        )
    if "ROE" in display_df.columns:
        display_df["ROE"] = display_df["ROE"].apply(
            lambda v: f"{v * 100:.1f}%" if pd.notna(v) else "—"
        )

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    if len(results) >= 2 and results["pe"].notna().sum() >= 2:
        st.subheader("Valuation vs. size")
        chart_df = results.dropna(subset=["pe", "market_cap"])
        fig = px.scatter(
            chart_df,
            x="market_cap",
            y="pe",
            color="sector",
            hover_name="ticker",
            hover_data={"name": True, "pe": ":.1f", "market_cap": ":.2s"},
            labels={"market_cap": "Market cap", "pe": "P/E", "sector": "Sector"},
            log_x=True,
        )
        fig.update_layout(legend_title_text="Sector", height=500)
        st.plotly_chart(fig, use_container_width=True)
elif df is not None:
    st.info("No data loaded yet for any ticker -- try clicking 'Load / refresh data' again.")
else:
    st.info("Set how many tickers to load in the sidebar, then click 'Load / refresh data' to get started.")
