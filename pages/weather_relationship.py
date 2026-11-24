"""Explore how weather and reservoir filling move together."""

from datetime import date

import plotly.express as px
import requests
import streamlit as st

from utils.correlation_utils import sliding_weather_correlation
from utils.data_utils import load_reservoirs
from utils.forecast_utils import monthly_reservoir
from utils.quality_utils import load_open_meteo_region


st.title("Weather and reservoir filling")
st.write("Explore how monthly weather and reservoir filling move together over time.")
area = st.session_state["electricity_area"]
left, right = st.columns(2)
with left:
    start = st.date_input("Start date", value=date(2024, 1, 1), key="correlation_start")
    property_name = st.selectbox("Weather property", ["precipitation", "temperature_2m"],
                                 format_func=lambda x: "Precipitation" if x == "precipitation" else "Temperature")
with right:
    end = st.date_input("End date", value=date(2024, 12, 31), key="correlation_end")
    lag = st.slider("Weather lead (months)", 0, 6, 0,
                    help="A positive value compares earlier weather with later filling.")
window = st.slider("Correlation window (months)", 3, 24, 6)
if start > end:
    st.warning("The start date must be before the end date.")
    st.stop()
try:
    with st.spinner(f"Loading weather and reservoir data for {area}…"):
        weather = load_open_meteo_region(area, start.isoformat(), end.isoformat(), point_count=5)
        # Compare full UTC months only, not a partial weather month with a full reservoir month.
        counts = weather.groupby(weather["time"].dt.to_period("M")).size()
        full_months = counts[counts == counts.index.days_in_month * 24].index
        weather = weather.loc[weather["time"].dt.to_period("M").isin(full_months)]
        if weather.empty:
            st.info("Choose dates covering at least one full calendar month.")
            st.stop()
        reservoir = monthly_reservoir(load_reservoirs(), area)
        result = sliding_weather_correlation(reservoir, weather, property_name, window, lag)
except (requests.RequestException, ValueError) as error:
    st.error(f"Could not calculate the correlation: {error}")
    st.stop()
if result.empty:
    st.info("Choose a longer interval or a shorter correlation window.")
    st.stop()
fig = px.line(result, x="date", y="correlation", markers=True,
              labels={"date": "Month", "correlation": "Correlation"}, color_discrete_sequence=["#2F6F73"])
fig.update_layout(title=f"{area}: moving correlation", yaxis_range=[-1, 1])
fig.add_hline(y=0, line_dash="dash", line_color="#777777")
st.plotly_chart(fig, width="stretch")
st.caption("The line shows a moving correlation, not proof that weather caused a change in filling. Weather values are complete UTC-month averages from five sampled points. Incomplete edge months are left out.")
with st.expander("Show values"):
    st.dataframe(result, hide_index=True, width="stretch")
