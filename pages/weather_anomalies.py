"""Precipitation and temperature outlier views for project part 3."""

from datetime import date

import requests
import streamlit as st

from utils.quality_utils import (
    load_open_meteo_region,
)

from utils.interactive_weather import weather_check

st.title("Weather outliers")
st.write(
    "I use hourly ERA5 estimates from Open-Meteo for a reproducible sample of "
        "locations inside the selected NVE electricity-area polygon. "
        "The app averages those points before looking for unusual values."
)

area_code = st.session_state["electricity_area"]
# I use the bidding-zone polygons here because the weather sample should match the chosen area.
st.caption(f"Weather sample locations are drawn from the NVE polygon for {area_code}.")
with st.expander("Electricity areas and NVE regions"):
    st.write(
        "This page uses the selected electricity area (NO1–NO5). The separate NVE "
        "weather-region samples use East = RS + RØ, West = RV and North = RM + RN, "
        "with 1,000 points sampled inside each combined region. These region boundaries "
        "do not match the electricity-area boundaries exactly."
    )
left, right = st.columns(2)
with left:
    start_date = st.date_input("Start date", value=date(2024, 1, 1), key="weather_start")
with right:
    end_date = st.date_input("End date", value=date(2024, 12, 31), key="weather_end")
if start_date > end_date:
    st.warning("The start date must be before the end date.")
    st.stop()

# Keep a small default for responsive browsing; the full fixed sample is also selectable.
point_count = st.selectbox(
    "Sample locations used in the app", options=[5, 25, 100, 1000], index=0,
    help="The reproducible sample has 1,000 points per electricity area. Larger requests take longer and can reach the free API limit.",
)

request_key = (area_code, start_date.isoformat(), end_date.isoformat(), int(point_count))
if point_count >= 100:
    st.info(
        "Large weather downloads can take a long time and reach Open-Meteo's free API limit, "
        "especially for a full year. Completed batches are cached when storage is available; "
        "cloud redeployments can clear that cache. "
        "If the limit is reached, try again later or choose fewer locations."
    )
    if st.session_state.get("confirmed_weather_request") != request_key:
        if st.button(f"Download weather for {point_count:,} locations"):
            st.session_state["confirmed_weather_request"] = request_key
        else:
            st.stop()

with st.spinner(f"Getting hourly weather for {point_count:,} locations in {area_code}…"):
    try:
        weather = load_open_meteo_region(
            area_code, start_date.isoformat(), end_date.isoformat(), int(point_count)
        )
    except (requests.RequestException, ValueError) as error:
        st.error(f"The weather series could not be loaded: {error}")
        st.stop()

st.caption(
    f"The {point_count:,} selected locations in {area_code} give {len(weather):,} hourly observations from "
    f"{weather['time'].min():%d %b %Y} to {weather['time'].max():%d %b %Y}. "
    "Times are UTC. The API provides ERA5 reanalysis and does not need an access token for this use."
)

property_name = st.selectbox("Weather property", ["Temperature", "Precipitation"])
spc_tab, lof_tab = st.tabs(["SATV and SPC", "LOF"])
with spc_tab:
    st.write("DCT separates a background from the short-term variation (SATV). SATV is used to calculate the limits and flag unusual hours; the SATV values themselves are not plotted. A flag does not necessarily mean an error.")
    first, second = st.columns(2)
    with first:
        cutoff = st.slider("DCT cutoff fraction", 0.02, 0.30, 0.08, 0.01)
    with second:
        n_sd = st.slider("Robust limit multiplier", 1.0, 5.0, 3.0, 0.5)
    try:
        fig, count, total = weather_check(weather, property_name, "SPC", cutoff=cutoff, n_sd=n_sd)
        st.plotly_chart(fig, width="stretch")
        st.write(f"The DCT check flagged {count:,} of {total:,} hours ({count / total * 100:.2f}%).")
    except ValueError as error:
        st.warning(str(error))
with lof_tab:
    st.write("LOF compares each value and its change from a 24-hour median with nearby observations. The default 1% is a setting, not the probability of an error.")
    if property_name == "Precipitation":
        st.caption("Many precipitation values are zero, so repeated values can make LOF less reliable. Interpret these flags carefully.")
    contamination = st.slider("Expected anomaly proportion", 0.005, 0.05, 0.01, 0.005, format="%.3f")
    try:
        fig, count, total = weather_check(weather, property_name, "LOF", contamination=contamination)
        st.plotly_chart(fig, width="stretch")
        st.write(f"LOF marked {count:,} of {total:,} hours ({count / total * 100:.2f}%).")
    except ValueError as error:
        st.warning(str(error))

with st.expander("Weather data source"):
    st.write(
        "Open-Meteo's Historical Weather API supplies ERA5 hourly precipitation "
        "and 2 m temperature. For this part I average the chosen location sample "
        "by hour before running the outlier methods. Each electricity-area "
        "sample is drawn from its matching NVE bidding-zone polygon with a fixed seed."
    )
    st.markdown(
        "[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) · "
        "[NVE map services](https://www.nve.no/map-services/)"
    )
