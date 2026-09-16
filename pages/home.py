"""Home page for the reservoir app."""

import streamlit as st

from data_utils import load_reservoirs, national_series


st.title("Reservoir levels in Norway")
st.write(
    "This is my first IND320 app. It reads the local reservoirs.csv file and "
    "lets me inspect the weekly data before moving to a database in the next project part."
)

# The CSV includes nine area series. The plots use the national NO/0 series so
# each week appears once; the full imported dataset is still kept in the app.
data = load_reservoirs()
national = national_series(data)

st.subheader("What is in the file?")
st.write(
    f"The file has {len(data):,} rows and {len(data.columns)} columns. "
    f"The national series has {len(national):,} weekly observations, from "
    f"{national['date'].min():%d %B %Y} to {national['date'].max():%d %B %Y}."
)
st.write(
    "Use the sidebar to see the column-by-column table, explore plots, or read "
    "the short note on what this first version covers."
)
