"""Entry point for my IND320 Streamlit app."""

import streamlit as st


# Keeping the navigation in one file gives every page the same sidebar menu.
st.set_page_config(page_title="Norwegian energy data | IND320", layout="wide")

# I keep each screen in its own file so the page code stays separate from navigation.
home = st.Page("pages/home.py", title="Home", default=True)
area_map = st.Page("pages/area_map.py", title="Area map")
reservoir_data = st.Page("pages/reservoir_data.py", title="Reservoir data")
power_transfers = st.Page("pages/power_transfers.py", title="Power transfers")
reservoir_patterns = st.Page("pages/reservoir_patterns.py", title="Reservoir patterns")
weather_anomalies = st.Page("pages/weather_anomalies.py", title="Weather outliers")
weather_relationship = st.Page("pages/weather_relationship.py", title="Weather and reservoirs")
exchange_rates = st.Page("pages/exchange_rates.py", title="Exchange rates")
reservoir_forecast = st.Page("pages/reservoir_forecast.py", title="Reservoir forecast")

# One navigation list keeps the same sidebar available on every page.
page = st.navigation(
    {"Explore": [home, area_map, reservoir_data, power_transfers, exchange_rates],
     "Analysis": [reservoir_patterns, weather_anomalies, weather_relationship],
     "Forecast": [reservoir_forecast]},
    position="sidebar",
)
st.sidebar.caption("IND320 project 4 | Sivan")
# A widget in the entry point keeps the same selection when pages change.
# Both the NVE pattern analysis and ERA5 download use this electricity area.
st.sidebar.selectbox(
    "Electricity area", ["NO1", "NO2", "NO3", "NO4", "NO5"],
    index=2, key="electricity_area",
    help="Shared by the weather and reservoir analysis pages.",
)
page.run()
