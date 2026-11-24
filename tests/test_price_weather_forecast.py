import unittest
from unittest.mock import patch, Mock
import numpy as np
import pandas as pd
from utils.forecast_utils import forecast_reservoir
from utils.price_utils import daily_spot_price


class AddedInputsTests(unittest.TestCase):
    def test_price_weights_daylight_saving_day_by_duration(self):
        edges = pd.date_range('2024-03-31', '2024-04-01', freq='h', tz='Europe/Oslo')
        rows = [{'time_start': a.isoformat(), 'time_end': b.isoformat(), 'NOK_per_kWh': i}
                for i, (a, b) in enumerate(zip(edges[:-1], edges[1:]))]
        response = Mock(); response.json.return_value = rows; response.raise_for_status.return_value = None
        with patch('utils.price_utils.requests.get', return_value=response):
            daily_spot_price.clear()
            self.assertAlmostEqual(daily_spot_price('NO1', '2024-03-31'), 11.0)
            daily_spot_price.clear()
            response.json.return_value = rows[:-1]
            with self.assertRaises(ValueError): daily_spot_price('NO1', '2024-03-31')

    def test_weather_features_reject_missing_and_do_not_use_future_values(self):
        idx = pd.date_range('2018-01-01', periods=72, freq='MS')
        series = pd.Series(50 + 20 * np.sin(np.arange(72) * np.pi / 6), index=idx)
        weather = pd.DataFrame({'temperature': np.arange(72, dtype=float)}, index=idx)
        args = dict(lags=3, n_neighbors=3, weather_properties=('temperature',))
        _, test1, _ = forecast_reservoir(series, weather=weather, **args)
        changed = weather.copy(); changed.iloc[-1, 0] = 999
        _, test2, _ = forecast_reservoir(series, weather=changed, **args)
        pd.testing.assert_series_equal(test1.predicted, test2.predicted)
        weather.iloc[10, 0] = np.nan
        with self.assertRaisesRegex(ValueError, 'missing'):
            forecast_reservoir(series, weather=weather, **args)

if __name__ == '__main__': unittest.main()
