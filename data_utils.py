"""Download and prepare the weekly reservoir data from NVE."""

import pandas as pd
import requests
import streamlit as st


NVE_RESERVOIR_URL = (
    "https://biapi.nve.no/magasinstatistikk/api/"
    "Magasinstatistikk/HentOffentligData"
)
NVE_AREAS_URL = NVE_RESERVOIR_URL.rsplit('/', 1)[0] + '/HentOmråder'

AREA_TYPES = {
    "EL": "Electricity bidding zones",
    "NO": "Norway as a whole",
    "VASS": "Watercourse regions",
}

# These are my English summaries of NVE's HentOmråder descriptions.
# EL and VASS divide the country differently, even when a number is the same.
AREA_DETAILS = {
    ("NO", 0): ("Norway", "The whole country."),
    ("EL", 1): ("NO1: South-eastern Norway", "Eastern Østlandet from Buskerud northwards, excluding the part of Innlandet west and north of Vågåmo."),
    ("EL", 2): ("NO2: South-western Norway", "Most of Vestfold, Telemark, Agder and Rogaland, and southern Vestland."),
    ("EL", 3): ("NO3: Central Norway", "Northern and western Vestland, Innlandet west and north of Vågåmo, Møre og Romsdal, and Trøndelag as far as Tunnsjødal."),
    ("EL", 4): ("NO4: Northern Norway", "The rest of Trøndelag and Northern Norway."),
    ("EL", 5): ("NO5: Western Norway", "Central Vestland up to Sognefjorden, Indre Sogn, and western Buskerud."),
    ("VASS", 1): ("South-eastern Norway", "Østlandet, Agder and parts of Rogaland."),
    ("VASS", 2): ("Western Norway", "The rest of Rogaland and Vestland."),
    ("VASS", 3): ("Central Norway", "Møre og Romsdal, Trøndelag and southern Nordland."),
    ("VASS", 4): ("Northern Norway", "The rest of Nordland and the areas further north."),
}


def area_label(area_type: str, area_number: int) -> str:
    # I keep the original code beside the name so it can be checked against the API.
    name = AREA_DETAILS.get((area_type, area_number), ("Unmapped area", ""))[0]
    return f"{area_type} {area_number}: {name}"


@st.cache_data(ttl=86400)
def load_reservoir_areas() -> pd.DataFrame:
    # Area metadata changes less often than the measurements, so a daily cache is enough.
    response = requests.get(NVE_AREAS_URL, timeout=30)
    response.raise_for_status()
    rows = []
    for group in response.json():
        for areas in group.values():
            for area in areas:
                key = (area["omrType"], area["omrnr"])
                name, coverage = AREA_DETAILS.get(key, (area["navn"], "See NVE's description."))
                rows.append({
                    "area_type": key[0], "area_number": key[1],
                    "Area": name, "Coverage": coverage,
                    "NVE description": area["beskrivelse"],
                })
    return pd.DataFrame(rows).sort_values(["area_type", "area_number"])

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


@st.cache_data(ttl=3600)
def _download_reservoirs() -> pd.DataFrame:
    # NVE sends the complete public history from this endpoint. I cache that
    # response for one hour and select the requested dates after downloading it.
    response = requests.get(NVE_RESERVOIR_URL, timeout=30)
    response.raise_for_status()
    data = pd.DataFrame(response.json()).rename(columns=COLUMN_NAMES)

    # NVE does not return the rows in date order, so I fix that before plotting.
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values(
        ["date", "area_type", "area_number"]
    ).reset_index(drop=True)
    data.attrs["downloaded_at"] = pd.Timestamp.now(tz="UTC").isoformat()
    return data


def load_reservoirs(
    start_month: str | None = None, end_month: str | None = None
) -> pd.DataFrame:
    data = _download_reservoirs()
    if start_month is None and end_month is None:
        return data
    if start_month is None or end_month is None:
        raise ValueError("Both ends of the data interval must be selected.")

    # The API cannot filter dates on the server, so this is the interval kept
    # from the downloaded response and used by the table and plots.
    month_keys = data["date"].dt.to_period("M").astype(str)
    selected = data.loc[month_keys.between(start_month, end_month)].copy()
    selected.attrs.update(data.attrs)
    return selected


def national_series(data: pd.DataFrame) -> pd.DataFrame:
    # There are several area rows per week. NO/0 is the national total, which
    # keeps the old Project 1 plots comparable without mixing regions together.
    return data.loc[
        (data["area_type"] == "NO") & (data["area_number"] == 0)
    ].copy()
