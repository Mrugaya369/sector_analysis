"""
downloads.py
Styled CSV download with a format dropdown (popover) and a toast on export.
"""

import streamlit as st


def render_download_menu(formats: dict, label: str = "Download as CSV") -> None:
    """
    formats: {format_name: (csv_bytes, filename)}. Renders a popover button
    with a format selector and a primary download button; toasts on export.
    """
    with st.popover(label, width="stretch"):
        format_name = st.selectbox("Format", list(formats.keys()), label_visibility="collapsed")
        data, filename = formats[format_name]
        if st.download_button(
            "Download CSV",
            data=data,
            file_name=filename,
            mime="text/csv",
            type="primary",
            width="stretch",
        ):
            st.toast(f"CSV exported — {filename}")
