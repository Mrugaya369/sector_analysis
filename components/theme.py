"""
theme.py
Global CSS, Material Symbols font loading, and the dark-mode toggle/state.
The toggle lives in the sidebar and flips CSS variables on rerun.
"""

import streamlit as st

_MATERIAL_FONT = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family='
    "Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap\">"
)

_CSS_BASE = """
:root {
  --background-color: #ffffff;
  --secondary-background-color: #f3f6fc;
  --text-color: #111827;
  --primary-color: #1f6feb;
}

/* ---- layout & spacing ---- */
.block-container { padding-top: 1rem; max-width: 1400px; margin: 0 auto; }
[data-testid="stHorizontalBlock"] { gap: 0.5rem; }
.stPlotlyChart, .stDataFrame { margin: 0.4rem 0 1rem; }
.section { margin: 1.6rem 0 0.8rem; }
.section h2 { font-size: 1.12rem; margin: 0 0 0.6rem; }

/* ---- material symbols ---- */
.material-symbols-outlined { user-select: none; }

/* ---- header ---- */
.app-header { text-align: center; padding: 1.2rem 0 0.5rem; }
.app-header h1 { font-size: 2.1rem; margin: 0; letter-spacing: -0.02em; }
.app-header .subtitle { opacity: 0.7; margin-top: 0.25rem; font-size: 0.95rem; }
.app-header .badges { display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin-top: 0.85rem; }
.badge {
  display: inline-flex; align-items: center; gap: 0.35rem;
  background: var(--secondary-background-color);
  border: 1px solid var(--secondary-background-color);
  border-radius: 999px; padding: 0.25rem 0.8rem; font-size: 0.8rem;
}

/* ---- sector cards ---- */
.sector-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(185px, 1fr)); gap: 0.8rem; }
.sector-card {
  background: var(--secondary-background-color); border-radius: 12px;
  padding: 0.85rem 1rem; border-top: 4px solid #6b7280;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.sector-card .name { font-weight: 600; font-size: 0.95rem; }
.sector-card .meta { display: flex; justify-content: space-between; margin-top: 0.45rem; font-size: 0.82rem; }
.sector-card .mom { font-size: 1.05rem; font-weight: 700; }
.pos { color: #15803d; }
.neg { color: #b91c1c; }
.flat { color: #6b7280; }
.rank-badge { float: right; font-size: 0.7rem; background: var(--background-color); border-radius: 999px; padding: 0.1rem 0.5rem; }

/* ---- top 3 ---- */
.top3-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
.top3-card {
  background: var(--secondary-background-color); border: 2px solid var(--primary-color);
  border-radius: 12px; padding: 1rem; text-align: center;
}
.rank-chip {
  display: inline-block; width: 22px; height: 22px; line-height: 22px; border-radius: 50%;
  background: var(--primary-color); color: white; font-size: 0.72rem; font-weight: 700;
}

/* ---- legend ---- */
.legend { display: flex; align-items: center; gap: 0.75rem; margin: 0.3rem 0 1rem; font-size: 0.8rem; }
.legend-bar { flex: 1; height: 12px; border-radius: 6px; }
.legend-bar.green { background: linear-gradient(to right, #d7191c, #ffffbf, #1a9641); }
.legend-bar.corr { background: linear-gradient(to right, #2166ac, #f7f7f7, #b2182b); }

/* ---- warning banner ---- */
.warn-banner {
  display: flex; gap: 0.6rem; align-items: flex-start;
  background: rgba(234, 179, 8, 0.12); border: 1px solid #d97706; color: #92400e;
  border-radius: 10px; padding: 0.7rem 1rem; margin: 1rem 0; font-size: 0.9rem;
}
.warn-banner .icon { flex-shrink: 0; }
.warn-banner strong { display: block; margin-bottom: 0.15rem; }

/* ---- widgets ---- */
[data-testid="stSegmentedControl"] button[aria-checked="true"] {
  background: var(--primary-color); color: white; border-color: var(--primary-color);
}
[data-testid="stPopover"] button { font-weight: 600; }
[data-testid="stMetric"] { background: var(--secondary-background-color); border-radius: 12px; padding: 0.75rem 1rem; }

/* ---- responsive ---- */
@media (max-width: 1024px) {
  .sector-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
}
@media (max-width: 720px) {
  .app-header h1 { font-size: 1.5rem; }
  .sector-grid { grid-template-columns: 1fr 1fr; }
  .top3-grid { grid-template-columns: 1fr; }
  .badges { flex-direction: column; align-items: center; }
}
@media (max-width: 480px) {
  .sector-grid { grid-template-columns: 1fr; }
  [data-testid="stMetric"] { padding: 0.5rem; }
}
"""

_CSS_DARK = """
[data-testid="stAppViewContainer"] {
  background-color: #0e1117; color: #e6edf3;
  --background-color: #0e1117; --text-color: #e6edf3;
  --secondary-background-color: #161b22;
}
[data-testid="stHeader"] { background: #0e1117; }
[data-testid="stSidebar"] {
  background: #161b22; color: #e6edf3;
  --background-color: #161b22; --text-color: #e6edf3;
  --secondary-background-color: #0e1117;
}
.sector-card, .top3-card, .badge { background: #1c2128; border-color: #30363d; box-shadow: none; }
.rank-badge { background: #0e1117; color: #e6edf3; }
.warn-banner { color: #fbbf24; border-color: #b45309; background: rgba(180, 83, 9, 0.18); }
.app-header .subtitle { color: #9aa5b1; }
"""


def init_dark_mode() -> bool:
    """Ensure dark-mode session state exists; returns the current value."""
    st.session_state.setdefault("dark_mode", False)
    return bool(st.session_state["dark_mode"])


def dark_mode_toggle() -> bool:
    """Render the sidebar dark-mode toggle. Returns True when dark is active."""
    init_dark_mode()
    with st.sidebar:
        current = st.toggle("Dark mode", value=st.session_state["dark_mode"], key="dark_mode_toggle")
    if current != st.session_state["dark_mode"]:
        st.session_state["dark_mode"] = current
        st.rerun()
    return current


def plotly_theme(dark: bool) -> str:
    """Plotly template name matching the active app theme."""
    return "plotly_dark" if dark else "plotly_white"


def inject_global_css(dark: bool) -> None:
    """Inject shared + (conditional) dark CSS plus the Material Symbols font."""
    st.markdown(_MATERIAL_FONT, unsafe_allow_html=True)
    st.markdown(f"<style>{_CSS_BASE}{_CSS_DARK if dark else ''}</style>", unsafe_allow_html=True)
