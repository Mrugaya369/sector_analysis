"""
banners.py
Status banners for missing / stale / partial data. The "Data unavailable"
banner tells users when only last cached values are being shown.
"""

import streamlit as st

from components.icons import material_icon


def render_data_gap_banner(missing: list, partial: list | None = None) -> None:
    """Warn when sectors have no on-disk data, or only partial history."""
    partial = partial or []
    if missing:
        st.markdown(
            '<div class="warn-banner">'
            f'{material_icon("warning", 20)}'
            '<div><strong>&#9888;&#65039; Data unavailable — showing last cached values.</strong>'
            f"No data on disk for: <b>{', '.join(missing)}</b>.</div></div>",
            unsafe_allow_html=True,
        )
    if partial:
        st.caption(f"Partial history (some timeframes show n/a): {', '.join(partial)}")


def render_stale_data_banner(stale_days: int, threshold: int = 3) -> None:
    """Warn when the local data is older than `threshold` days."""
    if stale_days is None or stale_days < threshold:
        return
    st.markdown(
        '<div class="warn-banner">'
        f'{material_icon("schedule", 20)}'
        "<div><strong>Stale data detected.</strong>"
        f"Last update was {stale_days} day(s) ago. Run <b>Update Data</b> to refresh.</div></div>",
        unsafe_allow_html=True,
    )


def render_fetch_failure_banner(failed: list) -> None:
    """Warn when an update run failed for some instruments (only cached values remain)."""
    if not failed:
        return
    st.markdown(
        '<div class="warn-banner">'
        f'{material_icon("error", 20)}'
        "<div><strong>Some instruments could not be fetched.</strong> "
        "Showing last cached values for: "
        f"<b>{', '.join(failed[:10])}</b>{'…' if len(failed) > 10 else ''}.</div></div>",
        unsafe_allow_html=True,
    )
