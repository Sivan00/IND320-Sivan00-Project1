"""Precipitation and temperature outlier views for project part 3."""

from datetime import date

import matplotlib.pyplot as plt
import requests
import streamlit as st

from utils.quality_utils import (
    lof_temperature_plot,
    load_open_meteo_region,
    spc_precipitation_plot,
)


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
    "The API provides ERA5 reanalysis and does not need an access token for this use."
)

spc_tab, lof_tab = st.tabs(["SPC precipitation outliers", "LOF temperature anomalies"])
with spc_tab:
    st.write(
        "The DCT high-pass residual (SATV) is only used to decide which hours to "
        "flag. The chart stays on the original precipitation scale, with robust "
        "limits estimated from all residuals in the selected interval. "
        "Select a full year for the annual analysis required in the assignment. "
        "Marked hours stand out from the pattern; they are not necessarily errors."
    )
    # These controls stay visible because each one changes how many hours are flagged.
    first, second = st.columns(2)
    with first:
        cutoff = st.slider("DCT cutoff fraction", min_value=0.02, max_value=0.30, value=0.08, step=0.01)
    with second:
        n_sd = st.slider("Robust limit multiplier", min_value=1.0, max_value=5.0, value=3.0, step=0.5)
    # SATV is kept inside the function for detection; the user sees precipitation units.
    try:
        fig, summary = spc_precipitation_plot(weather, cutoff=float(cutoff), n_sd=float(n_sd))
        st.pyplot(fig)
        plt.close(fig)
        st.write(
            f"The DCT check flagged {summary['outliers']:,} of {summary['observations']:,} "
            f"hours ({summary['outlier_percent']:.2f}%)."
        )
    except ValueError as error:
        st.warning(str(error))

with lof_tab:
    st.write(
        "LOF compares each hourly temperature with nearby observations. I include "
        "the departure from a 24-hour rolling median as a second feature, which "
        "helps separate a sudden change from an ordinary seasonal temperature. "
        "The 1% default controls how many hours are flagged; it is not a probability of error."
    )
    # The anomaly proportion controls how much of the series LOF marks as unusual.
    contamination = st.slider(
        "Expected anomaly proportion", min_value=0.005, max_value=0.05,
        value=0.01, step=0.005, format="%.3f",
    )
    # LOF receives the visible contamination setting rather than a hidden fixed value.
    try:
        fig, summary = lof_temperature_plot(weather, contamination=float(contamination))
        st.pyplot(fig)
        plt.close(fig)
        st.write(
            f"LOF marked {summary['anomalies']:,} of {summary['observations']:,} "
            f"hours ({summary['anomaly_percent']:.2f}%)."
        )
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
