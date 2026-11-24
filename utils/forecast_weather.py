"""Monthly weather inputs for the reservoir forecast."""
import pandas as pd
import requests
import streamlit as st
from utils.quality_utils import load_electricity_sample


@st.cache_data(ttl=86400, show_spinner=False)
def monthly_weather_input(area: str, start: str, end: str) -> pd.DataFrame:
    """Download daily UTC ERA5 for one fixed sample point and average by month."""
    points = load_electricity_sample()
    chosen = points.loc[points['area_group'] == area]
    if chosen.empty:
        raise ValueError('No weather sample point is available for this area.')
    point = chosen.iloc[0]
    response = requests.get('https://archive-api.open-meteo.com/v1/archive', params={
        'latitude': float(point.latitude), 'longitude': float(point.longitude),
        'start_date': start, 'end_date': end,
        'daily': 'temperature_2m_mean,precipitation_sum',
        'timezone': 'GMT', 'models': 'era5',
    }, timeout=(10, 90))
    response.raise_for_status()
    daily = response.json().get('daily', {})
    try:
        data = pd.DataFrame({'date': pd.to_datetime(daily['time']),
                             'temperature': daily['temperature_2m_mean'],
                             'precipitation': daily['precipitation_sum']}).set_index('date')
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('Weather data were incomplete or had an unexpected format.') from error
    expected = pd.date_range(start, end, freq='D')
    if not data.index.equals(expected) or data.isna().any().any():
        raise ValueError('Weather is missing for one or more days; no partial monthly average was used.')
    return data.astype(float).resample('MS').mean()
