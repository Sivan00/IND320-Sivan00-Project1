"""Show exchange rates from Norges Bank."""

from datetime import date

import plotly.express as px
import requests
import streamlit as st

from utils.currency_utils import load_exchange_rates


st.title("Exchange rates")
st.write("Daily EUR and USD exchange rates from Norges Bank, shown in Norwegian kroner.")
left, right = st.columns(2)
with left:
    start = st.date_input("Start date", value=date(2024, 1, 1), key="currency_start")
with right:
    end = st.date_input("End date", value=date(2024, 12, 31), key="currency_end")
if start > end:
    st.warning("The start date must be before the end date.")
    st.stop()
try:
    with st.spinner("Loading exchange rates from Norges Bank…"):
        rates = load_exchange_rates(start.isoformat(), end.isoformat())
except (requests.RequestException, ValueError) as error:
    st.error(f"Could not load exchange rates: {error}")
    st.stop()
choice = st.multiselect("Currencies", ["EUR", "USD"], default=["EUR", "USD"])
selected = rates.loc[rates.currency.isin(choice)]
if selected.empty:
    st.info("Select at least one currency.")
    st.stop()
fig = px.line(selected, x="date", y="nok_per_unit", color="currency",
              labels={"date": "Date", "nok_per_unit": "NOK per unit", "currency": "Currency"},
              color_discrete_sequence=["#2F6F73", "#A45A52"])
fig.update_layout(title="Exchange rates", hovermode="x unified")
st.plotly_chart(fig, width="stretch")
st.caption("Rates are listed for business days. There are no new observations for weekends or public holidays.")
with st.expander("Show exchange rates"):
    st.dataframe(selected, hide_index=True, width="stretch")
st.link_button("Norges Bank data portal", "https://data.norges-bank.no/")
