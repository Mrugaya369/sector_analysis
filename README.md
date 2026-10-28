# Sector Rotation Heatmap — India Markets

A production-ready **Streamlit** dashboard for sector rotation and trend analysis on
NSE (National Stock Exchange, India) sector indices and their constituent stocks.
Data comes from **Yahoo Finance** and is cached locally as Parquet — no API keys,
no database, no external service required.

![Dashboard preview](docs/screenshot_landing.png)

> Screenshots are placeholders — add your own under `docs/` after running the app.

---

## Features

- **Sector rotation heatmap** — 12 NSE sector indices × timeframes (1D, 1W, 1M, 3M, 6M, 1Y, FY, CY)
  with a red → yellow → green diverging scale and a visual color legend.
- **Hover tooltips** — every heatmap cell shows the sector name, return %, timeframe, and rank.
- **Rankings & momentum** — a weighted **Momentum Score** (0.5·1M + 0.3·3M + 0.2·6M), column-wise
  ranks, and ▲/▼ trend arrows per sector.
- **Top 3 outperformers** — a dedicated highlight section ranked by momentum.
- **Sector card grid** — responsive cards with momentum, 1M/6M returns, rank, and trend arrow.
- **Raw returns table** — always-visible, color-graded, sortable by any timeframe.
- **CSV export** — a styled **Download as CSV** dropdown (full matrix / ranked / transposed)
  with a toast confirmation.
- **Trend Explorer** — compare any sectors/stocks in Overlay, Grid, or Tabs across
  trend, rolling returns, relative strength vs NIFTY 50, and normalized price.
- **Correlation Matrix** — pairwise correlation of daily returns with most/least-correlated pairs.
- **Update Data** — incremental Yahoo Finance fetches with progress bar, ticker health check,
  and custom-stock adding.
- **Dark mode toggle**, **auto-refresh every 5 minutes**, and **data-availability banners**
  that fall back to last cached values.
- **Responsive** layout for mobile and tablet via CSS media queries.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit (widgets, fragments, popovers, pills, segmented controls) |
| Charts | Plotly (heatmaps, line charts) |
| Data | pandas + NumPy |
| Data source | yfinance (Yahoo Finance) |
| Storage | Parquet (one file per instrument) + JSON metadata |

## Project structure

```
sector_dashboard/
├── app.py                  # Landing page: header, metrics, sector cards, Top-3
├── pages/                  # Streamlit multi-page app
│   ├── 1_Heatmap.py        # Sector rotation heatmap + rankings + CSV export
│   ├── 2_Trend_Explorer.py # Trend / rolling / relative strength / normalized charts
│   ├── 3_Update_Data.py    # Incremental data updates + custom stocks
│   └── 4_Correlation_Matrix.py
├── components/             # Streamlit UI layer (the only place importing streamlit)
│   ├── theme.py            # Global CSS, dark mode toggle, plotly theme
│   ├── header.py           # Shared page header + status badges
│   ├── cards.py            # Sector card grid + Top-3 highlight
│   ├── legends.py          # Heatmap color legends
│   ├── banners.py          # Stale / missing-data warning banners
│   ├── downloads.py        # CSV download dropdown with toast
│   └── icons.py            # Material Symbols + SVG arrow helpers
├── modules/                # Pure logic — never imports streamlit
│   ├── utils.py            # Constants, paths, metadata helpers
│   ├── compute_returns.py  # Returns engine, momentum, ranks, trend direction
│   ├── heatmap_builder.py  # Plotly heatmap factories
│   ├── trend_builder.py    # Plotly line-chart factories
│   └── fetch_data.py       # Incremental Yahoo Finance fetcher
├── data/                   # Generated at runtime
│   ├── sectors/*.parquet
│   ├── stocks/*.parquet
│   ├── metadata.json
│   └── last_update.txt
└── .streamlit/config.toml  # Base theme
```

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/your-user/sector_analysis.git
cd sector_analysis/sector_dashboard

# 2. Create and activate a virtual environment (optional but recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Open http://localhost:8501 in your browser. Head to **Update Data** first if the
sector/stock counts show 0.

## API usage

There is no REST API — the "API" is the pure-Python `modules/` layer:

```python
from modules.utils import SECTOR_TICKERS
from modules.compute_returns import build_returns_matrix, momentum_score, rank_matrix

matrix = build_returns_matrix(list(SECTOR_TICKERS), kind="sector")  # DataFrame of % returns
ranks = rank_matrix(matrix)                                          # column-wise ranks (1 = best)
score = momentum_score("NIFTY IT", "sector")                         # weighted momentum score
```

For scheduled updates outside the app:

```python
from modules.fetch_data import update_all
from modules.utils import SECTOR_TICKERS, DEFAULT_STOCKS

update_all(SECTOR_TICKERS, DEFAULT_STOCKS)  # run from cron, then reload the app
```

The auto-refresh on the Heatmap page re-reads this local data every 5 minutes, so
externally updated data appears without a manual reload.

## Data & design notes

- **Universe:** 12 NSE sector indices (`modules/utils.py::SECTOR_TICKERS`) + default
  constituents per sector + any user-added custom tickers.
- **Incremental updates:** only rows newer than what's on disk are fetched
  (`modules/fetch_data.py::update_instrument`).
- **Consistency:** all returns are computed as of the latest trading date shared by
  every sector, so no row is "ahead" of another. Missing history renders as `n/a`.
- **FY** is the Indian financial year (Apr 1 – Mar 31); **CY** is the calendar year.
- Some NSE indices (PSU Bank, Media, Infra) are unreliable on Yahoo Finance —
  the app surfaces these with a "Data unavailable — showing last cached values"
  banner instead of failing silently.

## Roadmap

- [x] Core heatmap with rankings, legend, hover tooltips, CSV export
- [x] Momentum score, trend arrows, Top-3 highlight
- [x] Dark mode toggle and responsive layout
- [x] Auto-refresh + stale/cached-data banners
- [ ] NSE-direct data fallback for missing indices
- [ ] Full backtest engine for rotation strategies
- [ ] Multi-period relative-strength screener
- [ ] Docker deployment + scheduled cron update
- [ ] Automated tests (`pytest`)

## License

MIT
