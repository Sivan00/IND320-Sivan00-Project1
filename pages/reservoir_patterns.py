"""Reservoir seasonal pattern and frequency views for project part 3."""

from datetime import date

import matplotlib.pyplot as plt
import streamlit as st

from utils.data_utils import load_reservoirs
from utils.quality_utils import fill_spectrogram, stl_decomposition


st.title("Reservoir patterns")
st.write(
    "These two views look at the same weekly fill-level series in different ways. "
    "STL separates the seasonal cycle from the longer trend, while the spectrogram "
    "shows which repeating patterns are strongest."
)

area_code = st.session_state["electricity_area"]
area_number = int(area_code[-1])
# The NVE series stays weekly here; I do not merge it with hourly weather data.
reservoirs = load_reservoirs()
# I filter to one electricity area before decomposing so the weekly observations stay in order.
selected = reservoirs.loc[
    (reservoirs["area_type"] == "EL") & (reservoirs["area_number"] == area_number)
].sort_values("date")
if selected.empty:
    st.info(f"NVE has not returned a fill-level series for {area_code}.")
    st.stop()
fill = selected.set_index("date")["fill_fraction"].mul(100)
st.caption(
    f"Using {len(fill):,} weekly observations for {area_code}, "
    f"from {fill.index.min():%d %b %Y} to {fill.index.max():%d %b %Y}."
)

stl_tab, spectrum_tab = st.tabs(["STL decomposition", "Spectrogram"])
with stl_tab:
    st.write(
        "The series is weekly, so a period of 52 represents one year. "
        "I leave the trend smoother automatic by default and keep robust fitting on "
        "to reduce the effect of unusual weeks."
    )
    # These settings let me compare how the smooth seasonal curve changes.
    left, right = st.columns(2)
    with left:
        seasonal = st.select_slider("Seasonal smoother", options=[7, 9, 11, 13, 15, 17, 19], value=13)
        robust = st.checkbox("Robust fitting", value=True)
    with right:
        trend_choice = st.selectbox("Trend smoother", ["Automatic", 105, 157, 209, 261])
        period = st.number_input("Seasonal period (weeks)", min_value=2, max_value=104, value=52)
    # The utility returns both the figure and components so the result can be checked.
    try:
        trend = None if trend_choice == "Automatic" else int(trend_choice)
        fig, components = stl_decomposition(
            fill, period=int(period), seasonal_smoother=int(seasonal),
            trend_smoother=trend, robust=robust,
        )
        st.pyplot(fig)
        plt.close(fig)
        st.write(
            f"The decomposition uses {len(components):,} observations. "
            f"The last fitted trend value is {components['trend'].iloc[-1]:.1f}%."
        )
    except ValueError as error:
        st.warning(str(error))

with spectrum_tab:
    st.write(
        "The spectrogram uses overlapping windows to show how the strength of "
        "different frequencies changes over time. The fill series itself is still "
        "weekly, so the frequency axis is in cycles per year."
    )
    # A shorter window shows changes in more detail; overlap makes the timeline less choppy.
    window = st.slider("Window length (weeks)", min_value=26, max_value=min(260, len(fill)), value=min(104, len(fill)))
    overlap = st.slider(
        "Overlap (weeks)", min_value=0, max_value=window - 1,
        value=min(78, window - 1),
    )
    # Window size and overlap are exposed because they change the time-frequency detail.
    try:
        fig, summary = fill_spectrogram(
            fill, window_weeks=int(window), overlap_weeks=int(overlap)
        )
        st.pyplot(fig)
        plt.close(fig)
        st.caption(
            f"The calculation uses {summary['observations']:,} weekly values and "
            f"creates {summary['time_windows']} overlapping windows."
        )
    except ValueError as error:
        st.warning(str(error))
