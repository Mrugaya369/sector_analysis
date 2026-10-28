"""
utils.py
Shared constants, file paths, and small IO helpers.
Nothing in here talks to the network — that's fetch_data.py's job.
"""

import json
import os
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SECTOR_DIR = os.path.join(DATA_DIR, "sectors")
STOCK_DIR = os.path.join(DATA_DIR, "stocks")
METADATA_PATH = os.path.join(DATA_DIR, "metadata.json")
LAST_UPDATE_PATH = os.path.join(DATA_DIR, "last_update.txt")

os.makedirs(SECTOR_DIR, exist_ok=True)
os.makedirs(STOCK_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Universe definitions
# ---------------------------------------------------------------------------
# Sector name -> Yahoo Finance ticker. Some NSE sector indices are unreliable
# or missing on Yahoo (PSU Bank, Media, Infra) — validate_tickers() in
# fetch_data.py flags these at runtime instead of failing silently.
SECTOR_TICKERS = {
    "NIFTY IT": "^CNXIT",
    "NIFTY Pharma": "^CNXPHARMA",
    "NIFTY Auto": "^CNXAUTO",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY Metal": "^CNXMETAL",
    "NIFTY PSU Bank": "^CNXPSUBANK",
    "NIFTY Realty": "^CNXREALTY",
    "NIFTY Financial Services": "NIFTY_FIN_SERVICE.NS",
    "NIFTY Energy": "^CNXENERGY",
    "NIFTY Media": "^CNXMEDIA",
    "NIFTY Infra": "^CNXINFRA",
}

BENCHMARK_TICKER = "^NSEI"  # NIFTY 50, used for relative strength

# Default top constituents per sector (starter set — user can add more
# tickers from the Update Data page, which are stored the same way).
DEFAULT_STOCKS = {
    "NIFTY IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"],
    "NIFTY Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
    "NIFTY Auto": ["MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS"],
    "NIFTY FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
    "NIFTY Metal": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS"],
    "NIFTY PSU Bank": ["SBIN.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS"],
    "NIFTY Realty": ["DLF.NS", "OBEROIRLTY.NS", "GODREJPROP.NS"],
    "NIFTY Financial Services": ["BAJFINANCE.NS", "HDFCLIFE.NS", "SBILIFE.NS"],
    "NIFTY Energy": ["RELIANCE.NS", "NTPC.NS", "POWERGRID.NS", "ONGC.NS"],
    "NIFTY Media": ["ZEEL.NS", "PVRINOX.NS", "SUNTV.NS"],
    "NIFTY Infra": ["LT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS"],
}

# Return-window engine, expressed in trading days (None = special handling)
TIMEFRAMES = {
    "1D": 1,
    "1W": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "1Y": 252,
}

# Momentum score = weighted blend of near-term returns.
MOMENTUM_LABEL = "Momentum"
MOMENTUM_WEIGHTS = {"1M": 0.5, "3M": 0.3, "6M": 0.2}

# Timeframes offered by the Heatmap page's focus selector (rankable columns).
FOCUS_TIMEFRAMES = ["1D", "1M", "6M", "FY"]

# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------
def load_metadata() -> dict:
    """Read metadata.json, returning an empty dict if it doesn't exist yet."""
    if not os.path.exists(METADATA_PATH):
        return {}
    with open(METADATA_PATH, "r") as f:
        return json.load(f)


def save_metadata(metadata: dict) -> None:
    """Write metadata.json and stamp last_update.txt."""
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    with open(LAST_UPDATE_PATH, "w") as f:
        f.write(datetime.now().isoformat())


def get_last_update() -> str:
    """Human-readable timestamp of the last successful update run."""
    if not os.path.exists(LAST_UPDATE_PATH):
        return "Never"
    with open(LAST_UPDATE_PATH, "r") as f:
        raw = f.read().strip()
    if raw == "never" or not raw:
        return "Never"
    return datetime.fromisoformat(raw).strftime("%Y-%m-%d %H:%M")


def stale_days() -> int | None:
    """Number of days since the last update run, or None if never updated."""
    if not os.path.exists(LAST_UPDATE_PATH):
        return None
    with open(LAST_UPDATE_PATH, "r") as f:
        raw = f.read().strip()
    if not raw or raw == "never":
        return None
    try:
        last = datetime.fromisoformat(raw)
        return (datetime.now() - last).days
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Parquet helpers
# ---------------------------------------------------------------------------
def ticker_to_filename(name: str) -> str:
    """Turn a sector name or ticker into a filesystem-safe file stem."""
    return name.replace(" ", "_").replace("^", "").replace(".", "_").replace("&", "and")


def parquet_path(name: str, kind: str) -> str:
    """kind is 'sector' or 'stock'."""
    folder = SECTOR_DIR if kind == "sector" else STOCK_DIR
    return os.path.join(folder, f"{ticker_to_filename(name)}.parquet")


def load_price_data(name: str, kind: str) -> pd.DataFrame:
    """Load a single instrument's OHLCV parquet. Empty DataFrame if missing."""
    path = parquet_path(name, kind)
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def list_available(kind: str) -> list:
    """Names of instruments that currently have data on disk."""
    folder = SECTOR_DIR if kind == "sector" else STOCK_DIR
    stems = [f[:-8] for f in os.listdir(folder) if f.endswith(".parquet")]
    lookup = SECTOR_TICKERS if kind == "sector" else {}
    reverse = {ticker_to_filename(k): k for k in lookup} if lookup else {}
    return sorted(reverse.get(s, s) for s in stems)
