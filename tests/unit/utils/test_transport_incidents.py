import unittest
from unittest.mock import patch

from conf.api_urls import FAULTY_TRAFFIC_LIGHTS_URL
from utils.transport.incidents import (
    _lta_headers,
    fetch_faulty_traffic_lights_data_async,
)


class TestTransportIncidentsHelpers(unittest.TestCase):
    @patch("utils.transport.incidents.os.getenv", return_value=None)
    def test_lta_headers_returns_none_without_api_key(self, _mock_getenv):
        self.assertIsNone(_lta_headers())

    @patch("utils.transport.incidents.os.getenv", return_value="abc123")
    def test_lta_headers_contains_expected_fields(self, _mock_getenv):
        headers = _lta_headers()
        self.assertIsNotNone(headers)
        self.assertEqual(headers["AccountKey"], "abc123")
        self.assertIn("User-Agent", headers)
        self.assertEqual(headers["Content-Type"], "application/json")

    @patch(
        "utils.transport.incidents.fetch_url_2min_cached",
        return_value={"value": []},
    )
    @patch("utils.transport.incidents.os.getenv", return_value="abc123")
    def test_faulty_lights_fetch_uses_documented_endpoint(
        self,
        _mock_getenv,
        mock_fetch,
    ):
        result = fetch_faulty_traffic_lights_data_async().result(timeout=2)

        self.assertEqual(result, {"value": []})
        mock_fetch.assert_called_once()
        self.assertEqual(mock_fetch.call_args.args[0], FAULTY_TRAFFIC_LIGHTS_URL)
        self.assertTrue(FAULTY_TRAFFIC_LIGHTS_URL.endswith("/FaultyTrafficLights"))
