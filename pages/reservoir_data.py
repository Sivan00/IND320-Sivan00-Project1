"""Explore the NVE reservoir data and the different area systems."""

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from utils.data_utils import AREA_TYPES, area_label, load_reservoir_areas, load_reservoirs


st.title("Reservoir data")
st.write("Explore reservoir filling and the areas used in NVE's statistics.")

try:
    with st.spinner("Loading reservoir data from NVE…"):
        data = load_reservoirs()
        areas = load_reservoir_areas()
except (requests.RequestException, ValueError, KeyError):
    st.error("The NVE data could not be loaded. Please try again shortly.")
    st.stop()

if data.empty or areas.empty:
    st.info("NVE returned no reservoir data or area information.")
    st.stop()

area_type = st.radio(
    "Area type", ["EL", "NO", "VASS"], horizontal=True,
    format_func=lambda code: f"{code}: {AREA_TYPES[code]}",
)
months = sorted(data["date"].dropna().dt.to_period("M").astype(str).unique())
if not months:
    st.info("NVE returned no dates for the reservoir data.")
    st.stop()
start_month, end_month = st.select_slider(
    "Time period", options=months,
    value=(months[max(0, len(months) - 12)], months[-1]),
    help="NVE provides its full history; this selects the months shown below.",
)
selected = load_reservoirs(start_month, end_month)
area_data = selected.loc[selected["area_type"] == area_type].copy()
catalogue = areas.loc[areas["area_type"] == area_type].sort_values("area_number").copy()
table_tab, plot_tab, guide_tab = st.tabs(["Table", "Plot", "Area guide"])

with table_tab:
    st.caption(f"Weekly reservoir fill from {start_month} to {end_month}.")
    summary = []
    for area in catalogue.itertuples(index=False):
        rows = area_data.loc[area_data["area_number"] == area.area_number].sort_values("date")
        summary.append({
            "Code": f"{area_type} {area.area_number}", "Area": area.Area,
            "Coverage": area.Coverage, "Weeks": len(rows),
            "Reservoir fill (%)": (rows["fill_fraction"] * 100).round(1).tolist(),
        })
    st.dataframe(
        pd.DataFrame(summary), hide_index=True, width="stretch",
        column_config={"Reservoir fill (%)": st.column_config.LineChartColumn(
            "Reservoir fill (%)", help="Weekly fill level", y_min=0, y_max=100,
        )},
    )
    missing = [row["Code"] for row in summary if not row["Reservoir fill (%)"]]
    if missing:
        st.info(f"No measurements were returned for {', '.join(missing)} in this period.")
    with st.expander("Rows used in the table"):
        shown = area_data.copy()
        shown["area"] = shown.apply(
            lambda row: area_label(row["area_type"], int(row["area_number"])), axis=1
        )
        st.dataframe(shown, hide_index=True, width="stretch")

with plot_tab:
    if area_data.empty:
        st.info("NVE returned no measurements for this choice.")
    else:
        area_data["Area"] = area_data["area_number"].map(
            lambda number: area_label(area_type, int(number))
        )
        area_data["Fill level (%)"] = area_data["fill_fraction"] * 100
        fig = px.line(
            area_data.sort_values("date"), x="date", y="Fill level (%)", color="Area",
            title=f"Reservoir fill: {AREA_TYPES[area_type]}",
            color_discrete_sequence=["#2F6F73", "#A45A52", "#947340", "#5D6699", "#77915F"],
        )
        fig.update_layout(xaxis_title="Date", yaxis_range=[0, 105], hovermode="x unified")
        st.plotly_chart(fig, width="stretch")
        st.caption(f"{len(area_data):,} weekly observations in the selected period.")

with guide_tab:
    st.write(
        "EL uses electricity areas, NO is the national total, and VASS uses "
        "watercourse areas. An area number can therefore refer to different places."
    )
    available = set(data.loc[data["area_type"] == area_type, "area_number"])
    catalogue["Code"] = catalogue.apply(
        lambda row: f"{row['area_type']} {row['area_number']}", axis=1
    )
    catalogue["Measurements available"] = catalogue["area_number"].map(
        lambda number: "Yes" if number in available else "No"
    )
    st.dataframe(catalogue[["Code", "Area", "Coverage", "Measurements available"]],
                 hide_index=True, width="stretch")
    st.caption("Availability refers to NVE's full history, not only the selected period.")
    st.link_button("About the reservoir statistics", "https://www.nve.no/energi/analyser-og-statistikk/om-magasinstatistikken/")
