"""Explore a simple River forecast for one electricity area."""

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from utils.currency_utils import load_exchange_rates
from utils.data_utils import load_reservoirs
from utils.forecast_utils import monthly_exchange_rates, monthly_reservoir, forecast_reservoir


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
end_month = st.selectbox("Last month in the history", months, index=len(months) - 1)
selected = monthly.loc[:pd.Timestamp(end_month + "-01")]
if len(selected) < 48:
    st.info("Choose a later month to include at least four years of history.")
    st.stop()
left, right = st.columns(2)
with left:
    history = st.slider("Months of history", 36, min(240, len(selected)), min(120, len(selected)), 12)
    lags = st.selectbox("Previous months used", [3, 6, 12], index=2)
with right:
    horizon = st.slider("Months to forecast", 1, 12, 3)
    neighbors = st.selectbox("Similar earlier months", [3, 5, 8], index=0)
currencies = st.multiselect("Add exchange rates", ["EUR", "USD"], default=[])
rates = None
if currencies:
    try:
        with st.spinner("Loading exchange rates from Norges Bank…"):
            start = selected.tail(history).index[0].date().isoformat()
            end = (selected.index[-1] + pd.offsets.MonthEnd()).date().isoformat()
            rates = monthly_exchange_rates(load_exchange_rates(start, end))
    except (requests.RequestException, ValueError) as error:
        st.error(f"Could not load exchange rates: {error}")
        st.stop()
try:
    with st.spinner("Calculating forecast…"):
        forecast, validation, summary = forecast_reservoir(
            selected, horizon=horizon, history_months=history, lags=lags,
            n_neighbors=neighbors, rates=rates, currencies=tuple(currencies),
        )
except ValueError as error:
    st.warning(str(error))
    st.stop()
fig = go.Figure()
recent = selected.tail(min(history, 36))
fig.add_scatter(x=recent.index, y=recent, name="Observed", line={"color": "#2F6F73"})
fig.add_scatter(x=[recent.index[-1], *forecast.date], y=[recent.iloc[-1], *forecast.predicted],
                name="Forecast", mode="lines+markers", line={"color": "#A45A52", "dash": "dash"})
fig.update_layout(title=f"{area}: monthly reservoir fill", xaxis_title="Month", yaxis_title="Fill level (%)",
                  hovermode="x unified", yaxis_range=[0, 100])
st.plotly_chart(fig, width="stretch")
st.caption(f"One-month-ahead test: average error {summary['mae']:.1f} percentage points over {summary['validation_months']} months.")
if currencies:
    st.info("For future months, the selected exchange rates are held at their last known values. This is an assumption.")
with st.expander("Show forecast and test results"):
    st.dataframe(forecast, hide_index=True, width="stretch")
    st.dataframe(validation, hide_index=True, width="stretch")
