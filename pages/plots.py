"""Explore one CSV column or compare the measurements on separate tracks."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from data_utils import MEASUREMENTS, load_reservoirs, national_series


st.title("Reservoir plots")
data = load_reservoirs()
national = national_series(data)

# Month labels are strings here because select_slider works well with an
# ordered list. A two-value default selects the first month as a range.
months = national["date"].dt.to_period("M").astype(str).unique().tolist()
choice = st.selectbox("Column", ["All columns"] + data.columns.tolist())
start_month, end_month = st.select_slider(
    "Months",
    options=months,
    value=(months[0], months[0]),
)

month_keys = national["date"].dt.to_period("M").astype(str)
selected = national.loc[month_keys.between(start_month, end_month)].copy()
st.write(
    f"Showing {len(selected)} national weekly observations from "
    f"{start_month} to {end_month}."
)

fig, ax = plt.subplots(figsize=(10, 6 if choice == "All columns" else 4.8))
fig.patch.set_facecolor("white")
palette = ["#2F6F73", "#A45A52", "#947340", "#5D6699", "#77915F"]
date_on_x = True

if choice == "All columns":
    # TWh and fractions cannot share a meaningful y-axis as raw numbers.
    # I give each 0–1-scaled line its own track because fill fraction and
    # stored energy nearly cover each other on a single axis.
    track_gap = 1.25
    for track, ((column, (label, _, _)), color) in enumerate(zip(MEASUREMENTS.items(), palette)):
        entire = national[column]
        spread = entire.max() - entire.min()
        # A constant column has no range to divide by. It appears as a flat
        # baseline on its track; the single-column plot still shows actual TWh.
        scaled = (selected[column] - entire.min()) / spread if spread else pd.Series(0.0, index=selected.index)
        baseline = track * track_gap
        ax.axhline(baseline, color="#E7E7E7", linewidth=0.7, zorder=0)
        ax.plot(
            selected["date"], scaled + baseline, color=color, linewidth=2,
            marker="o" if len(selected) <= 12 else None, markersize=4,
        )
    ax.set_yticks(
        [track * track_gap for track in range(len(MEASUREMENTS))],
        [label for label, _, _ in MEASUREMENTS.values()],
    )
    ax.set_ylabel("0–1 per track")
    ax.set_title("National reservoir measurements")
    ax.set_ylim(-0.15, (len(MEASUREMENTS) - 1) * track_gap + 1.05)
    st.caption(
        "Each line uses its own 0–1 historical range. The separate tracks keep "
        "similar curves visible; the capacity line is flat because it is constant here."
    )
elif choice in MEASUREMENTS:
    label, unit, multiplier = MEASUREMENTS[choice]
    ax.plot(selected["date"], selected[choice] * multiplier,
            color=palette[0], linewidth=2, marker="o" if len(selected) <= 12 else None,
            markersize=4)
    ax.set_title(label)
    ax.set_ylabel(unit)
elif pd.api.types.is_numeric_dtype(selected[choice]):
    # The selector includes every CSV column, even numeric calendar/area keys.
    # I plot those when selected but label them as metadata, not measurements.
    ax.plot(selected["date"], selected[choice], color=palette[2], linewidth=2,
            marker="o" if len(selected) <= 12 else None, markersize=4)
    ax.set_title(f"{choice} (metadata)")
    ax.set_ylabel("Value")
elif choice == "date":
    # Date is already the horizontal axis. A small dot per week shows the
    # records without pretending that dates are measurements on a y-axis.
    ax.scatter(selected["date"], [1] * len(selected), color=palette[0], s=28)
    ax.set_yticks([])
    ax.set_ylabel("Weekly records")
    ax.set_title("Dates in the selected period")
else:
    # A long list of dates hid the small bars beside the year-one placeholder.
    # Grouping that field keeps both the placeholder and recorded values visible.
    if choice == "next_publication_date":
        placeholder = selected[choice].astype(str).str.startswith("0001-01-01")
        counts = pd.Series({"Placeholder": int(placeholder.sum()),
                            "Recorded": int((~placeholder).sum())})
    else:
        counts = selected[choice].astype(str).value_counts().sort_values()
    ax.barh(counts.index, counts.values, color=palette[1])
    ax.set_title(f"{choice} (counts)")
    ax.set_xlabel("Weeks")
    ax.set_ylabel(choice.replace("_", " "))
    date_on_x = False

if date_on_x:
    ax.set_xlabel("Date")
    # Concise dates show days for a single month, but switch to months and
    # years when I widen the selection. Repeated "Jan 1995" ticks were messy.
    date_locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
    ax.xaxis.set_major_locator(date_locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(date_locator))
    ax.margins(x=0.04)
ax.set_axisbelow(True)
ax.grid(axis="x" if not date_on_x or choice == "All columns" else "y",
        color="#E7E7E7", linewidth=0.7)
ax.spines[["top", "right"]].set_visible(False)
title_text = ax.get_title()
ax.set_title("")
ax.set_title(title_text, loc="left", fontsize=13, fontweight="bold", pad=12)
# The combined chart needs space on the left for its five track labels.
fig.subplots_adjust(left=0.29 if choice == "All columns" else 0.13,
                    right=0.97, top=0.88, bottom=0.16)
st.pyplot(fig)
plt.close(fig)
