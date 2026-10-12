"""Home page for the reservoir and power transfer app."""

import streamlit as st

from data_utils import load_reservoirs, national_series


st.title("Norwegian energy data")
st.write(
    "This is the second part of my IND320 project. The reservoir pages now read "
    "weekly data directly from NVE, while the power transfer page uses the "
    "ENTSO-E data that I prepare through Cassandra, Spark and MongoDB."
)

# I still use NO/0 for the national overview because it gives one row per week.
data = load_reservoirs()
national = national_series(data)

st.subheader("Data available from NVE")
st.write(
    f"The API returned {len(data):,} rows and {len(data.columns)} columns. "
    f"The national series contains {len(national):,} weekly observations, from "
    f"{national['date'].min():%d %B %Y} to {national['date'].max():%d %B %Y}."
)

st.write(
    "The table and plot pages compare EL, NO and VASS without mixing their area "
    "numbers. The area guide explains the boundaries, and the final page shows "
    "cross-border power transfers stored in MongoDB."
)
