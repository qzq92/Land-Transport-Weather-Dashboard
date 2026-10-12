import unittest

from utils.transport.cache import _road_infra_cache, clear_road_infra_cache


class TestTransportCacheHelpers(unittest.TestCase):
    def test_clear_road_infra_cache_sets_all_values_to_none(self):
        _road_infra_cache["taxi_stands"] = {"value": [1]}
        _road_infra_cache["bus_routes_bucket"] = 202605

        clear_road_infra_cache()

        for key, value in _road_infra_cache.items():
            self.assertIsNone(value, msg=f"Expected {key} to be None after clear")
