"""Checks for the Project 3 feedback update."""
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import geopandas as gpd
import numpy as np
import pandas as pd

from utils.quality_utils import (
    _weather_batch_summary, build_combined_weather_sample,
    load_nve_regions, load_open_meteo_region,
)


def fake_response(url, params, timeout):
    count = len(params["latitude"].split(","))
    dates = pd.date_range(params["start_date"], pd.Timestamp(params["end_date"]) + pd.Timedelta(hours=23), freq="h")
    times = dates.strftime("%Y-%m-%dT%H:%M").tolist()
    payload = [{"hourly": {"time": times, "precipitation": [float(i)] * len(times),
                           "temperature_2m": [10.0] * len(times)}} for i in map(float, params["latitude"].split(","))]
    return SimpleNamespace(status_code=200, raise_for_status=lambda: None, json=lambda: payload)


class WeatherFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        cache_patch = patch("utils.quality_utils.WEATHER_BATCH_CACHE", Path(self.temp_dir.name))
        cache_patch.start()
        self.addCleanup(cache_patch.stop)
        _weather_batch_summary.clear()
        load_open_meteo_region.clear()

    def test_combined_region_samples_are_inside_each_union(self):
        regions = load_nve_regions()
        sample = build_combined_weather_sample(regions)
        for name, codes in {"East": ["RS", "RØ"], "West": ["RV"], "North": ["RM", "RN"]}.items():
            selected = sample[sample.region_group == name]
            polygon = regions[regions.reg_code.isin(codes)].geometry.union_all()
            points = gpd.GeoSeries(gpd.points_from_xy(selected.longitude, selected.latitude), crs=4326)
            self.assertEqual(len(points), 1000)
            self.assertTrue(points.covered_by(polygon).all())

    def test_all_thousand_locations_contribute_to_mean(self):
        sample = pd.DataFrame({"area_group": ["NO3"] * 1000,
                               "latitude": np.linspace(63, 64, 1000),
                               "longitude": np.linspace(10, 11, 1000)})
        with patch("utils.quality_utils.time.sleep"), patch("utils.quality_utils.requests.get", side_effect=fake_response) as request:
            result = load_open_meteo_region("NO3", "2024-01-01", "2024-01-01", 1000, sample)
        self.assertEqual(request.call_count, 20)
        self.assertEqual(len(result), 24)
        np.testing.assert_allclose(result.precipitation, 63.5)

    def test_finished_batch_is_reused_after_memory_cache_is_cleared(self):
        coordinates = ((63.1, 10.1), (63.2, 10.2))
        with patch("utils.quality_utils.requests.get", side_effect=fake_response) as request:
            first = _weather_batch_summary(coordinates, "2024-01-01", "2024-01-01")
            self.assertEqual(request.call_count, 1)
        _weather_batch_summary.clear()
        with patch("utils.quality_utils.requests.get", side_effect=AssertionError("unexpected download")):
            second = _weather_batch_summary(coordinates, "2024-01-01", "2024-01-01")
        pd.testing.assert_frame_equal(first, second, check_exact=False, check_dtype=False)

    def test_incomplete_batch_cannot_be_reported_as_complete(self):
        sample = pd.DataFrame({"region_group": ["East"] * 50,
                               "latitude": np.linspace(60, 61, 50),
                               "longitude": np.linspace(10, 11, 50)})
        def incomplete(url, params, timeout):
            response = fake_response(url, params, timeout)
            payload = response.json()[:-1]
            response.json = lambda: payload
            return response
        with patch("utils.quality_utils.time.sleep"), patch("utils.quality_utils.requests.get", side_effect=incomplete):
            with self.assertRaisesRegex(ValueError, "no partial average"):
                load_open_meteo_region("East", "2024-01-01", "2024-01-01", 50, sample)


if __name__ == "__main__":
    unittest.main()
