"""Simple monthly reservoir forecasts using past observations and River."""

import numpy as np
import pandas as pd
from river import neighbors


def monthly_reservoir(data: pd.DataFrame, area_code: str) -> pd.Series:
    """Turn weekly fill observations for one electricity area into monthly means."""
    if area_code not in {"NO1", "NO2", "NO3", "NO4", "NO5"}:
        raise ValueError("Choose an electricity area from NO1 to NO5.")
    rows = data.loc[(data["area_type"] == "EL") & (data["area_number"] == int(area_code[-1]))].copy()
    rows["date"] = pd.to_datetime(rows["date"])
    monthly = rows.set_index("date")["fill_fraction"].sort_index().resample("MS").mean().mul(100)
    # The current month is incomplete, so it should not be treated as a full month.
    current_month = pd.Timestamp.now(tz="Europe/Oslo").tz_localize(None).to_period("M").to_timestamp()
    monthly = monthly.loc[monthly.index < current_month]
    monthly.name = "fill_percent"
    return monthly


def monthly_exchange_rates(rates: pd.DataFrame) -> pd.DataFrame:
    """Average the observed business-day exchange rates for each month."""
    wide = rates.pivot(index="date", columns="currency", values="nok_per_unit")
    return wide.resample("MS").mean().rename_axis(None, axis=1)


def _features(history: list[float], month: pd.Timestamp, lags: int,
              last_rates: dict[str, float]) -> dict[str, float]:
    # Scaling the lag values keeps them comparable with the calendar features.
    values = {f"lag_{i}": history[-i] / 100 for i in range(1, lags + 1)}
    values["month_sin"] = float(np.sin(2 * np.pi * (month.month - 1) / 12))
    values["month_cos"] = float(np.cos(2 * np.pi * (month.month - 1) / 12))
    values.update({f"{name}_NOK": float(value) / 10 for name, value in last_rates.items()})
    return values


def forecast_reservoir(
    series: pd.Series, horizon: int = 3, history_months: int = 120,
    lags: int = 12, n_neighbors: int = 3, rates: pd.DataFrame | None = None,
    currencies: tuple[str, ...] = (), validation_months: int = 12,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Train on past months, test chronologically, then predict recursively.

    Exchange-rate features use the previous month's average. Future rates are
    held at their last known values; they are assumptions, not predictions.
    """
    if horizon < 1 or lags < 1 or n_neighbors < 1 or history_months < 1 or validation_months < 1:
        raise ValueError("Use positive values for the model settings.")
    if len(set(currencies)) != len(currencies) or not set(currencies) <= {"EUR", "USD"}:
        raise ValueError("Choose EUR, USD, both or no exchange rates.")
    data = series.sort_index().tail(history_months).astype(float)
    if data.index.has_duplicates or data.isna().any() or not np.isfinite(data).all():
        raise ValueError("The chosen monthly reservoir series must contain unique, nonmissing values.")
    expected = pd.date_range(data.index.min(), data.index.max(), freq="MS")
    if not data.index.equals(expected):
        raise ValueError("The selected history must have one value for every month.")
    if len(data) < lags + validation_months + n_neighbors + 1:
        raise ValueError("Choose a longer history or fewer validation months and neighbours.")
    if currencies:
        if rates is None or not set(currencies).issubset(rates.columns):
            raise ValueError("The selected exchange rates are not available.")
        aligned_rates = rates.reindex(data.index)[list(currencies)]
        if aligned_rates.isna().any().any():
            raise ValueError("Exchange rates are missing in the selected history.")
    else:
        aligned_rates = pd.DataFrame(index=data.index)
    model = neighbors.KNNRegressor(
        n_neighbors=n_neighbors, engine=neighbors.LazySearch(window_size=history_months),
    )
    history = data.iloc[:lags].tolist()
    validation = []
    first_validation = len(data) - validation_months
    for i in range(lags, len(data)):
        previous_rates = aligned_rates.iloc[i - 1].to_dict()
        features = _features(history, data.index[i], lags, previous_rates)
        # Predict before learning the current month, so validation only uses past data.
        if i >= first_validation:
            predicted = model.predict_one(features)
            validation.append({"date": data.index[i], "actual": float(data.iloc[i]), "predicted": float(predicted)})
        model.learn_one(features, float(data.iloc[i]))
        history.append(float(data.iloc[i]))
    last_rates = aligned_rates.iloc[-1].to_dict() if currencies else {}
    future_dates = pd.date_range(data.index[-1] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    predicted_values = []
    for month in future_dates:
        features = _features(history, month, lags, last_rates)
        prediction = float(model.predict_one(features))
        # A filling percentage must remain within the physical range.
        prediction = float(np.clip(prediction, 0, 100))
        predicted_values.append(prediction)
        history.append(prediction)
    forecast = pd.DataFrame({"date": future_dates, "predicted": predicted_values})
    validation = pd.DataFrame(validation)
    metrics = {"mae": float((validation.actual - validation.predicted).abs().mean()),
               "history_months": len(data), "validation_months": len(validation),
               "currencies": list(currencies), "last_month": str(data.index[-1].date())}
    return forecast, validation, metrics
