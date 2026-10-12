"""Show the ENTSO-E transfer data that has been curated in MongoDB."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import streamlit as st
from calendar import month_name
from calendar import isleap
from zoneinfo import ZoneInfo

from database_utils import load_power_transfers


st.title("Cross-border power transfers")
st.write(
    "The app reads this page from MongoDB. The rows are first collected from "
    "ENTSO-E, stored in Cassandra and filtered with Spark in the notebook."
)

try:
    transfers = load_power_transfers()
except Exception:
    # A connection error should not expose the private URI in the public app.
    st.error(
        "MongoDB could not be reached. Check the private connection settings "
        "and Atlas network access, then try again."
    )
    st.stop()

if transfers.empty:
    st.info("MongoDB is connected, but the power_transfers collection is still empty.")
    st.stop()

left, right = st.columns(2, gap="large")
connections = sorted(transfers["connection"].unique())
years = sorted(transfers["year"].unique(), reverse=True)

with left:
    st.subheader("Yearly direction split")
    connection = st.radio("Connection", connections, index=connections.index("NO2-DK1") if "NO2-DK1" in connections else 0)
    year = st.selectbox("Year", years)
    annual = transfers.loc[
        (transfers["connection"] == connection) & (transfers["year"] == year)
    ]

    # Summing the hourly MWh values gives the amount transferred in each direction.
    direction_totals = annual.groupby("direction")["transfer_mwh"].sum(min_count=1)
    expected_hours = (366 if isleap(int(year)) else 365) * 24
    recorded = annual.groupby("direction")["value_mw"].count()
    if len(recorded) != 2 or recorded.lt(expected_hours).any():
        st.warning("This year has missing readings. The pie shows recorded energy only.")
    if direction_totals.isna().any() or direction_totals.sum() <= 0:
        st.warning("There is not enough recorded transfer to draw this pie chart.")
        st.stop()
    fig, ax = plt.subplots(figsize=(5.8, 4.6))
    ax.pie(
        direction_totals,
        labels=direction_totals.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=["#2F6F73", "#D58A5C"],
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    ax.set_title(f"{connection}, {year}")
    ax.set_xlabel(f"Recorded transfer: {direction_totals.sum() / 1e6:,.2f} TWh")
    st.pyplot(fig)
    plt.close(fig)

with right:
    st.subheader("Monthly transfer pattern")
    month_numbers = sorted(
        transfers.loc[
            (transfers["year"] == year)
            & (transfers["connection"] == connection),
            "month",
        ].unique()
    )
    month_labels = {month_name[number]: number for number in month_numbers}
    chosen_month_names = st.pills(
        "Months",
        list(month_labels),
        default=[month_name[month_numbers[0]]],
        selection_mode="multi",
    )
    chosen_months = [month_labels[label] for label in chosen_month_names]
    monthly = transfers.loc[
        (transfers["year"] == year)
        & (transfers["connection"] == connection)
        & (transfers["month"].isin(chosen_months))
    ]

    if not chosen_months:
        st.info("Choose at least one month to show the line plot.")
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    # The connection and year come from the left column. Colour and line style
    # then make the two directions readable across any set of selected months.
    for (line_connection, direction), rows in monthly.groupby(
        ["connection", "direction"]
    ):
        for index, chosen_month in enumerate(chosen_months):
            month_rows = rows.loc[rows["month"] == chosen_month]
            if month_rows.empty:
                continue
            # Plotting each month separately leaves a real gap between January
            # and October instead of drawing a misleading diagonal line.
            ax.plot(
                month_rows["timestamp"],
                month_rows["value_mw"],
                label=f"{line_connection} | {direction}" if index == 0 else None,
                linewidth=1.5,
                color={"Into Norway": "#2F6F73", "Out of Norway": "#D58A5C"}[direction],
                linestyle="--" if direction == "Into Norway" else "-",
            )
    if chosen_month_names:
        months_in_title = (
            ", ".join(chosen_month_names)
            if len(chosen_month_names) <= 4
            else f"{len(chosen_month_names)} selected months"
        )
        ax.set_title(
            f"{connection}: {months_in_title} {year}",
            loc="left",
            fontweight="bold",
        )
    ax.set_xlabel("Date (Norwegian time)")
    ax.set_ylabel("MW")
    ax.grid(axis="y", color="#E7E7E7", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    locator = mdates.AutoDateLocator(minticks=3, maxticks=6, tz=ZoneInfo("Europe/Oslo"))
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator, tz=ZoneInfo("Europe/Oslo")))
    if chosen_months:
        ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncols=2)
    fig.tight_layout()
    if chosen_months:
        st.pyplot(fig)
    plt.close(fig)

with st.expander("Data source and preparation"):
    st.write(
        "ENTSO-E Transparency Platform provides the cross-border transfer series. "
        "The notebook stores the raw rows in local Cassandra, uses Spark to keep "
        "the columns needed here, and writes the curated rows to MongoDB."
    )
    st.write(
        "The series describe physical flows in MW, not electricity production. "
        "For a complete hour, average MW multiplied by one hour gives MWh. "
        "The yearly pie compares the recorded energy in each direction. "
        "Dates and calendar years follow Norwegian time."
    )
    st.markdown(
        "[ENTSO-E physical flows](https://transparencyplatform.zendesk.com/hc/en-us/articles/16583889683476-Physical-Flows-12-1-G)"
    )
