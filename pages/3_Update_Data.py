"""
3_Update_Data.py
Daily update mechanism: fetch new rows only, append to parquet, show progress + logs.
Also lets the user add a custom stock ticker to any sector.
"""

import streamlit as st

from modules.utils import DEFAULT_STOCKS, SECTOR_TICKERS, get_last_update
from modules.fetch_data import add_custom_stock, update_all, validate_tickers

from components.theme import dark_mode_toggle, inject_global_css
from components.header import render_header
from components.banners import render_fetch_failure_banner

st.set_page_config(page_title="Update Data", layout="wide", page_icon="🔄")

dark = dark_mode_toggle()
inject_global_css(dark)
render_header(
    "Update Data",
    "India Markets — pull the latest daily bars from Yahoo Finance",
    last_update=get_last_update(),
)

# --- Ticker health check -----------------------------------------------------
with st.expander("Check sector index availability on Yahoo Finance"):
    if st.button("Run ticker check"):
        with st.spinner("Validating tickers..."):
            health = validate_tickers(SECTOR_TICKERS)
        if health["dead"]:
            st.error(f"No data available for: {', '.join(health['dead'])}")
        st.success(f"Live: {', '.join(health['ok'])}")

st.divider()

# --- Main update button -------------------------------------------------------
if st.button("Update Data", type="primary", width="stretch"):
    progress = st.progress(0.0)
    log_box = st.empty()
    logs = []

    total = len(SECTOR_TICKERS) + sum(len(v) for v in DEFAULT_STOCKS.values())
    done = 0

    def log_fn(msg):
        global done
        logs.append(msg)
        done += 1
        progress.progress(min(done / total, 1.0))
        log_box.code("\n".join(logs[-15:]))

    results = update_all(SECTOR_TICKERS, DEFAULT_STOCKS, log_fn=log_fn)

    updated = sum(1 for r in results if r["status"] == "updated")
    up_to_date = sum(1 for r in results if r["status"] == "up_to_date")
    failed = [r["name"] for r in results if r["status"] == "failed"]

    m1, m2, m3 = st.columns(3)
    m1.metric("Updated", updated)
    m2.metric("Already up to date", up_to_date)
    m3.metric("Failed", len(failed))

    render_fetch_failure_banner(failed)
    st.toast("Update run finished")
    st.cache_data.clear()  # invalidate heatmap/trend caches so new data shows immediately

st.divider()

# --- Add a custom stock -------------------------------------------------------
st.subheader("Add a custom stock")
c1, c2, c3 = st.columns([2, 2, 1])
with c1:
    new_ticker = st.text_input("Ticker (e.g. RELIANCE.NS)")
with c2:
    new_sector = st.selectbox("Assign to sector", list(SECTOR_TICKERS.keys()))
with c3:
    st.write("")
    if st.button("Add ticker") and new_ticker:
        with st.spinner(f"Fetching {new_ticker}..."):
            result = add_custom_stock(new_ticker.strip().upper(), new_sector)
        st.success(f"{new_ticker}: {result['status']} ({result['rows_added']} rows)")
        st.toast(f"{new_ticker} added")
        st.cache_data.clear()
