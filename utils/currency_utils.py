"""Get daily EUR and USD exchange rates from Norges Bank."""

from io import StringIO

import pandas as pd
import requests
import streamlit as st

BANK_URL = "https://data.norges-bank.no/api/data/EXR/B.EUR+USD.NOK.SP"


@st.cache_data(ttl=86400, show_spinner=False)
def load_exchange_rates(start_date: str, end_date: str) -> pd.DataFrame:
    """Return available business-day rates in NOK per EUR or USD."""
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    if start > end:
        raise ValueError("The start date must be before the end date.")
    response = requests.get(
        BANK_URL,
        params={"format": "csv", "startPeriod": start.date().isoformat(),
                "endPeriod": end.date().isoformat(), "locale": "en"},
        timeout=30,
    )
    response.raise_for_status()
    raw = pd.read_csv(StringIO(response.text), sep=";")
    if not {"BASE_CUR", "TIME_PERIOD", "OBS_VALUE"}.issubset(raw.columns):
        raise ValueError("Norges Bank returned an unexpected table.")
    rates = raw.rename(columns={"BASE_CUR": "currency", "TIME_PERIOD": "date", "OBS_VALUE": "nok_per_unit"})
    rates = rates.loc[rates["currency"].isin(["EUR", "USD"]), ["date", "currency", "nok_per_unit"]].copy()
    rates["date"] = pd.to_datetime(rates["date"], errors="coerce")
    rates["nok_per_unit"] = pd.to_numeric(rates["nok_per_unit"], errors="coerce")
    rates = rates.dropna().sort_values(["date", "currency"]).reset_index(drop=True)
    if rates.empty or rates.duplicated(["date", "currency"]).any():
        raise ValueError("No usable exchange rates were returned for the selected dates.")
    return rates
