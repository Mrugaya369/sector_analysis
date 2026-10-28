"""
fetch_data.py
Incremental Yahoo Finance fetcher. Pulls only rows newer than what's already
on disk, appends to parquet, and updates metadata.json. Designed to be
called from the Update Data page with a progress callback.
"""

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from modules.utils import (
    SECTOR_TICKERS,
    parquet_path,
    load_metadata,
    save_metadata,
    load_price_data,
)


def validate_tickers(tickers: dict) -> dict:
    """
    Quick liveness check for a name -> ticker mapping.
    Returns {"ok": [...], "dead": [...]} so the UI can warn about
    NSE indices that Yahoo Finance doesn't reliably carry.
    """
    ok, dead = [], []
    for name, ticker in tickers.items():
        try:
            probe = yf.Ticker(ticker).history(period="5d")
            (ok if not probe.empty else dead).append(name)
        except Exception:
            dead.append(name)
    return {"ok": ok, "dead": dead}


def _fetch_new_rows(ticker: str, start_date: str | None) -> pd.DataFrame:
    """Download OHLCV from start_date to today. start_date=None fetches full history."""
    kwargs = {"start": start_date} if start_date else {"period": "max"}
    df = yf.download(ticker, progress=False, auto_adjust=True, **kwargs)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index.name = "Date"
    return df[["Open", "High", "Low", "Close", "Volume"]]


def update_instrument(name: str, ticker: str, kind: str, log_fn=None) -> dict:
    """
    Update a single instrument's parquet file incrementally.
    Returns a status dict: {"name", "rows_added", "status"}.
    """
    log = log_fn or (lambda msg: None)
    path = parquet_path(name, kind)
    existing = load_price_data(name, kind)

    start_date = None
    if not existing.empty:
        start_date = (existing.index.max() + timedelta(days=1)).strftime("%Y-%m-%d")
        if start_date >= datetime.now().strftime("%Y-%m-%d"):
            log(f"{name}: already up to date")
            return {"name": name, "rows_added": 0, "status": "up_to_date"}

    try:
        new_rows = _fetch_new_rows(ticker, start_date)
    except Exception as exc:
        log(f"{name}: fetch failed ({exc})")
        return {"name": name, "rows_added": 0, "status": "failed"}

    if new_rows.empty:
        log(f"{name}: no new rows")
        return {"name": name, "rows_added": 0, "status": "no_new_data"}

    combined = pd.concat([existing, new_rows]) if not existing.empty else new_rows
    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    combined.to_parquet(path)

    log(f"{name}: +{len(new_rows)} rows (total {len(combined)})")
    return {"name": name, "rows_added": len(new_rows), "status": "updated"}


def update_all(sector_map: dict, stock_map: dict, log_fn=None) -> list:
    """
    Update every sector index and every stock across all sectors.
    stock_map: {sector_name: [ticker, ticker, ...]}
    Returns a list of per-instrument status dicts and writes metadata.json.
    """
    log = log_fn or (lambda msg: None)
    metadata = load_metadata()
    results = []

    for name, ticker in sector_map.items():
        result = update_instrument(name, ticker, "sector", log)
        results.append(result)
        metadata[name] = {
            "ticker": ticker,
            "kind": "sector",
            "last_checked": datetime.now().isoformat(),
            "status": result["status"],
        }

    for sector, tickers in stock_map.items():
        for ticker in tickers:
            result = update_instrument(ticker, ticker, "stock", log)
            results.append(result)
            metadata[ticker] = {
                "ticker": ticker,
                "kind": "stock",
                "sector": sector,
                "last_checked": datetime.now().isoformat(),
                "status": result["status"],
            }

    save_metadata(metadata)
    return results


def add_custom_stock(ticker: str, sector: str, log_fn=None) -> dict:
    """Fetch full history for a user-added ticker and register it in metadata."""
    result = update_instrument(ticker, ticker, "stock", log_fn)
    metadata = load_metadata()
    metadata[ticker] = {
        "ticker": ticker,
        "kind": "stock",
        "sector": sector,
        "last_checked": datetime.now().isoformat(),
        "status": result["status"],
        "custom": True,
    }
    save_metadata(metadata)
    return result
