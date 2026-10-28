"""
trend_builder.py
Figure factories for the Trend Explorer: overlay line charts, per-instrument
mini charts (for grid/tabs layout), rolling returns, and relative strength.
"""

import pandas as pd
import plotly.graph_objects as go


def _empty_fig(message: str, template: str = "plotly_white") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=14))
    fig.update_layout(height=300, xaxis_visible=False, yaxis_visible=False, template=template)
    return fig


def overlay_chart(series_map: dict, title: str, y_label: str, template: str = "plotly_white") -> go.Figure:
    """series_map: {name: pd.Series}. One line per instrument, shared axes."""
    if not series_map:
        return _empty_fig("Select at least one sector or stock", template)

    fig = go.Figure()
    for name, series in series_map.items():
        if series.empty:
            continue
        fig.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines", name=name))

    fig.update_layout(
        title=title,
        yaxis_title=y_label,
        xaxis_title="Date",
        height=450,
        template=template,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def single_line_chart(name: str, series: pd.Series, y_label: str, template: str = "plotly_white") -> go.Figure:
    """One instrument's line, sized for grid-cell display."""
    if series.empty:
        return _empty_fig("No data", template)
    fig = go.Figure(go.Scatter(x=series.index, y=series.values, mode="lines", name=name))
    fig.update_layout(
        title=name,
        yaxis_title=y_label,
        height=280,
        template=template,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
    )
    return fig


def grid_columns(n_items: int) -> int:
    """Auto layout: 2x2 for <=4, 3x2 for <=6, 4x3 beyond that."""
    if n_items <= 4:
        return 2
    if n_items <= 6:
        return 3
    return 4
