"""Check that the interactive plots keep the original weather calculations."""
import unittest
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from utils.interactive_weather import weather_check
from utils.quality_utils import lof_temperature_plot, spc_precipitation_plot


class InteractiveWeatherTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(320)
        self.data = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=120, freq='h'),
            'temperature_2m': 4 + rng.normal(size=120),
            'precipitation': np.maximum(0, rng.normal(size=120)),
        })
        self.data.loc[80, 'temperature_2m'] = 20
        self.data.loc[50, 'precipitation'] = 15

    def test_original_flags_are_kept(self):
        old, original = spc_precipitation_plot(self.data)
        _, flags, count = weather_check(self.data, 'Precipitation', 'SPC')
        plt.close(old)
        self.assertEqual((flags, count), (original['outliers'], original['observations']))
        old, original = lof_temperature_plot(self.data)
        _, flags, count = weather_check(self.data, 'Temperature', 'LOF')
        plt.close(old)
        self.assertEqual((flags, count), (original['anomalies'], original['observations']))

    def test_spc_flags_match_the_limits_on_the_original_scale(self):
        for property_name, column in (("Temperature", "temperature_2m"), ("Precipitation", "precipitation")):
            fig, count, total = weather_check(self.data, property_name, "SPC", cutoff=0.08, n_sd=3.0)
            values = np.asarray(fig.data[0].y)
            lower, upper = np.asarray(fig.data[2].y), np.asarray(fig.data[3].y)
            expected = (values < lower) | (values > upper)
            np.testing.assert_array_equal(values, self.data[column].to_numpy())
            np.testing.assert_allclose(np.asarray(fig.data[-1].y), values[expected])
            self.assertEqual(count, int(expected.sum()))
            self.assertEqual(total, len(values))
            self.assertGreater(count, 0)
            self.assertNotIn("SATV", [trace.name for trace in fig.data])

    def test_both_properties_can_be_used_for_both_methods(self):
        for property_name in ('Temperature', 'Precipitation'):
            for method in ('SPC', 'LOF'):
                fig, flags, count = weather_check(self.data, property_name, method)
                self.assertGreaterEqual(flags, 0)
                self.assertEqual(count, 120)
                self.assertGreaterEqual(len(fig.data), 2)


if __name__ == '__main__':
    unittest.main()
