"""Home page for the IND320 energy and weather app."""
import requests
import streamlit as st
from utils.data_utils import load_reservoirs, national_series

st.title("Norwegian energy data")
st.write(
    "This app brings together reservoir filling, electricity transfers, weather, "
    "exchange rates and a simple forecast. Choose an area in the sidebar or on the map."
)
st.write(
    "Use **Explore** for the map and data, **Analysis** for patterns and weather, "
    "and **Forecast** for the reservoir model."
)
try:
    with st.spinner("Loading reservoir overview…"):
        data = load_reservoirs()
        national = national_series(data)
except (requests.RequestException, ValueError, KeyError):
    st.warning("The NVE overview is unavailable right now. Please try again later.")
    st.stop()
if national.empty:
    st.info("The national reservoir series is not available right now.")
    st.stop()
st.subheader("Data available from NVE")
st.write(
    f"The national series has {len(national):,} weekly observations, from "
    f"{national['date'].min():%d %B %Y} to {national['date'].max():%d %B %Y}."
)
st.caption("Weather and forecasts use samples and assumptions, so results should be interpreted with care.")
