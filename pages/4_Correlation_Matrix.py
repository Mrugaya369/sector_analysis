"""
4_Correlation_Matrix.py
Pairwise correlation of daily returns across sectors (and optionally stocks),
over a user-selected lookback window.
"""

import pandas as pd
import streamlit as st

from modules.utils import SECTOR_TICKERS, get_last_update, list_available
from modules.compute_returns import daily_return_series
from modules.heatmap_builder import build_correlation_heatmap

from components.theme import dark_mode_toggle, inject_global_css, plotly_theme
from components.header import render_header
from components.legends import render_correlation_legend
from components.downloads import render_download_menu

st.set_page_config(page_title="Correlation Matrix", layout="wide", page_icon="🔗")

dark = dark_mode_toggle()
inject_global_css(dark)
render_header(
    "Sector Correlation Matrix",
    "India Markets — how closely sector returns move together",
    last_update=get_last_update(),
)

sector_names = list(SECTOR_TICKERS.keys())
stock_names = list_available("stock")

c1, c2 = st.columns([2, 1])
with c1:
    include_stocks = st.multiselect("Add stocks to the matrix (optional)", stock_names)
with c2:
    lookback = st.select_slider(
        "Lookback window (trading days)", options=[21, 63, 126, 252], value=126
    )

selected = sector_names + include_stocks


@st.cache_data(ttl=3600)
def get_correlation_matrix(names: list, lookback_days: int) -> pd.DataFrame:
    """Correlation of daily returns over the lookback window for the given names."""
    series_map = {}
    for name in names:
        kind = "sector" if name in SECTOR_TICKERS else "stock"
        series_map[name] = daily_return_series(name, kind, lookback_days)
    combined = pd.DataFrame(series_map).dropna(how="all")
    return combined.corr() if not combined.empty else pd.DataFrame()


corr_df = get_correlation_matrix(selected, lookback)

if corr_df.empty:
    st.info("No data found yet. Go to **Update Data** to fetch it first.")
else:
    st.markdown(
        f"#### Correlation of daily returns — last {lookback} trading days"
    )
    render_correlation_legend()
    fig = build_correlation_heatmap(
        corr_df,
        title=f"Correlation of daily returns — last {lookback} trading days",
        template=plotly_theme(dark),
    )
    st.plotly_chart(fig, width="stretch")

    formats = {
        "Full correlation matrix": (
            corr_df.to_csv().encode("utf-8"),
            "sector_correlation.csv",
        ),
    }
    render_download_menu(formats)

    with st.expander("Most and least correlated pairs"):
        pairs = (
            corr_df.where(~corr_df.isna())
            .stack()
            .reset_index()
        )
        pairs.columns = ["Instrument A", "Instrument B", "Correlation"]
        pairs = pairs[pairs["Instrument A"] != pairs["Instrument B"]]
        pairs["pair_key"] = pairs.apply(lambda r: tuple(sorted([r["Instrument A"], r["Instrument B"]])), axis=1)
        pairs = pairs.drop_duplicates("pair_key").drop(columns="pair_key")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Most correlated**")
            st.dataframe(
                pairs.sort_values("Correlation", ascending=False).head(5),
                hide_index=True,
            )
        with col_b:
            st.markdown("**Least correlated / most diversifying**")
            st.dataframe(
                pairs.sort_values("Correlation").head(5),
                hide_index=True,
            )
