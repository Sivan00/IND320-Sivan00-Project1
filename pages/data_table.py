"""Show one reservoir sparkline for each area in the selected area system."""

import pandas as pd
import requests
import streamlit as st

from data_utils import (
    AREA_TYPES, area_label, load_reservoir_areas, load_reservoirs,
)


st.title("Reservoir table")
st.write(
    "The table compares the areas returned by NVE. I can change the area system "
    "and the data interval without mixing electricity zones and watercourse regions."
)

try:
    complete_data = load_reservoirs()
    area_catalogue = load_reservoir_areas()
except requests.RequestException:
    st.error("The NVE data could not be loaded. Please try again shortly.")
    st.stop()

area_type = st.radio(
    "Area type",
    ["EL", "NO", "VASS"],
    horizontal=True,
    format_func=lambda code: f"{code}: {AREA_TYPES[code]}",
)

# The endpoint returns the full history, while this slider decides which part
# of that download is kept for the table. Twelve months is a useful first view.
months = complete_data["date"].dt.to_period("M").astype(str).unique().tolist()
default_start = months[max(0, len(months) - 12)]
start_month, end_month = st.select_slider(
    "Download interval",
    options=months,
    value=(default_start, months[-1]),
    help="The month range retained from NVE's downloaded response.",
)
selected = load_reservoirs(start_month, end_month)
area_rows = selected.loc[selected["area_type"] == area_type].copy()

summary = []
catalogue_rows = area_catalogue.loc[
    area_catalogue["area_type"] == area_type
].sort_values("area_number")
for area in catalogue_rows.itertuples(index=False):
    rows = area_rows.loc[
        area_rows["area_number"] == area.area_number
    ].sort_values("date")

    # LineChartColumn needs a list for each row. An empty list shows that NVE
    # has defined the area but did not return measurements for this interval.
    fill_line = (rows["fill_fraction"] * 100).round(1).tolist()
    summary.append(
        {
            "Code": f"{area_type} {area.area_number}",
            "Area": area.Area,
            "Coverage": area.Coverage,
            "Weeks": len(rows),
            "Reservoir fill (%)": fill_line,
        }
    )

st.caption(
    f"Rows retained from {start_month} to {end_month}. Each small line shows the "
    f"weekly fill level for one {area_type} area."
)
st.dataframe(
    pd.DataFrame(summary),
    column_config={
        "Reservoir fill (%)": st.column_config.LineChartColumn(
            "Reservoir fill (%)",
            help="Weekly fill level in the selected download interval",
            y_min=0,
            y_max=100,
        )
    },
    hide_index=True,
    width="stretch",
)

missing = [row["Code"] for row in summary if not row["Reservoir fill (%)"]]
if missing:
    st.info(
        f"NVE defines {', '.join(missing)}, but no measurements were returned "
        "for the selected interval. I leave its mini chart empty instead of using zero."
    )

with st.expander("Rows used in the table"):
    # Keeping the original weekly rows nearby makes the sparklines reproducible.
    shown = area_rows.copy()
    shown["area"] = shown.apply(
        lambda row: area_label(row["area_type"], int(row["area_number"])), axis=1
    )
    st.dataframe(shown, hide_index=True, width="stretch")
