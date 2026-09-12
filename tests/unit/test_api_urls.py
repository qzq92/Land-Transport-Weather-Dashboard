"""Tests that dashboard HTTP endpoints live in conf and are not duplicated."""

import unittest
from pathlib import Path
from unittest.mock import patch

import conf.api_urls as api_urls
from conf.api_urls import (
    BUS_ARRIVAL_URL,
    CARPARK_AVAILABILITY_URL,
    DATA_GOV_DATASET_API_BASE,
    DATA_GOV_REALTIME_API_BASE,
    DATA_GOV_V1_API_BASE,
    FLOOD_ALERTS_URL,
    GTFS_TRAIN_SERVICE_ALERTS_URL,
    GTFS_TRAIN_TRIP_UPDATES_URL,
    LTA_DATAMALL_BASE,
    ONEMAP_BASE,
    ONEMAP_SEARCH_URL,
    ONEMAP_SITE_URL,
    ONEMAP_TILES_URL,
    PARKS_DATASET_ID,
    PARKS_POLL_DOWNLOAD_URL,
    SLA_SITE_URL,
    TAXI_API_URL,
    TAXI_STANDS_URL,
    WEATHER_2H_FORECAST_URL,
    WEATHER_24H_FORECAST_URL,
    poll_download_url,
)
from utils.data_download_helper import get_initiate_download_url
from utils.map_utils import get_onemap_attribution
from utils.realtime_weather_api import fetch_realtime_data
from utils.transport import gtfs_train_alerts
from utils.transport import taxi as taxi_utils

REPO_ROOT = Path(__file__).resolve().parents[2]
HARDCODED_API_HOSTS = (
    "api.data.gov.sg",
    "api-open.data.gov.sg",
    "datamall2.mytransport.sg",
    "www.onemap.gov.sg/api",
    "www.onemap.gov.sg/maps",
    "pointhi/leaflet-color-markers",
    "cdnjs.cloudflare.com/ajax/libs/leaflet",
)


class TestApiUrlsConfig(unittest.TestCase):
    def test_url_and_base_constants_use_https(self):
        named_urls = []
        for name in dir(api_urls):
            if not (name.endswith("_URL") or name.endswith("_BASE")):
                continue
            value = getattr(api_urls, name)
            if isinstance(value, str) and value.startswith("http"):
                named_urls.append((name, value))
                self.assertTrue(
                    value.startswith("https://"),
                    f"{name} must use https: {value}",
                )
        self.assertGreaterEqual(len(named_urls), 20)

    def test_resource_urls_are_composed_from_bases(self):
        self.assertTrue(TAXI_API_URL.startswith(DATA_GOV_V1_API_BASE))
        self.assertTrue(WEATHER_2H_FORECAST_URL.startswith(DATA_GOV_V1_API_BASE))
        self.assertTrue(WEATHER_24H_FORECAST_URL.startswith(DATA_GOV_REALTIME_API_BASE))
        self.assertTrue(BUS_ARRIVAL_URL.startswith(LTA_DATAMALL_BASE))
        self.assertTrue(CARPARK_AVAILABILITY_URL.startswith(LTA_DATAMALL_BASE))
        self.assertTrue(ONEMAP_SEARCH_URL.startswith(ONEMAP_BASE))
        self.assertEqual(
            PARKS_POLL_DOWNLOAD_URL,
            poll_download_url(PARKS_DATASET_ID),
        )

    def test_python_modules_do_not_hardcode_api_hosts(self):
        offenders = []
        skip_parts = {".venv", "__pycache__", ".pytest_cache"}
        for path in REPO_ROOT.rglob("*.py"):
            if path.name in {"api_urls.py", "test_api_urls.py"}:
                continue
            if skip_parts.intersection(path.parts):
                continue
            text = path.read_text(encoding="utf-8")
            for host in HARDCODED_API_HOSTS:
                if host in text:
                    offenders.append(f"{path.relative_to(REPO_ROOT)}: {host}")
        self.assertEqual(offenders, [])

    def test_onemap_tile_template_keeps_zoom_placeholders(self):
        self.assertIn("{z}/{x}/{y}", ONEMAP_TILES_URL)
        self.assertNotIn("{{z}}", ONEMAP_TILES_URL)

    def test_transport_helpers_import_conf_values(self):
        self.assertEqual(taxi_utils.TAXI_API_URL, TAXI_API_URL)
        self.assertEqual(taxi_utils.TAXI_STANDS_URL, TAXI_STANDS_URL)
        self.assertEqual(
            gtfs_train_alerts.GTFS_TRAIN_SERVICE_ALERTS_URL,
            GTFS_TRAIN_SERVICE_ALERTS_URL,
        )
        self.assertEqual(
            gtfs_train_alerts.GTFS_TRAIN_TRIP_UPDATES_URL,
            GTFS_TRAIN_TRIP_UPDATES_URL,
        )

    def test_initiate_download_url_uses_dataset_base(self):
        dataset_id = "d_example"
        url = get_initiate_download_url(dataset_id)
        self.assertTrue(url.startswith(DATA_GOV_DATASET_API_BASE))
        self.assertTrue(url.endswith(f"{dataset_id}/initiate-download"))

    def test_onemap_attribution_uses_conf_site_urls(self):
        attribution = get_onemap_attribution()
        self.assertIn(ONEMAP_SITE_URL, attribution)
        self.assertIn(SLA_SITE_URL, attribution)

    @patch("utils.realtime_weather_api.fetch_url_2min_cached", return_value={"ok": True})
    def test_realtime_weather_fetch_uses_conf_base(self, mock_fetch):
        data = fetch_realtime_data("air-temperature")
        self.assertEqual(data, {"ok": True})
        mock_fetch.assert_called_once()
        called_url = mock_fetch.call_args[0][0]
        self.assertEqual(called_url, f"{DATA_GOV_REALTIME_API_BASE}/air-temperature")
        self.assertTrue(FLOOD_ALERTS_URL.startswith(DATA_GOV_REALTIME_API_BASE))
