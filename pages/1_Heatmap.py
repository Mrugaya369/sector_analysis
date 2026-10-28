"""
1_Heatmap.py
Sector rotation heatmap: rows = sectors, columns = timeframes. Highlights the
top sectors, ranks each column, exposes a color legend, a ranked raw-returns
table, and a styled CSV download. Auto-refreshes from local parquet every 5 min.
"""

import pandas as pd
import streamlit as st

from modules.utils import (
    FOCUS_TIMEFRAMES,
    MOMENTUM_LABEL,
    SECTOR_TICKERS,
    get_last_update,
    stale_days,
)
from modules.compute_returns import build_returns_matrix, rank_matrix, trend_direction
from modules.heatmap_builder import build_heatmap

from components.theme import dark_mode_toggle, inject_global_css, plotly_theme
from components.header import render_header
from components.legends import render_return_legend
from components.banners import render_data_gap_banner, render_stale_data_banner
from components.cards import render_sector_grid, render_top3
from components.downloads import render_download_menu
from components.table_styles import style_returns_table

st.set_page_config(page_title="Heatmap", layout="wide", page_icon="🗺️")

dark = dark_mode_toggle()
inject_global_css(dark)
render_header(
    "Sector Rotation Heatmap",
    "India Markets — sector rotation across timeframes",
    last_update=get_last_update(),
    auto_refresh=True,
)


@st.cache_data(ttl=240)
def get_returns_matrix() -> pd.DataFrame:
    """All sectors' returns as of the latest shared trading date."""
    return build_returns_matrix(list(SECTOR_TICKERS.keys()), kind="sector")


def _history_issues(returns_df: pd.DataFrame) -> tuple:
    """(sectors with no data, sectors with partial history)."""
    missing, partial = [], []
    for name in returns_df.index:
        row = returns_df.loc[name]
        if row.dropna().empty:
            missing.append(name)
        elif row.isna().any():
            partial.append(name)
    return missing, partial


def _ranked_table(returns_df: pd.DataFrame, ranks_df: pd.DataFrame, focus: str, trend_map: dict) -> pd.DataFrame:
    """Raw returns table with rank and trend arrow columns, sorted by `focus`."""
    table = returns_df.copy()
    rank_key = focus if focus in ranks_df.columns else MOMENTUM_LABEL
    table.insert(0, "Rank", ranks_df[rank_key])
    table.insert(
        1,
        "Trend",
        table.index.map(lambda n: "▲" if trend_map.get(n, 0) > 0 else ("▼" if trend_map.get(n, 0) < 0 else "—")),
    )
    return table.sort_values("Rank", ascending=True, na_position="last")


@st.fragment(run_every=300)
def render_dashboard() -> None:
    """Data section: banners, focus selector, heatmap, cards, table, download."""
    returns_df = get_returns_matrix()

    missing, partial = _history_issues(returns_df)
    render_data_gap_banner(missing, partial)
    render_stale_data_banner(stale_days())

    if returns_df.empty or returns_df.dropna(how="all").empty:
        st.info("No sector data found yet. Go to **Update Data** to fetch it first.")
        st.stop()

    ranks_df = rank_matrix(returns_df)
    trend_map = {name: trend_direction(name, "sector") for name in SECTOR_TICKERS}

    focus_options = FOCUS_TIMEFRAMES + [MOMENTUM_LABEL]
    focus = st.segmented_control(
        "Focus timeframe",
        options=focus_options,
        default="1M",
        help="Drives the ranking, the sector-card ranks, and the table sort.",
    )

    st.markdown("#### Sector rotation — returns across timeframes (%)")
    render_return_legend()
    fig = build_heatmap(
        returns_df,
        ranks_df=ranks_df,
        title="Sector rotation — returns across timeframes (%)",
        template=plotly_theme(dark),
    )
    st.plotly_chart(fig, width="stretch")

    render_top3(returns_df, trend_map)
    render_sector_grid(returns_df, trend_map, ranks_df, focus)

    st.markdown("#### Raw returns table")
    table = _ranked_table(returns_df, ranks_df, focus, trend_map)
    value_cols = [c for c in returns_df.columns if c in table]
    styled = style_returns_table(table, value_cols, focus)
    st.dataframe(styled, width="stretch", hide_index=True)

    _render_download_menu(returns_df, table)


def _render_download_menu(returns_df: pd.DataFrame, ranked_table: pd.DataFrame) -> None:
    """CSV export options (full matrix / ranked / transposed) with a toast."""
    formats = {
        "Full returns matrix": (
            returns_df.to_csv().encode("utf-8"),
            "sector_returns_full.csv",
        ),
        "Ranked returns table": (
            ranked_table.to_csv().encode("utf-8"),
            "sector_returns_ranked.csv",
        ),
        "Transposed (timeframes × sectors)": (
            returns_df.T.to_csv().encode("utf-8"),
            "sector_returns_transposed.csv",
        ),
    }
    render_download_menu(formats)


render_dashboard()
