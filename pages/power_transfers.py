"""Show the ENTSO-E transfer data that has been curated in MongoDB."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from calendar import month_name
from calendar import isleap

from utils.database_utils import load_power_transfers


st.title("Cross-border power transfers")
st.write(
    "The app reads this page from MongoDB. The rows are first collected from "
    "ENTSO-E, stored in Cassandra and filtered with Spark in the notebook."
)

# This page uses the curated collection from the notebook, rather than calling ENTSO-E again.
try:
    transfers = load_power_transfers()
except Exception as error:
    # A connection error should not expose the private URI in the public app.
    st.error(
        "MongoDB could not be reached. Check the private connection settings "
        "and Atlas network access, then try again."
    )
    # The error type is safe to show and helps me find the problem without
    # printing the connection string or any login details.
    st.caption(f"Connection check: {type(error).__name__}")
    st.stop()

if transfers.empty:
    st.info("MongoDB is connected, but the power_transfers collection is still empty.")
    st.stop()

left, right = st.columns(2, gap="large")
connections = sorted(transfers["connection"].unique())
years = sorted(transfers["year"].unique(), reverse=True)

with left:
    st.subheader("Yearly direction split")
    # I keep the connection fixed for both charts so their values can be compared.
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
    fig = px.pie(values=direction_totals.values, names=direction_totals.index,
                 title=f"{connection}, {year}", color_discrete_sequence=["#2F6F73", "#D58A5C"])
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Recorded transfer: {direction_totals.sum() / 1e6:,.2f} TWh")

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
    # Pills let me compare any combination of months without changing the left-hand year.
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
    if chosen_months:
        fig = go.Figure()
        for direction, rows in monthly.groupby("direction"):
            for index, chosen_month in enumerate(chosen_months):
                month_rows = rows.loc[rows["month"] == chosen_month].sort_values("timestamp")
                if month_rows.empty:
                    continue
                # Convert stored UTC timestamps to Norwegian wall time for the displayed axis.
                local_times = month_rows["timestamp"].dt.tz_convert("Europe/Oslo").dt.tz_localize(None)
                fig.add_scatter(x=local_times, y=month_rows["value_mw"],
                                name=direction, legendgroup=direction, showlegend=index == 0,
                                line={"color": {"Into Norway": "#2F6F73", "Out of Norway": "#D58A5C"}.get(direction, "#947340")})
        fig.update_layout(title=f"{connection}: selected months in {year}",
                          xaxis_title="Date (Norwegian time)", yaxis_title="MW")
        st.plotly_chart(fig, width="stretch")
        st.caption("Times are shown in Europe/Oslo; the autumn clock change repeats one local hour.")

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
