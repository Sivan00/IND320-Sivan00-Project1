"""Compare reservoir fill for every area in one selected NVE area system."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import requests
import streamlit as st

from data_utils import AREA_TYPES, area_label, load_reservoirs


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
area_data = selected.loc[selected["area_type"] == area_type].copy()
if area_data.empty:
    st.info("NVE returned no measurements for this choice.")
    st.stop()

fig, ax = plt.subplots(figsize=(10.5, 5.5))
colors = ["#2F6F73", "#A45A52", "#947340", "#5D6699", "#77915F"]
# Each area gets its own line, so EL, NO and VASS are never mixed together.
for index, (area_number, rows) in enumerate(area_data.groupby("area_number")):
    rows = rows.sort_values("date")
    ax.plot(
        rows["date"],
        rows["fill_fraction"] * 100,
        label=area_label(area_type, int(area_number)),
        color=colors[index % len(colors)],
        linewidth=1.8,
    )

ax.set_title(f"Reservoir fill: {AREA_TYPES[area_type]}", loc="left", fontweight="bold")
ax.set_xlabel("Date")
ax.set_ylabel("Fill level (%)")
ax.set_ylim(0, 105)
# The light grid and open frame keep several area lines readable at once.
ax.grid(axis="y", color="#E7E7E7", linewidth=0.7)
ax.spines[["top", "right"]].set_visible(False)
locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
ax.legend(
    title="Area",
    loc="upper center",
    bbox_to_anchor=(0.5, -0.18),
    ncols=2,
    frameon=False,
    fontsize=9,
)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

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
