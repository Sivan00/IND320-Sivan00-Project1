"""Entry point for my IND320 Streamlit app."""

import streamlit as st


# Keeping the navigation in one file gives every page the same sidebar menu.
st.set_page_config(page_title="Norwegian energy data | IND320", layout="wide")

# I keep each screen in its own file so the page code stays separate from navigation.
home = st.Page("pages/home.py", title="Home", default=True)
table = st.Page("pages/data_table.py", title="Reservoir table")
plots = st.Page("pages/plots.py", title="Reservoir plots")
reservoir_api = st.Page("pages/reservoir_api.py", title="NVE area guide")
power_transfers = st.Page("pages/power_transfers.py", title="Power transfers")
reservoir_patterns = st.Page("pages/reservoir_patterns.py", title="Reservoir patterns")
weather_anomalies = st.Page("pages/weather_anomalies.py", title="Weather outliers")

# One navigation list keeps the same sidebar available on every page.
page = st.navigation(
    [home, table, plots, reservoir_patterns, weather_anomalies, reservoir_api, power_transfers],
    position="sidebar",
)
st.sidebar.caption("IND320 project 3 | Sivan")
# A widget in the entry point keeps the same selection when pages change.
# Both the NVE pattern analysis and ERA5 download use this electricity area.
st.sidebar.selectbox(
    "Electricity area", ["NO1", "NO2", "NO3", "NO4", "NO5"],
    index=2, key="electricity_area",
    help="Shared by Reservoir patterns and Weather outliers.",
)
page.run()
