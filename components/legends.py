"""
legends.py
Color legend bars rendered above the charts so the red → yellow → green
(and blue → red) mappings are self-explanatory.
"""

import streamlit as st


def render_return_legend() -> None:
    """Red → yellow → green gradient bar for the sector-returns heatmap."""
    st.markdown(
        '<div class="legend"><span>Red = underperformance</span>'
        '<div class="legend-bar green"></div>'
        '<span>Green = outperformance</span></div>'
        '<div style="font-size:0.75rem;opacity:0.6;margin:-0.7rem 0 0.6rem;">'
        "Returns are % change over the labelled timeframe. Yellow \u2248 flat. "
        "Hover any cell for sector, return, and rank.</div>",
        unsafe_allow_html=True,
    )


def render_correlation_legend() -> None:
    """Blue → white → red gradient bar for the correlation matrix."""
    st.markdown(
        '<div class="legend"><span>&minus;1 (opposite)</span>'
        '<div class="legend-bar corr"></div>'
        '<span>+1 (moves together)</span></div>',
        unsafe_allow_html=True,
    )
