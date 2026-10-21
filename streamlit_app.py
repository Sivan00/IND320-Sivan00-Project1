"""Entry point for the second part of my IND320 Streamlit app."""

import streamlit as st


# Keeping the navigation in one file gives every page the same sidebar menu.
st.set_page_config(page_title="Norwegian energy data | IND320", layout="wide")

home = st.Page("pages/home.py", title="Home", default=True)
table = st.Page("pages/data_table.py", title="Reservoir table")
plots = st.Page("pages/plots.py", title="Reservoir plots")
reservoir_api = st.Page("pages/reservoir_api.py", title="NVE area guide")
power_transfers = st.Page("pages/power_transfers.py", title="Power transfers")

page = st.navigation(
    [home, table, plots, reservoir_api, power_transfers],
    position="sidebar",
)
st.sidebar.caption("IND320 project 2 | Sivan")
page.run()
