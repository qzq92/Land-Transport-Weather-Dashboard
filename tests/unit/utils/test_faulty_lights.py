"""Tests for faulty traffic-light normalization and location lookup."""

from datetime import datetime
from unittest.mock import Mock

from utils.transport.faulty_lights import (
    extract_location,
    geocode_location,
    locate_faulty_lights,
    normalize_faulty_lights,
    parse_lta_datetime,
    summarize_faulty_lights,
)


def _record(**overrides):
    record = {
        "AlarmID": "GL703034136",
        "NodeID": "703034136",
        "Type": "13",
        "StartDate": "2026-10-12 01:58:00.0",
        "EndDate": "",
        "Message": (
            "(12/10)1:58 Flashing Yellow at Bedok North Interchange/"
            "Bedok North Street 1 Junc."
        ),
    }
    record.update(overrides)
    return record


def test_parse_lta_datetime_accepts_documented_format():
    assert parse_lta_datetime("2026-10-12 01:58:00.0") == datetime(
        2026,
        10,
        12,
        1,
        58,
    )
    assert parse_lta_datetime("") is None
    assert parse_lta_datetime("not-a-date") is None


def test_extract_location_uses_junction_phrase():
    assert extract_location(_record()["Message"]) == (
        "Bedok North Interchange/Bedok North Street 1"
    )
    assert extract_location("") == "Location unavailable"


def test_normalize_classifies_fault_and_maintenance_and_deduplicates():
    payload = {
        "value": [
            _record(),
            _record(),
            _record(
                AlarmID="GL2",
                NodeID="2",
                Type="4",
                EndDate="2026-10-12 05:00:00.0",
            ),
            _record(AlarmID="GL3", NodeID="3", Type="99"),
        ]
    }

    alerts = normalize_faulty_lights(payload)

    assert len(alerts) == 3
    by_id = {alert["alarm_id"]: alert for alert in alerts}
    assert by_id["GL703034136"]["status"] == "fault"
    assert by_id["GL703034136"]["type_label"] == "Flashing yellow"
    assert by_id["GL2"]["status"] == "maintenance"
    assert by_id["GL2"]["type_label"] == "Blackout"
    assert by_id["GL3"]["type_label"] == "Alarm type 99"


def test_normalize_handles_empty_and_malformed_payloads():
    assert normalize_faulty_lights(None) == []
    assert normalize_faulty_lights({"value": "invalid"}) == []
    assert normalize_faulty_lights([None, "invalid"]) == []


def test_summary_counts_unique_nodes_by_status():
    alerts = normalize_faulty_lights(
        {
            "value": [
                _record(),
                _record(AlarmID="GL2"),
                _record(AlarmID="GL3", NodeID="2", EndDate="2026-10-13 01:00:00"),
            ]
        }
    )

    assert summarize_faulty_lights(alerts) == {
        "faults": 1,
        "maintenance": 1,
        "total": 2,
    }


def test_geocode_location_returns_singapore_result_and_caches(monkeypatch):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "results": [
            {
                "LATITUDE": "1.325",
                "LONGITUDE": "103.931",
                "ADDRESS": "BEDOK NORTH STREET 1",
            }
        ]
    }
    get = Mock(return_value=response)
    monkeypatch.setattr("utils.transport.faulty_lights.requests.get", get)
    geocode_location.cache_clear()

    first = geocode_location("Bedok North Interchange/Bedok North Street 1")
    second = geocode_location("Bedok North Interchange/Bedok North Street 1")

    assert first == (1.325, 103.931, "BEDOK NORTH STREET 1")
    assert second == first
    assert get.call_count == 1
    assert "and" in get.call_args.args[0]


def test_locate_preserves_unresolved_records(monkeypatch):
    alerts = normalize_faulty_lights({"value": [_record()]})
    monkeypatch.setattr(
        "utils.transport.faulty_lights.geocode_location",
        lambda _location: None,
    )

    located = locate_faulty_lights(alerts)

    assert len(located) == 1
    assert located[0]["latitude"] is None
    assert located[0]["location"] == (
        "Bedok North Interchange/Bedok North Street 1"
    )
