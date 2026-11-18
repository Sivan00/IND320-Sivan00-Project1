"""Compare monthly reservoir filling and weather over a moving window."""

import pandas as pd


def sliding_weather_correlation(
    reservoir: pd.Series, weather: pd.DataFrame, property_name: str,
    window_months: int = 6, lag_months: int = 0,
) -> pd.DataFrame:
    """Correlate monthly fill with weather from the same or an earlier month.

    A positive lag compares earlier weather with later reservoir filling.
    No correlation is shown until the entire selected window is available.
    """
    if property_name not in {"precipitation", "temperature_2m"}:
        raise ValueError("Choose precipitation or temperature.")
    if window_months < 3 or lag_months < 0:
        raise ValueError("Use a window of at least three months and a nonnegative lag.")
    if not {"time", property_name}.issubset(weather.columns):
        raise ValueError("The weather data is missing the selected property.")
    hourly = weather.copy()
    hourly["time"] = pd.to_datetime(hourly["time"])
    monthly_weather = hourly.set_index("time")[property_name].sort_index().resample("MS").mean()
    monthly_fill = reservoir.sort_index().resample("MS").mean()
    combined = pd.concat([monthly_fill.rename("fill_percent"), monthly_weather.rename("weather")], axis=1)
    # Reindex before shifting so a missing calendar month cannot count as a lag.
    if combined.empty:
        raise ValueError("No monthly values were available.")
    combined = combined.reindex(pd.date_range(combined.index.min(), combined.index.max(), freq="MS"))
    combined["weather_with_lag"] = combined.weather.shift(lag_months)
    combined = combined.loc[monthly_weather.index.min():monthly_weather.index.max()]
    combined["correlation"] = combined.fill_percent.rolling(window_months, min_periods=window_months).corr(combined.weather_with_lag)
    return combined.loc[combined["correlation"].notna()].rename_axis("date").reset_index()
