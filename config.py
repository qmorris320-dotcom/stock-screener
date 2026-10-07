"""
Project-wide configuration.

Loads secrets from a local .env file (see .env.example) so API keys never
get committed to git. Other modules should import constants from here
rather than reading environment variables directly.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths -------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

UNIVERSE_FILE = PROJECT_ROOT / "data" / "sp500_constituents.csv"
PRICE_CACHE_DB = CACHE_DIR / "prices.sqlite3"
FUNDAMENTALS_CACHE_DB = CACHE_DIR / "fundamentals.sqlite3"

# --- API keys ------------------------------------------------------------
# Not required for v1 -- prices and fundamentals both come from yfinance,
# which needs no signup or key. FMP_API_KEY is kept here as an opt-in
# upgrade path (its data is cleaner/more complete than yfinance's free
# `.info` dict) if there's time to add it back later; unset is fine.
FMP_API_KEY = os.getenv("FMP_API_KEY", "")

# --- Caching -------------------------------------------------------------
# How long a cached row is considered fresh before we re-fetch it.
PRICE_CACHE_TTL_HOURS = 24
FUNDAMENTALS_CACHE_TTL_HOURS = 24 * 7  # fundamentals change slowly

# --- Universe --------------------------------------------------------------
# Phase 0 scope: S&P 500 constituents only (bounded, well-covered by
# yfinance's free data). Widen later if it's still adding value.
DEFAULT_UNIVERSE = "sp500"

# --- Fetching --------------------------------------------------------------
# yfinance has no batch endpoint for fundamentals (.info is one HTTP
# request per ticker), so we fetch concurrently. Keep this modest --
# too many parallel requests risks Yahoo rate-limiting/blocking us.
FUNDAMENTALS_FETCH_WORKERS = 8
