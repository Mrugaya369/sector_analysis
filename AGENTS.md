# AGENTS.md

Instructions for AI coding agents (Claude Code, Copilot, etc.) working in this repository.

## Project

NSE Sector Dashboard — a Streamlit app for sector rotation and trend analysis on NSE
sector indices and stocks, using daily data from Yahoo Finance stored locally as Parquet.

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

No API keys, no database, no `.env` file. All state is on disk under `data/`.

## Architecture rules (do not violate)

1. **`modules/` never imports `streamlit`.** Modules are pure Python — data fetch,
   computation, and figure factories. Only files in `pages/`, `app.py`, and the
   `components/` UI layer may import `streamlit` or read `st.session_state`.
   `components/` must stay thin (rendering + CSS only — no business logic) and
   must never import `modules/fetch_data.py` (network) or mutate on-disk data.
2. **`compute_returns.py` never calls the network.** It only reads Parquet already
   on disk via `utils.load_price_data()`. All network calls live in `fetch_data.py`.
3. **`heatmap_builder.py` / `trend_builder.py` never load data themselves.** They
   take a DataFrame or dict of Series as input and return a `plotly.graph_objects.Figure`.
   Do not add `pd.read_parquet` calls to these files.
4. **One Parquet file per instrument**, named via `utils.ticker_to_filename()`.
   Never write a combined multi-instrument Parquet file — it breaks incremental
   updates and per-instrument caching.
5. **Fetches are always incremental.** `fetch_data.update_instrument()` must
   continue reading the last date already on disk and requesting only newer
   rows. Do not change this to a full re-download unless explicitly asked.
6. **Constants belong in `utils.py`** — ticker maps, default stock lists,
   timeframe windows. Do not hardcode tickers or day-counts inside pages.

## Conventions

- Type hints on all function signatures (`str | None` etc., Python 3.10+ syntax).
- Every public function gets a one-line docstring stating what it returns.
- Keep functions short — if a function in `modules/` exceeds ~40 lines, split it.
- No classes unless there's real shared state to hold. Prefer plain functions.
- Cache expensive reads at the page level with `st.cache_data`, not inside modules.
- Currency/returns are always expressed as **percent** (e.g. `2.5` means 2.5%),
  never as a raw ratio (`0.025`). Keep this consistent across all new metrics.

## Testing changes

There is no formal test suite. Before submitting a change:

```bash
python3 -m py_compile modules/*.py pages/*.py components/*.py app.py
```

For logic changes to `compute_returns.py` or `fetch_data.py`, write a throwaway
synthetic-data smoke test (synthetic OHLCV DataFrame → parquet → call the
function → assert shape/values), run it, then discard it. Do not commit test
scripts into the repo — there is no `tests/` directory by design; keep the
project scope small.

## Adding a new page

1. Add computation to the relevant `modules/*.py` file (or a new module if it's
   a genuinely new concern — e.g. correlation logic went into `compute_returns.py`,
   not a new file, because it's still "return-derived computation").
2. Add a figure factory to `heatmap_builder.py` or `trend_builder.py` if it's a
   new chart type, or reuse an existing one.
3. Add `pages/N_Page_Name.py` (N = next number in sequence). Keep the page thin:
   selection UI → module calls → render. No business logic in the page file.
4. Update `specification.md` with the new page's purpose and behavior.

## Known limitations (do not "fix" without asking)

- Some NSE sector indices (PSU Bank, Media, Infra) are unreliable or missing on
  Yahoo Finance. This is a data-source limitation, not a bug — `validate_tickers()`
  in `fetch_data.py` is the intended mitigation, not a full NSE-direct fallback.
- No scheduled/cron update — updates are manually triggered from the
  Update Data page by design (see specification.md for rationale).
- Auto-refresh (Heatmap page `@st.fragment(run_every=300)`) is a **re-render only**:
  it re-reads local parquet and never calls the network. It must not be replaced
  with a scheduled Yahoo fetch without an explicit request.
- FY is hardcoded to Apr 1 – Mar 31 (Indian financial year). Do not change to
  calendar year without an explicit request.
