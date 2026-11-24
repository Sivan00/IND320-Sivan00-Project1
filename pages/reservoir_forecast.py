"""Explore a simple River forecast for one electricity area."""

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from utils.currency_utils import load_exchange_rates
from utils.data_utils import load_reservoirs
from utils.forecast_utils import monthly_exchange_rates, monthly_reservoir, forecast_reservoir
from utils.forecast_weather import monthly_weather_input


st.title("Reservoir forecast")
st.write(
    "This example uses earlier monthly reservoir levels to estimate the next few months. "
    "It is a simple model, so the forecast should be read as an illustration."
)
area = st.session_state["electricity_area"]
try:
    with st.spinner("Loading reservoir data…"):
        monthly = monthly_reservoir(load_reservoirs(), area).dropna()
except (requests.RequestException, ValueError) as error:
    st.error(f"Could not load reservoir data: {error}")
    st.stop()
if len(monthly) < 48:
    st.warning("At least four years of monthly observations are needed for this example.")
    st.stop()
months = monthly.index.strftime("%Y-%m").tolist()
if st.session_state.get("selected_month") not in months:
    st.session_state.selected_month = months[-1]
if st.session_state.get("forecast_month") != st.session_state.selected_month:
    st.session_state.forecast_month = st.session_state.selected_month

def save_month():
    st.session_state.selected_month = st.session_state.forecast_month

end_month = st.selectbox("Last month in the history", months, key="forecast_month", on_change=save_month)
selected = monthly.loc[:pd.Timestamp(end_month + "-01")]
if len(selected) < 48:
    st.info("Choose a later month to include at least four years of history.")
    st.stop()
max_history = min(240, len(selected))
st.session_state.selected_history = max(36, min(max_history, st.session_state.get("selected_history", 120)))
if st.session_state.get("forecast_history") != st.session_state.selected_history:
    st.session_state.forecast_history = st.session_state.selected_history
if "selected_horizon" not in st.session_state:
    st.session_state.selected_horizon = 3
if st.session_state.get("forecast_horizon") != st.session_state.selected_horizon:
    st.session_state.forecast_horizon = st.session_state.selected_horizon

def save_history():
    st.session_state.selected_history = st.session_state.forecast_history

def save_horizon():
    st.session_state.selected_horizon = st.session_state.forecast_horizon

left, right = st.columns(2)
with left:
    history = st.slider("Months of history", 36, max_history, key="forecast_history", on_change=save_history)
    lags = st.selectbox("Previous months used", [3, 6, 12], index=2)
with right:
    horizon = st.slider("Months to forecast", 1, 12, key="forecast_horizon", on_change=save_horizon)
    neighbors = st.selectbox("Similar earlier months", [3, 5, 8], index=0)
st.caption(f"Training history: {selected.tail(history).index[0]:%Y-%m} to {end_month}. The map uses the same time settings.")
currencies = st.multiselect("Add exchange rates", ["EUR", "USD"], default=[])
weather_properties = st.multiselect("Add weather inputs", ["temperature", "precipitation"],
                                    format_func=str.capitalize, default=[])
if weather_properties:
    st.caption("Weather uses UTC-month averages from one fixed sample point, not the whole area. Large date ranges may take time.")
rates = None
weather = None
if currencies:
    try:
        with st.spinner("Loading exchange rates from Norges Bank…"):
            start = selected.tail(history).index[0].date().isoformat()
            end = (selected.index[-1] + pd.offsets.MonthEnd()).date().isoformat()
            rates = monthly_exchange_rates(load_exchange_rates(start, end))
    except (requests.RequestException, ValueError) as error:
        st.error(f"Could not load exchange rates: {error}")
        st.stop()
if weather_properties:
    try:
        with st.spinner("Loading daily weather from Open-Meteo…"):
            start = selected.tail(history).index[0].date().isoformat()
            end = (selected.index[-1] + pd.offsets.MonthEnd()).date().isoformat()
            weather = monthly_weather_input(area, start, end)
    except (requests.RequestException, ValueError) as error:
        st.error(f"Could not load weather inputs: {error}")
        st.stop()
try:
    with st.spinner("Calculating forecast…"):
        forecast, validation, summary = forecast_reservoir(
            selected, horizon=horizon, history_months=history, lags=lags,
            n_neighbors=neighbors, rates=rates, currencies=tuple(currencies),
            weather=weather, weather_properties=tuple(weather_properties),
        )
except ValueError as error:
    st.warning(str(error))
    st.stop()
fig = go.Figure()
recent = selected.tail(min(history, 36))
fig.add_scatter(x=recent.index, y=recent, name="Observed", line={"color": "#2F6F73"})
fig.add_scatter(x=[recent.index[-1], *forecast.date], y=[recent.iloc[-1], *forecast.predicted],
                name="Forecast", mode="lines+markers", line={"color": "#A45A52", "dash": "dash"})
# The animation reveals one forecast month at a time.
fig.frames = [
    go.Frame(name=str(i), traces=[1], data=[go.Scatter(
        x=[recent.index[-1], *forecast.date.iloc[:i]],
        y=[recent.iloc[-1], *forecast.predicted.iloc[:i]],
    )]) for i in range(1, len(forecast) + 1)
]
steps = [{"label": str(i), "method": "animate",
          "args": [[str(i)], {"mode": "immediate", "frame": {"duration": 0}, "transition": {"duration": 0}}]}
         for i in range(1, len(forecast) + 1)]
fig.update_layout(title=f"{area}: monthly reservoir fill", xaxis_title="Month", yaxis_title="Fill level (%)",
                  hovermode="x unified", yaxis_range=[0, 100],
                  updatemenus=[{"type": "buttons", "buttons": [{"label": "Play forecast", "method": "animate",
                      "args": [None, {"fromcurrent": False, "frame": {"duration": 600, "redraw": False},
                                      "transition": {"duration": 200}}]}]}],
                  sliders=[{"active": len(steps) - 1, "currentvalue": {"prefix": "Forecast month: "}, "steps": steps}])
st.plotly_chart(fig, width="stretch")
st.caption(f"One-month-ahead test: average error {summary['mae']:.1f} percentage points over {summary['validation_months']} months.")
if currencies or weather_properties:
    st.info("For future months, selected exchange rates and weather inputs are held at their last known monthly values. This is an assumption, not a forecast of those inputs.")
with st.expander("Show forecast and test results"):
    st.dataframe(forecast, hide_index=True, width="stretch")
    st.dataframe(validation, hide_index=True, width="stretch")
