"""Checks for the first Project 4 functions."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

from utils.correlation_utils import sliding_weather_correlation
from utils.currency_utils import load_exchange_rates
from utils.forecast_utils import forecast_reservoir, monthly_exchange_rates


class Project4Tests(unittest.TestCase):
    def setUp(self):
        load_exchange_rates.clear()

    def test_exchange_rates_are_parsed_without_writing_a_csv(self):
        body = ("BASE_CUR;TIME_PERIOD;OBS_VALUE\n"
                "EUR;2024-01-02;11.2\nUSD;2024-01-02;10.3\n")
        response = SimpleNamespace(text=body, raise_for_status=lambda: None)
        with patch("utils.currency_utils.requests.get", return_value=response):
            rates = load_exchange_rates("2024-01-01", "2024-01-03")
        self.assertEqual(set(rates.currency), {"EUR", "USD"})
        self.assertEqual(len(monthly_exchange_rates(rates)), 1)

    def test_validation_does_not_look_at_later_targets(self):
        idx = pd.date_range("2017-01-01", periods=96, freq="MS")
        values = pd.Series(55 + 20 * np.sin(np.arange(len(idx)) * 2 * np.pi / 12), index=idx)
        _, first, _ = forecast_reservoir(values, lags=12, n_neighbors=3)
        changed = values.copy()
        changed.iloc[-1] = 0
        _, second, _ = forecast_reservoir(changed, lags=12, n_neighbors=3)
        np.testing.assert_allclose(first.predicted, second.predicted)

    def test_positive_lag_compares_earlier_weather_with_later_fill(self):
        dates = pd.date_range("2024-01-01", periods=12, freq="MS")
        weather_values = [1, 3, 2, 8, 4, 10, 5, 7, 2, 8, 1, 4]
        weather = pd.DataFrame({"time": dates, "precipitation": weather_values})
        fill = pd.Series([0, *weather_values[:-1]], index=dates, dtype=float)
        result = sliding_weather_correlation(fill, weather, "precipitation", window_months=4, lag_months=1)
        self.assertEqual(len(result), 8)
        np.testing.assert_allclose(result.correlation, 1.0, atol=1e-12)

    def test_missing_selected_exchange_rates_are_not_silently_filled(self):
        idx = pd.date_range("2017-01-01", periods=96, freq="MS")
        values = pd.Series(np.full(len(idx), 50.0), index=idx)
        rates = pd.DataFrame({"EUR": 10.0}, index=idx)
        rates.iloc[-5, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "missing"):
            forecast_reservoir(values, currencies=("EUR",), rates=rates)


if __name__ == "__main__":
    unittest.main()
