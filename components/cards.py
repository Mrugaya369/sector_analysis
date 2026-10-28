"""
cards.py
Sector card grid and "Top 3 outperforming sectors" highlight, rendered as
a responsive CSS grid via unsafe_allow_html.
"""

import pandas as pd
import streamlit as st

from components.icons import material_icon, trend_arrow
from modules.utils import MOMENTUM_LABEL


def _is_na(value) -> bool:
    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def _fmt(value, plus: bool = True, decimals: int = 1) -> str:
    if _is_na(value):
        return "n/a"
    return f"{value:+.{decimals}f}%" if plus else f"{value:.{decimals}f}%"


def _color_class(value) -> str:
    if _is_na(value):
        return "flat"
    if value > 0:
        return "pos"
    if value < 0:
        return "neg"
    return "flat"


def _color_hex(value) -> str:
    if _is_na(value) or value == 0:
        return "#6b7280"
    return "#16a34a" if value > 0 else "#dc2626"


def render_sector_grid(
    returns_df: pd.DataFrame,
    trend_map: dict | None = None,
    ranks_df: pd.DataFrame | None = None,
    focus: str = "1M",
) -> None:
    """Responsive card grid: name, momentum, 1M/6M, rank, trend arrow."""
    if returns_df is None or returns_df.empty:
        return
    trend_map = trend_map or {}
    cards = []
    for name, row in returns_df.iterrows():
        momentum = row.get(MOMENTUM_LABEL)
        arrow = trend_arrow(trend_map.get(name, 0), 13)

        rank = None
        if ranks_df is not None and focus in ranks_df and name in ranks_df.index:
            value = ranks_df.loc[name, focus]
            rank = value if not _is_na(value) else None
        rank_html = ""
        if rank is not None:
            rank_html = (
                f'<span class="rank-badge">{material_icon("emoji_events", 12)} #{int(rank)}</span>'
            )

        cards.append(
            f'<div class="sector-card" style="border-top-color:{_color_hex(momentum)};">'
            f'<div class="name">{name} {arrow}{rank_html}</div>'
            f'<div class="meta"><span>Momentum</span>'
            f'<span class="mom {_color_class(momentum)}">{_fmt(momentum)}</span></div>'
            f'<div class="meta"><span>1M</span><span class="{_color_class(row.get("1M"))}">{_fmt(row.get("1M"))}</span>'
            f'<span>6M</span><span class="{_color_class(row.get("6M"))}">{_fmt(row.get("6M"))}</span></div>'
            f"</div>"
        )

    st.markdown(
        '<div class="section"><h2>Sector overview</h2>'
        f'<div class="sector-grid">{"".join(cards)}</div></div>',
        unsafe_allow_html=True,
    )


def render_top3(returns_df: pd.DataFrame, trend_map: dict | None = None) -> None:
    """Highlight the top 3 sectors by momentum score."""
    if returns_df is None or returns_df.empty or MOMENTUM_LABEL not in returns_df:
        return
    trend_map = trend_map or {}
    top3 = returns_df[MOMENTUM_LABEL].dropna().sort_values(ascending=False).head(3)
    if top3.empty:
        return

    cards = []
    for i, (name, momentum) in enumerate(top3.items(), start=1):
        arrow = trend_arrow(trend_map.get(name, 0), 14)
        one_m = returns_df.loc[name, "1M"]
        six_m = returns_df.loc[name, "6M"]
        cards.append(
            f'<div class="top3-card">'
            f'<div><span class="rank-chip">#{i}</span> {name} {arrow}</div>'
            f'<div class="mom {_color_class(momentum)}" style="font-size:1.3rem;margin-top:0.4rem;">'
            f"{_fmt(momentum)}</div>"
            f'<div style="font-size:0.8rem;opacity:0.75;">1M {_fmt(one_m)} &middot; 6M {_fmt(six_m)}</div>'
            f"</div>"
        )

    st.markdown(
        '<div class="section"><h2>Top 3 outperforming sectors</h2>'
        f'<div class="top3-grid">{"".join(cards)}</div></div>',
        unsafe_allow_html=True,
    )
