"""
heatmap_builder.py
Turns a returns matrix into a Plotly heatmap. No data logic lives here.
"""

import numpy as np
import plotly.graph_objects as go


def _symmetric_limits(z: np.ndarray) -> float:
    """Absolute max return so the diverging scale stays symmetric around 0."""
    flat = np.asarray(z, dtype=float)
    finite = flat[np.isfinite(flat)]
    return float(np.max(np.abs(finite))) if finite.size else 1.0


def build_heatmap(
    returns_df,
    ranks_df=None,
    title: str = "Sector rotation heatmap",
    template: str = "plotly_white",
) -> go.Figure:
    """
    returns_df: DataFrame with instruments as rows, timeframes as columns,
    values as % returns (may contain NaN for missing history).
    ranks_df: optional same-shaped DataFrame of column-wise ranks (1 = best),
    surfaced in the hover tooltip.
    """
    z = returns_df.values
    text = [[f"{v:.2f}%" if v == v else "n/a" for v in row] for row in z]

    customdata = None
    hovertemplate = "Sector: %{y}<br>Timeframe: %{x}<br>Return: %{z:.2f}%"
    if ranks_df is not None:
        customdata = [[f"#{int(r)}" if r == r else "n/a" for r in row] for row in ranks_df.values]
        hovertemplate += "<br>Rank: %{customdata}"
    hovertemplate += "<extra></extra>"

    zmax = _symmetric_limits(z)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=returns_df.columns,
            y=returns_df.index,
            text=text,
            texttemplate="%{text}",
            colorscale="RdYlGn",
            zmid=0,
            zmin=-zmax,
            zmax=zmax,
            hovertemplate=hovertemplate,
            customdata=customdata,
            colorbar=dict(title="% return", thickness=12),
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Timeframe",
        yaxis_title="Sector",
        height=max(320, 90 + 34 * len(returns_df)),
        template=template,
        font=dict(size=11),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def build_correlation_heatmap(
    corr_df,
    title: str = "Sector correlation matrix",
    template: str = "plotly_white",
) -> go.Figure:
    """
    corr_df: square DataFrame of pairwise correlations (-1 to 1), same
    instrument set on both axes.
    """
    z = corr_df.values
    text = [[f"{v:.2f}" if v == v else "n/a" for v in row] for row in z]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=corr_df.columns,
            y=corr_df.index,
            text=text,
            texttemplate="%{text}",
            colorscale="RdBu",
            zmid=0,
            zmin=-1,
            zmax=1,
            hovertemplate="%{y} vs %{x}: %{z:.2f}<extra></extra>",
            colorbar=dict(title="corr", thickness=12),
        )
    )
    fig.update_layout(
        title=title,
        height=max(400, 40 * len(corr_df)),
        template=template,
        font=dict(size=11),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig
