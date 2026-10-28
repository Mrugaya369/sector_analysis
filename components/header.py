"""
header.py
Shared page header: title, subtitle, and status badges (last update,
auto-refresh). Single source of truth so "Last data update" never repeats.
"""

import streamlit as st

from components.icons import material_icon


def render_header(
    title: str = "Sector Rotation Heatmap",
    subtitle: str = "India Markets — NSE sector rotation & trend analysis",
    last_update: str | None = None,
    auto_refresh: bool = False,
) -> None:
    """Render the page header with an optional last-update and auto-refresh badge."""
    badges = []
    if last_update:
        badges.append(
            f'<span class="badge">{material_icon("schedule", 15)}Last data update: {last_update}</span>'
        )
    if auto_refresh:
        badges.append(
            f'<span class="badge">{material_icon("autorenew", 15)}Auto-refresh: every 5 min</span>'
        )
    html = f'<div class="app-header"><h1>{title}</h1><div class="subtitle">{subtitle}</div>'
    if badges:
        html += '<div class="badges">' + "".join(badges) + "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
