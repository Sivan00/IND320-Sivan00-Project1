"""Home page for the reservoir, weather and power transfer app."""

import streamlit as st

from utils.data_utils import load_reservoirs, national_series


st.title("Norwegian energy data")
st.write(
    "This is the third part of my IND320 project. The app still uses NVE reservoir "
    "data and the ENTSO-E transfer data prepared through Cassandra, Spark and MongoDB. "
    "I have added weather-based outlier checks and two views of reservoir patterns."
)

# I still use NO/0 for the national overview because it gives one row per week.
data = load_reservoirs()
national = national_series(data)

# This summary gives a quick sense of the national series before I move to area-level pages.
st.subheader("Data available from NVE")
st.write(
    f"The API returned {len(data):,} rows and {len(data.columns)} columns. "
    f"The national series contains {len(national):,} weekly observations, from "
    f"{national['date'].min():%d %B %Y} to {national['date'].max():%d %B %Y}."
)

st.write(
    "The table and plot pages compare EL, NO and VASS without mixing their area "
    "numbers. The area guide explains the boundaries, and the final page shows "
    "cross-border power transfers stored in MongoDB. The new analysis pages use "
    "ERA5 weather from Open-Meteo and weekly fill levels from NVE."
)
