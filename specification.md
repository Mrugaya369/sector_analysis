# Specification — NSE Sector Dashboard

## 1. Purpose

A Streamlit dashboard for daily sector rotation and trend analysis on NSE
(National Stock Exchange, India) sector indices and their constituent stocks,
built on data pulled from Yahoo Finance and cached locally as Parquet.

## 2. Data layer

### 2.1 Source
Yahoo Finance, via the `yfinance` Python package. OHLCV daily bars, adjusted close.

### 2.2 Universe

**Sector indices** (`modules/utils.py::SECTOR_TICKERS`):

| Sector | Ticker |
|---|---|
| NIFTY IT | `^CNXIT` |
| NIFTY Pharma | `^CNXPHARMA` |
| NIFTY Auto | `^CNXAUTO` |
| NIFTY FMCG | `^CNXFMCG` |
| NIFTY Metal | `^CNXMETAL` |
| NIFTY PSU Bank | `^CNXPSUBANK` |
| NIFTY Realty | `^CNXREALTY` |
| NIFTY Financial Services | `NIFTY_FIN_SERVICE.NS` |
| NIFTY Energy | `^CNXENERGY` |
| NIFTY Media | `^CNXMEDIA` |
| NIFTY Infra | `^CNXINFRA` |

Benchmark for relative strength: `^NSEI` (NIFTY 50).

**Stocks** — two sources, both stored identically as one Parquet file per ticker:
1. Defaults per sector (`modules/utils.py::DEFAULT_STOCKS`), 3–5 top constituents each.
2. User-added, via the "Add a custom stock" form on the Update Data page. Custom
   tickers are tagged `"custom": true` in `metadata.json` but otherwise behave
   identically to defaults.

### 2.3 Storage

```
data/
├── sectors/<name>.parquet     # one file per sector index, columns: Open, High, Low, Close, Volume
├── stocks/<ticker>.parquet    # one file per stock, same columns
├── metadata.json              # per-instrument: ticker, kind, sector, last_checked, status
└── last_update.txt            # ISO timestamp of the last successful update run
```

Filenames are sanitized via `utils.ticker_to_filename()` (spaces → `_`, `^`/`.`/`&` stripped or replaced)
so index names and tickers are both safe as filenames.

### 2.4 Update mechanism

Triggered manually from the **Update Data** page (`pages/3_Update_Data.py`) —
no cron/scheduler by design, so the user controls when network calls happen.

Algorithm (`modules/fetch_data.py::update_instrument`):
1. Load existing Parquet for the instrument, if any.
2. If data exists, request only rows from `max(existing date) + 1 day` onward.
   If none exists, request full history (`period="max"`).
3. Concatenate, drop duplicate index entries (keep latest), sort, overwrite Parquet.
4. Return a status: `updated | up_to_date | no_new_data | failed`.

`update_all()` runs this for every sector and every default stock, streaming
progress via a `log_fn` callback that the page uses to drive a progress bar
and a scrolling log box. `st.cache_data.clear()` is called after a successful
run so the Heatmap/Trend/Correlation pages immediately reflect new data.

`validate_tickers()` does a lightweight 5-day history probe per sector ticker
and reports which ones returned no data — used to flag Yahoo Finance coverage
gaps (historically PSU Bank, Media, and Infra are the most likely to fail)
without needing a full update run.

## 3. Returns engine (`modules/compute_returns.py`)

All functions are pure — they read Parquet via `utils.load_price_data()` and
return floats, Series, or DataFrames. No network access.

| Function | Returns |
|---|---|
| `compute_returns_row(name, kind, as_of=None)` | dict of 1D/1W/1M/3M/6M/1Y/FY/CY % returns for one instrument, aligned to `as_of` |
| `build_returns_matrix(names, kind)` | DataFrame, rows=instruments, columns=timeframes + **Momentum** — feeds the heatmap. All values computed as of the latest shared trading date |
| `momentum_score(name, kind)` | weighted momentum = 0.5·1M + 0.3·3M + 0.2·6M (`utils.MOMENTUM_WEIGHTS`) |
| `rank_matrix(returns_df)` | column-wise rank (1 = highest return; NaN stays NaN) |
| `trend_direction(name, kind, lookback=21)` | +1/−1/0 vs the price `lookback` sessions ago |
| `custom_range_return(name, kind, start, end)` | % return between two user-picked dates |
| `rolling_return_series(name, kind, window_days)` | rolling N-day % return, full series |
| `normalized_price_series(name, kind, start)` | price rebased to 100 at `start` (or series start) |
| `relative_strength_series(name, kind, benchmark_close)` | instrument/benchmark ratio, rebased to 100 |
| `daily_return_series(name, kind, lookback_days)` | daily % return series, tail-limited |
| `build_correlation_matrix(names, kind, lookback_days)` | pairwise Pearson correlation of daily returns |

