"""
compute_returns.py
Pure computation over parquet data already on disk. No network calls here.
"""

from datetime import date

import pandas as pd

from modules.utils import (
    MOMENTUM_LABEL,
    MOMENTUM_WEIGHTS,
    TIMEFRAMES,
    load_price_data,
)


def _pct_return(series: pd.Series, periods: int, as_of: pd.Timestamp | None = None) -> float | None:
    """Return % change over the last `periods` trading days (as of `as_of` if given)."""
    if as_of is not None:
        series = series.loc[:as_of]
    if len(series) <= periods:
        return None
    return float((series.iloc[-1] / series.iloc[-1 - periods] - 1) * 100)


def _range_return(
    series: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
    as_of: pd.Timestamp | None = None,
) -> float | None:
    """Return % change between the closest available prices to start and end."""
    if as_of is not None:
        series = series.loc[:as_of]
    window = series.loc[(series.index >= start) & (series.index <= end)]
    if len(window) < 2:
        return None
    return float((window.iloc[-1] / window.iloc[0] - 1) * 100)


def fy_bounds(as_of: pd.Timestamp) -> tuple:
    """Indian financial year bounds (Apr 1 - Mar 31) containing `as_of`."""
    year = as_of.year if as_of.month >= 4 else as_of.year - 1
    return pd.Timestamp(year, 4, 1), pd.Timestamp(year + 1, 3, 31)


def _empty_row(name: str) -> dict:
    """Row of all-None returns for an instrument with no usable price history."""
    row = {"Instrument": name}
    row.update({tf: None for tf in TIMEFRAMES})
    row["FY"] = None
    row["CY"] = None
    return row


def compute_returns_row(name: str, kind: str, as_of: pd.Timestamp | None = None) -> dict:
    """
    Full return set for one instrument (fixed timeframes + FY + CY), optionally
    computed as of a shared end date so all instruments align.
    """
    df = load_price_data(name, kind)
    if df.empty or "Close" not in df:
        return _empty_row(name)

    close = df["Close"].dropna()
    if as_of is not None:
        close = close.loc[:as_of]
    if close.empty:
        return _empty_row(name)

    today = close.index.max()
    row = {"Instrument": name}
    for label, days in TIMEFRAMES.items():
        row[label] = _pct_return(close, days)

    fy_start, fy_end = fy_bounds(today)
    row["FY"] = _range_return(close, fy_start, fy_end)
    row["CY"] = _range_return(close, pd.Timestamp(today.year, 1, 1), pd.Timestamp(today.year, 12, 31))
    return row


def _common_end_date(names: list, kind: str) -> pd.Timestamp | None:
    """Latest trading date that every instrument shares, or None if no data."""
    ends = []
    for name in names:
        df = load_price_data(name, kind)
        if df.empty or "Close" not in df:
            continue
        close = df["Close"].dropna()
        if not close.empty:
            ends.append(close.index.max())
    return max(ends) if ends else None


def momentum_from_row(row: dict) -> float | None:
    """Weighted blend of 1M/3M/6M returns from a compute_returns_row dict."""
    total = 0.0
    for tf, weight in MOMENTUM_WEIGHTS.items():
        value = row.get(tf)
        if value is None or value != value:  # covers None and NaN
            return None
        total += value * weight
    return total


def momentum_score(name: str, kind: str, as_of: pd.Timestamp | None = None) -> float | None:
    """Weighted momentum score (0.5*1M + 0.3*3M + 0.2*6M) for one instrument."""
    return momentum_from_row(compute_returns_row(name, kind, as_of))


def build_returns_matrix(names: list, kind: str, add_momentum: bool = True) -> pd.DataFrame:
    """
    Rows = instruments, columns = timeframes + Momentum. All returns are computed
    as of the latest date common to every instrument, so no row is "ahead" of another.
    """
    as_of = _common_end_date(names, kind)
    rows = [compute_returns_row(name, kind, as_of) for name in names]
    df = pd.DataFrame(rows).set_index("Instrument")
    if add_momentum and not df.empty:
        df[MOMENTUM_LABEL] = df.apply(momentum_from_row, axis=1)
    return df


def rank_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    """Column-wise rank (1 = highest return). NaN cells stay NaN."""
    return returns_df.rank(axis=0, ascending=False, method="min", na_option="keep")


def trend_direction(name: str, kind: str, lookback_days: int = 21) -> int:
    """+1 / -1 / 0 depending on whether price is above/below `lookback_days` ago."""
    df = load_price_data(name, kind)
    if df.empty or "Close" not in df:
        return 0
    close = df["Close"].dropna()
    if len(close) <= lookback_days:
        return 0
    previous = close.iloc[-1 - lookback_days]
    above = int(close.iloc[-1] > previous)
    below = int(close.iloc[-1] < previous)
    return above - below


def custom_range_return(name: str, kind: str, start: date, end: date) -> float | None:
    """% return for a user-picked date range, used by the Trend Explorer."""
    df = load_price_data(name, kind)
    if df.empty or "Close" not in df:
        return None
    return _range_return(df["Close"].dropna(), pd.Timestamp(start), pd.Timestamp(end))


def rolling_return_series(name: str, kind: str, window_days: int) -> pd.Series:
    """Rolling N-day % return series, for the 'rolling returns' chart."""
    df = load_price_data(name, kind)
    if df.empty or "Close" not in df:
        return pd.Series(dtype=float)
    close = df["Close"].dropna()
    return (close / close.shift(window_days) - 1) * 100


def normalized_price_series(name: str, kind: str, start: date = None) -> pd.Series:
    """Price series rebased to 100 at the start of the window, for comparison charts."""
    df = load_price_data(name, kind)
    if df.empty or "Close" not in df:
        return pd.Series(dtype=float)
    close = df["Close"].dropna()
    if start:
        close = close.loc[close.index >= pd.Timestamp(start)]
    if close.empty:
        return close
    return close / close.iloc[0] * 100


def daily_return_series(name: str, kind: str, lookback_days: int = None) -> pd.Series:
    """Daily % return series, optionally limited to the last `lookback_days` rows."""
    df = load_price_data(name, kind)
    if df.empty or "Close" not in df:
        return pd.Series(dtype=float)
    returns = df["Close"].pct_change().dropna() * 100
    if lookback_days:
        returns = returns.tail(lookback_days)
    return returns


def build_correlation_matrix(names: list, kind: str, lookback_days: int = 126) -> pd.DataFrame:
    """
    Pairwise correlation of daily returns across instruments, over the last
    `lookback_days` trading days. Feeds the Correlation Matrix page.
    """
    series_map = {name: daily_return_series(name, kind, lookback_days) for name in names}
    combined = pd.DataFrame(series_map).dropna(how="all")
    if combined.empty:
        return pd.DataFrame(index=names, columns=names, dtype=float)
    return combined.corr()


def relative_strength_series(name: str, kind: str, benchmark_close: pd.Series) -> pd.Series:
    """Ratio of instrument price to benchmark price, rebased to 100."""
    df = load_price_data(name, kind)
    if df.empty or "Close" not in df or benchmark_close.empty:
        return pd.Series(dtype=float)
    aligned = pd.concat([df["Close"], benchmark_close], axis=1, join="inner")
    aligned.columns = ["instrument", "benchmark"]
    ratio = aligned["instrument"] / aligned["benchmark"]
    return ratio / ratio.iloc[0] * 100
