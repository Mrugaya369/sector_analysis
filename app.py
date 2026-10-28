"""
app.py
Landing page for the Sector Rotation Heatmap. Shows headline metrics, the
sector card grid, and the Top-3 outperformers. Page navigation is handled
automatically by Streamlit's multi-page mechanism (files in pages/).
"""

import pandas as pd
import streamlit as st

from modules.utils import SECTOR_TICKERS, get_last_update, list_available, stale_days
from modules.compute_returns import build_returns_matrix, rank_matrix, trend_direction

from components.theme import dark_mode_toggle, inject_global_css
from components.header import render_header
from components.banners import render_data_gap_banner, render_stale_data_banner
from components.cards import render_sector_grid, render_top3

st.set_page_config(page_title="Sector Rotation Heatmap — India Markets", layout="wide", page_icon="📊")

dark = dark_mode_toggle()
inject_global_css(dark)
render_header(
    "Sector Rotation Heatmap",
    "India Markets — NSE sector rotation & trend analysis, built on daily Yahoo Finance data.",
    last_update=get_last_update(),
)


@st.cache_data(ttl=240)
def get_returns_matrix() -> pd.DataFrame:
    """All sectors' returns, including the momentum score column."""
    return build_returns_matrix(list(SECTOR_TICKERS.keys()), kind="sector")


returns_df = get_returns_matrix()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Sectors tracked", len(list_available("sector")))
col2.metric("Stocks tracked", len(list_available("stock")))
col3.metric("Last data update", get_last_update())
col4.metric("Sectors with data", int((~returns_df.isna().all(axis=1)).sum()))

st.divider()

if returns_df.empty or returns_df.dropna(how="all").empty:
    st.info("No sector data found yet. Go to **Update Data** to fetch it first.")
else:
    ranks_df = rank_matrix(returns_df)
    trend_map = {name: trend_direction(name, "sector") for name in SECTOR_TICKERS}

    missing = [name for name in returns_df.index if returns_df.loc[name].dropna().empty]
    render_data_gap_banner(missing)
    render_stale_data_banner(stale_days())

    render_top3(returns_df, trend_map)
    render_sector_grid(returns_df, trend_map, ranks_df, focus="Momentum")

    st.divider()
    st.markdown(
        """
        #### Navigate using the sidebar
        - **Heatmap** — sector rotation across timeframes, color-coded, with rankings and CSV export
        - **Trend Explorer** — compare sectors/stocks with overlay, grid, or tab layouts
        - **Correlation Matrix** — pairwise correlation of daily returns
        - **Update Data** — pull the latest daily bars from Yahoo Finance

        If sector or stock counts above show 0, head to **Update Data** first.
        """
    )