**Fixed timeframes** are expressed in trading days: 1D=1, 1W=5, 1M=21, 3M=63,
6M=126, 1Y=252 (`utils.TIMEFRAMES`). An instrument with fewer rows than the
window returns `None` for that cell rather than raising.

**FY** = Indian financial year, Apr 1 – Mar 31, computed via `fy_bounds()`.
**CY** = calendar year, Jan 1 – Dec 31.

## 4. Visual modules

### 4.1 Heatmap (`pages/1_Heatmap.py`)
- Rows = 12 sector indices, columns = all fixed timeframes + FY + CY + Momentum.
- Red→green diverging color scale (`RdYlGn`, `zmid=0`, symmetric around 0).
- **Hover tooltips** show sector name, timeframe, return %, and column rank.
- **Focus selector** (`st.segmented_control`: 1D/1M/6M/FY/Momentum) drives the
  ranking of the raw-returns table and the sector-card ranks. The full matrix
  stays the primary chart.
- **Color legend** rendered above the chart (red → yellow → green).
- **Top-3 outperformers** and a responsive **sector card grid** (momentum, 1M/6M,
  rank, trend arrow).
- **CSV download dropdown** (full matrix / ranked / transposed) with a toast.
- **Auto-refresh** via `@st.fragment(run_every=300)` — re-reads local parquet
  only, no network calls. Cached 4 min (`st.cache_data(ttl=240)`).
- "Data unavailable — showing last cached values" banner when sectors have no
  on-disk data; "Stale data" banner when `last_update.txt` is older than 3 days.

### 4.2 Trend Explorer (`pages/2_Trend_Explorer.py`)
- Multiselect for any number of sectors and/or stocks (no upper limit enforced).
- Date range picker for the display window.
- Three layout modes, user-selectable via `st.pills`:
  - **Overlay** — one multi-line chart, all instruments together.
  - **Grid** — auto column count via `trend_builder.grid_columns()`
    (2 cols ≤4 items, 3 cols ≤6 items, 4 cols beyond).
  - **Tabs** — one `st.tabs()` entry per instrument.
- Four chart types as sub-tabs: Trend line, Rolling returns (window selectable:
  5/21/63/126 days), Relative strength vs NIFTY 50, Normalized comparison (rebased to 100).
- Charts follow the active light/dark theme via a shared Plotly template.

### 4.3 Correlation Matrix (`pages/4_Correlation_Matrix.py`)
- All 12 sectors by default; any fetched stock can be added via multiselect.
- Lookback window selectable: 21/63/126/252 trading days.
- Diverging red-blue heatmap (`RdBu`, `zmid=0`, range fixed to [-1, 1]) with a legend.
- "Most correlated" / "least correlated" pair tables below the chart, deduplicated
  (A-vs-B and B-vs-A collapsed to one row).
- CSV download (styled dropdown with toast).

### 4.4 Update Data (`pages/3_Update_Data.py`)
- Ticker health check expander (`validate_tickers`) — run on demand, not automatic.
- "Update Data" button: progress bar + scrolling log, driven by `update_all()`'s
  `log_fn` callback. Summary metrics (updated / up-to-date / failed) and a
  failure banner after the run.
- Custom stock add form: ticker + sector assignment, fetches full history immediately.

## 5. App shell (`app.py`)

Landing page with the shared `components/header.render_header()` (title, subtitle,
last-update badge), headline `st.metric` cards, Top-3 outperformers, and the
responsive sector card grid. Page navigation is Streamlit's built-in multi-page
mechanism (alphanumeric-prefixed files in `pages/`) — no custom router.

### 5.1 UI layer (`components/`)

`components/` is the only non-page layer allowed to import `streamlit`. It must
stay thin: rendering, CSS, and theme state only. Business logic lives in `modules/`.
- `theme.py` — global CSS, Material Symbols font, dark-mode toggle (sidebar) + `plotly_theme()`.
- `header.py` — shared header/badges (single "Last data update" source).
- `cards.py` — sector card grid + Top-3.
- `legends.py` / `banners.py` / `downloads.py` / `icons.py` — legend bars,
  warning banners, CSV download menu, and icon helpers.

## 6. Non-goals (explicitly out of scope for this version)

- No database — Parquet + JSON metadata only.
- No authentication/multi-user support.
- No scheduled/automatic *network* updates — manual trigger only. Auto-refresh on
  the Heatmap page re-renders local parquet (never fetches from Yahoo).
- No NSE-direct data fallback (Yahoo Finance only); coverage gaps are surfaced,
  not patched, by `validate_tickers()`.
- No options/derivatives data.

## 7. Dependencies

See `requirements.txt`: `streamlit`, `pandas`, `numpy`, `yfinance`, `plotly`, `pyarrow`.
