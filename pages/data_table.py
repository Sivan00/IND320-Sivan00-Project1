"""A row-per-column overview with first-month sparklines."""

import pandas as pd
import streamlit as st

from data_utils import load_reservoirs, national_series


st.title("Data table")
data = load_reservoirs()
national = national_series(data)

# January 1995 is the first calendar month in the sorted national series.
# I use its weekly rows for every sparkline so the mini charts are comparable.
first_month = national["date"].dt.to_period("M").min()
month_rows = national.loc[national["date"].dt.to_period("M") == first_month]

summary_rows = []
for column in data.columns:
    month_values = month_rows[column]
    numeric = pd.api.types.is_numeric_dtype(month_values)

    # LineChartColumn needs numbers. Date and text fields still get their own
    # table rows, but an empty sparkline is more honest than invented numbers.
    sparkline = month_values.astype(float).tolist() if numeric else []
    # I take the example from the same national series as the mini chart,
    # so an area label in this row does not disagree with the plotted values.
    example = national[column].iloc[0]
    if column == "date":
        example = example.strftime("%Y-%m-%d")

    summary_rows.append(
        {
            "Column": column,
            "Data type": str(data[column].dtype),
            "Example": str(example),
            "First month": sparkline,
        }
    )

st.write(
    f"One row for each of the {len(data.columns)} imported columns. The small lines "
    f"show the national weekly values in {first_month.strftime('%B %Y')}."
)
st.dataframe(
    pd.DataFrame(summary_rows),
    column_config={
        "First month": st.column_config.LineChartColumn(
            "First month", help="Weekly numeric values for the first month"
        )
    },
    hide_index=True,
    width="stretch",
)
st.caption("Text and date columns have no line because they are not numeric measurements.")

st.subheader("A few imported rows, with English column names")
st.dataframe(data.head(12), hide_index=True, width="stretch")
