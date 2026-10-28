"""
2_Trend_Explorer.py
Compare any number of sectors/stocks across trend, rolling returns,
relative strength, and normalized price — in overlay, grid, or tab layout.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from modules.utils import (
    BENCHMARK_TICKER,
    SECTOR_TICKERS,
    get_last_update,
    list_available,
    load_price_data,
)
from modules.compute_returns import (
    normalized_price_series,
    relative_strength_series,
    rolling_return_series,
)
from modules.trend_builder import grid_columns, overlay_chart, single_line_chart

from components.theme import dark_mode_toggle, inject_global_css, plotly_theme
from components.header import render_header

st.set_page_config(page_title="Trend Explorer", layout="wide", page_icon="📈")

dark = dark_mode_toggle()
inject_global_css(dark)
render_header(
    "Trend Explorer",
    "India Markets — compare sectors and stocks over time",
    last_update=get_last_update(),
)

# --- Selection controls -----------------------------------------------------
sector_names = list(SECTOR_TICKERS.keys())
stock_names = list_available("stock")

with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        selected_sectors = st.multiselect("Sectors", sector_names, default=sector_names[:3])
        selected_stocks = st.multiselect("Stocks", stock_names)
    with c2:
        start_date = st.date_input("From", value=date.today() - timedelta(days=180))
        end_date = st.date_input("To", value=date.today())
        comparison_mode = st.pills(
            "Layout",
            ["Overlay", "Grid", "Tabs"],
            default="Overlay",
            help="How to arrange the selected instruments' charts.",
        )

selection = [(name, "sector") for name in selected_sectors] + [(name, "stock") for name in selected_stocks]

if not selection:
    st.info("Pick at least one sector or stock above to begin.")
    st.stop()

template = plotly_theme(dark)

# --- Chart type tabs ---------------------------------------------------------
tab_price, tab_rolling, tab_rs, tab_norm = st.tabs(
    ["Trend line", "Rolling returns", "Relative strength vs NIFTY", "Normalized comparison"]
)


def render(series_map, title, y_label):
    """Route to overlay / grid / tabs based on the user's chosen layout."""
    if comparison_mode == "Overlay":
        st.plotly_chart(overlay_chart(series_map, title, y_label, template), width="stretch")
    elif comparison_mode == "Grid":
        names = list(series_map.keys())
        n_cols = grid_columns(len(names))
        cols = st.columns(n_cols)
        for i, name in enumerate(names):
            with cols[i % n_cols]:
                st.plotly_chart(
                    single_line_chart(name, series_map[name], y_label, template),
                    width="stretch",
                )
    else:  # Tabs
        chart_tabs = st.tabs(list(series_map.keys()))
        for tab, name in zip(chart_tabs, series_map.keys()):
            with tab:
                st.plotly_chart(
                    single_line_chart(name, series_map[name], y_label, template),
                    width="stretch",
                )


with tab_price:
    series_map = {
        name: load_price_data(name, kind)["Close"].loc[str(start_date):str(end_date)]
        for name, kind in selection
        if not load_price_data(name, kind).empty
    }
    render(series_map, "Price trend", "Price")

with tab_rolling:
    window = st.select_slider("Rolling window (trading days)", options=[5, 21, 63, 126], value=21)
    series_map = {name: rolling_return_series(name, kind, window) for name, kind in selection}
    render(series_map, f"{window}-day rolling return", "% return")

with tab_rs:
    benchmark = load_price_data("NIFTY 50", "sector")
    if benchmark.empty or "Close" not in benchmark:
        import yfinance as yf  # local import: only needed for this on-demand benchmark pull

        raw = yf.download(BENCHMARK_TICKER, period="2y", progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        benchmark = raw
    benchmark_close = benchmark["Close"].dropna() if not benchmark.empty else pd.Series(dtype=float)
    series_map = {name: relative_strength_series(name, kind, benchmark_close) for name, kind in selection}
    render(series_map, "Relative strength vs NIFTY 50 (rebased to 100)", "Relative strength")

with tab_norm:
    series_map = {name: normalized_price_series(name, kind, start_date) for name, kind in selection}
    render(series_map, "Normalized price (rebased to 100)", "Index (start = 100)")
