import unittest
from unittest.mock import patch

from google.transit import gtfs_realtime_pb2

from utils.transport.gtfs_train_alerts import (
    fetch_gtfs_train_service_alerts,
    fetch_gtfs_train_trip_updates,
    merge_gtfs_with_legacy_status,
)


class TestGtfsTrainAlerts(unittest.TestCase):
    @staticmethod
    def _new_feed():
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        return feed

    @patch("utils.transport.gtfs_train_alerts._fetch_gtfs_payload")
    def test_fetch_gtfs_service_alerts_parses_disruption_line(self, mock_fetch_payload):
        feed = self._new_feed()
        entity = feed.entity.add()
        entity.id = "alert-1"
        alert = entity.alert
        alert.effect = gtfs_realtime_pb2.Alert.Effect.SIGNIFICANT_DELAYS
        informed_entity = alert.informed_entity.add()
        informed_entity.route_id = "NSL"
        translation = alert.description_text.translation.add()
        translation.text = "NSL experiencing delays"
        mock_fetch_payload.return_value = feed.SerializeToString()

        result = fetch_gtfs_train_service_alerts()

        self.assertIn("NSL", result)
        self.assertEqual(result["NSL"]["status"], 2)
        self.assertEqual(result["NSL"]["status_text"], "Service disruption")

    @patch("utils.transport.gtfs_train_alerts._fetch_gtfs_payload")
    def test_fetch_gtfs_trip_updates_marks_delays(self, mock_fetch_payload):
        feed = self._new_feed()
        entity = feed.entity.add()
        entity.id = "trip-1"
        trip_update = entity.trip_update
        trip_update.trip.route_id = "EWL"
        stop_update = trip_update.stop_time_update.add()
        stop_update.arrival.delay = 240
        mock_fetch_payload.return_value = feed.SerializeToString()

        result = fetch_gtfs_train_trip_updates()

        self.assertIn("EWL", result)
        self.assertEqual(result["EWL"]["status"], 2)
        self.assertEqual(result["EWL"]["status_text"], "Delay")

    @patch("utils.transport.gtfs_train_alerts._fetch_gtfs_payload", return_value=b"not-protobuf")
    def test_fetch_gtfs_service_alerts_handles_decode_errors(self, _mock_payload):
        result = fetch_gtfs_train_service_alerts()
        self.assertEqual(result, {})

    def test_merge_gtfs_with_legacy_status_prioritizes_gtfs(self):
        legacy_map = {"NSL": {"status": 1, "status_text": "Normal"}}
        service_map = {"NSL": {"status": 2, "status_text": "Service disruption"}}
        trip_map = {"EWL": {"status": 2, "status_text": "Delay"}}

        merged = merge_gtfs_with_legacy_status(legacy_map, service_map, trip_map)

        self.assertEqual(merged["NSL"]["status_text"], "Service disruption")
        self.assertEqual(merged["EWL"]["status_text"], "Delay")
