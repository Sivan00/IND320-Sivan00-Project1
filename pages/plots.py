"""Compare reservoir fill for every area in one selected NVE area system."""

import plotly.express as px
import requests
import streamlit as st

from utils.data_utils import AREA_TYPES, area_label, load_reservoirs


st.title("Reservoir plots")
st.write(
    "The radio buttons choose one area system at a time. The interval slider "
    "then decides which part of the downloaded NVE data is used in the plot."
)

try:
    # I load the full response first because NVE does not accept dates in this request.
    complete_data = load_reservoirs()
except requests.RequestException:
    st.error("The NVE data could not be loaded. Please try again shortly.")
    st.stop()

area_type = st.radio(
    "Area type",
    ["EL", "NO", "VASS"],
    horizontal=True,
    format_func=lambda code: f"{code}: {AREA_TYPES[code]}",
)
months = complete_data["date"].dt.to_period("M").astype(str).unique().tolist()
# Two years gives a useful first view without making the opening plot too crowded.
default_start = months[max(0, len(months) - 24)]
start_month, end_month = st.select_slider(
    "Download interval",
    options=months,
    value=(default_start, months[-1]),
    help="The month range retained from NVE's downloaded response.",
)

selected = load_reservoirs(start_month, end_month)
# Filtering once here keeps every line on the same month interval.
area_data = selected.loc[selected["area_type"] == area_type].copy()
if area_data.empty:
    st.info("NVE returned no measurements for this choice.")
    st.stop()

area_data["Area"] = area_data["area_number"].map(lambda number: area_label(area_type, int(number)))
area_data["Fill level (%)"] = area_data["fill_fraction"] * 100
fig = px.line(area_data.sort_values("date"), x="date", y="Fill level (%)", color="Area",
              title=f"Reservoir fill: {AREA_TYPES[area_type]}",
              color_discrete_sequence=["#2F6F73", "#A45A52", "#947340", "#5D6699", "#77915F"])
fig.update_layout(xaxis_title="Date", yaxis_range=[0, 105], hovermode="x unified")
st.plotly_chart(fig, width="stretch")

st.caption(
    f"Showing {area_data['area_number'].nunique()} {area_type} areas and "
    f"{len(area_data):,} weekly rows from {start_month} to {end_month}."
)

with st.expander("How the interval works"):
    st.write(
        "NVE's HentOffentligData endpoint does not accept start and end dates. "
        "It returns the complete public history, so the app caches that response "
        "and retains only the interval selected above for the table and plot."
    )
    st.markdown(
        "[NVE API documentation](https://biapi.nve.no/magasinstatistikk/swagger/index.html) · "
        "[About the reservoir statistics](https://www.nve.no/energi/analyser-og-statistikk/om-magasinstatistikken/)"
    )
