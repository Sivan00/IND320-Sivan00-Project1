"""Load the source CSV and make its column names easier to work with."""

from pathlib import Path

import pandas as pd
import streamlit as st


DATA_FILE = Path(__file__).resolve().parent / "data" / "reservoirs.csv"

COLUMN_NAMES = {
    "dato_Id": "date",
    "omrType": "area_type",
    "omrnr": "area_number",
    "iso_aar": "iso_year",
    "iso_uke": "iso_week",
    "fyllingsgrad": "fill_fraction",
    "kapasitet_TWh": "capacity_twh",
    "fylling_TWh": "stored_energy_twh",
    "neste_Publiseringsdato": "next_publication_date",
    "fyllingsgrad_forrige_uke": "previous_week_fill_fraction",
    "endring_fyllingsgrad": "weekly_change_fill_fraction",
}

MEASUREMENTS = {
    "fill_fraction": ("Reservoir fill", "Percent", 100),
    "capacity_twh": ("Capacity", "TWh", 1),
    "stored_energy_twh": ("Stored energy", "TWh", 1),
    "previous_week_fill_fraction": ("Previous week's fill", "Percent", 100),
    "weekly_change_fill_fraction": ("Weekly change in fill", "Percentage points", 100),
}


@st.cache_data
def load_reservoirs() -> pd.DataFrame:
    # The CSV stays unchanged. I rename columns in memory so the notebook and app
    # can use the same readable names without losing track of the original source.
    data = pd.read_csv(DATA_FILE).rename(columns=COLUMN_NAMES)
    data["date"] = pd.to_datetime(data["date"])

    # The file is not in date order, so I sort it before making any time plot.
    return data.sort_values(["date", "area_type", "area_number"]).reset_index(drop=True)


def national_series(data: pd.DataFrame) -> pd.DataFrame:
    # There are nine area rows per week. NO/0 is the national series, which gives
    # one observation per week instead of mixing different regions in one line.
    return data.loc[
        (data["area_type"] == "NO") & (data["area_number"] == 0)
    ].copy()
