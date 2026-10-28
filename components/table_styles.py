"""
table_styles.py
Matplotlib-free DataFrame styling for the raw-returns table. pandas'
`Styler.background_gradient` requires matplotlib, so we interpolate the
RdYlGn colors manually and apply them via `Styler.map`.
"""

from __future__ import annotations

import pandas as pd

_RED = (215, 25, 28)
_YELLOW = (255, 255, 191)
_GREEN = (26, 150, 41)


def _rdylgn_css(value, lo: float, hi: float) -> str | None:
    """CSS background color for `value` on a red→yellow→green scale, or None if blank."""
    if pd.isna(value) or lo == hi:
        return None
    t = max(0.0, min(1.0, (value - lo) / (hi - lo)))
    if t < 0.5:  # red → yellow
        s = t * 2
        rgb = tuple(int(a + (b - a) * s) for a, b in zip(_RED, _YELLOW))
    else:  # yellow → green
        s = (t - 0.5) * 2
        rgb = tuple(int(a + (b - a) * s) for a, b in zip(_YELLOW, _GREEN))
    return f"background-color: rgba({rgb[0]},{rgb[1]},{rgb[2]},0.55)"


def style_returns_table(table: pd.DataFrame, value_cols: list, focus: str) -> pd.io.formats.style.Styler:
    """
    Return a styled version of the returns table: %-formatted values, integer
    ranks, and a symmetric red→yellow→green background on the focus column.
    """
    focus = focus if focus in value_cols else None
    hi = table[focus].max() if focus else 0.0
    lo = table[focus].min() if focus else 0.0
    limit = max(abs(lo), abs(hi)) or 1.0  # keep the scale symmetric around 0

    formatters = {c: "{:.2f}%" for c in value_cols}
    formatters["Rank"] = "{:.0f}"

    styler = table.style.format(formatters, na_rep="n/a")
    if focus:
        styler = styler.map(lambda v: _rdylgn_css(v, -limit, limit), subset=[focus])
    return styler
