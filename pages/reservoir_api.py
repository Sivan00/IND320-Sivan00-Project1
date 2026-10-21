"""Explain the geographic area codes used in the reservoir pages."""

import requests
import streamlit as st

from data_utils import AREA_TYPES, load_reservoir_areas, load_reservoirs


st.title("NVE area guide")
st.write(
    "EL, NO and VASS do not describe the same borders. I keep this guide on a "
    "separate page so the table and plot pages can stay focused on the data."
)

try:
    # I use both responses so the page can compare NVE's area list with the data.
    areas = load_reservoir_areas()
    measurements = load_reservoirs()
except requests.RequestException:
    st.error("The NVE area information could not be loaded. Please try again shortly.")
    st.stop()

area_type = st.radio(
    "Area type",
    ["EL", "NO", "VASS"],
    horizontal=True,
    format_func=lambda code: f"{code}: {AREA_TYPES[code]}",
)
area_table = areas.loc[areas["area_type"] == area_type].copy()
# This check shows whether every area defined by NVE also has measurements.
available = set(
    measurements.loc[measurements["area_type"] == area_type, "area_number"]
)
area_table["Code"] = area_table.apply(
    lambda row: f"{row['area_type']} {row['area_number']}", axis=1
)
area_table["Measurements available"] = area_table["area_number"].map(
    lambda number: "Yes" if number in available else "No"
)
st.dataframe(
    area_table[["Code", "Area", "Coverage", "Measurements available"]],
    hide_index=True,
    width="stretch",
)

st.write(
    "EL contains the electricity bidding zones NO1 to NO5. NO with area number "
    "0 is the national total. VASS uses watercourse regions, so VASS 1 and EL 1 "
    "should not be compared as if they cover the same places."
)
missing = area_table.loc[
    area_table["Measurements available"] == "No", "Code"
].tolist()
if missing:
    # I report the missing series instead of making it look like the value is zero.
    st.info(
        f"NVE lists {', '.join(missing)} in the area catalogue but does not return "
        "a measurement series for it."
    )
