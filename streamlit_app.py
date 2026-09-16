"""Entry point for my first IND320 Streamlit app."""

import streamlit as st


# Keeping navigation here means every page gets the same sidebar menu.
st.set_page_config(page_title="Reservoir levels | IND320", layout="wide")

home = st.Page("pages/home.py", title="Home", default=True)
table = st.Page("pages/data_table.py", title="Data table")
plots = st.Page("pages/plots.py", title="Plots")
notes = st.Page("pages/notes.py", title="Notes")

page = st.navigation([home, table, plots, notes], position="sidebar")
st.sidebar.caption("IND320 project 1 | Sivan")
page.run()
