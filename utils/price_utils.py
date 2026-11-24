"""Daily electricity spot prices for the five Norwegian price areas."""
from datetime import date
import math
import pandas as pd
import requests
import streamlit as st


@st.cache_data(ttl=86400, show_spinner=False)
def daily_spot_price(area: str, day: str) -> float:
    """Return the duration-weighted daily spot price in NOK/kWh."""
    if area not in {'NO1', 'NO2', 'NO3', 'NO4', 'NO5'}:
        raise ValueError('Choose an electricity area from NO1 to NO5.')
    when = date.fromisoformat(day)
    if when < date(2022, 11, 1):
        raise ValueError('This price source starts in November 2022. Choose a later month.')
    url = f'https://www.hvakosterstrommen.no/api/v1/prices/{when:%Y/%m-%d}_{area}.json'
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or not payload:
        raise ValueError(f'No prices were returned for {area} on {day}.')
    try:
        table = pd.DataFrame(payload)
        starts = pd.to_datetime(table['time_start'], utc=True)
        ends = pd.to_datetime(table['time_end'], utc=True)
        prices = pd.to_numeric(table['NOK_per_kWh'], errors='raise')
        ordered = pd.DataFrame({'start': starts, 'end': ends, 'price': prices}).sort_values('start').reset_index(drop=True)
        expected_start = pd.Timestamp(day, tz='Europe/Oslo').tz_convert('UTC')
        expected_end = (pd.Timestamp(day, tz='Europe/Oslo') + pd.DateOffset(days=1)).tz_convert('UTC')
        durations = (ordered['end'] - ordered['start']).dt.total_seconds()
        if (ordered['start'].iloc[0] != expected_start or ordered['end'].iloc[-1] != expected_end
                or not ordered['start'].iloc[1:].reset_index(drop=True).equals(ordered['end'].iloc[:-1].reset_index(drop=True))
                or (durations <= 0).any() or ordered['price'].isna().any()
                or not all(math.isfinite(x) for x in ordered['price'])):
            raise ValueError('The returned prices do not cover the full day.')
        return float((ordered['price'] * durations).sum() / durations.sum())
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('The price data had an unexpected format.') from error
