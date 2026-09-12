"""Tests for bus arrival board presentation helpers."""

from datetime import datetime, timedelta

from dash import no_update

from callbacks.bus_arrival_callback import (
    format_arrival_time_minutes,
    format_bus_arrival_display,
    load_label,
    next_bus_wait_seconds,
    opposite_search_input_updates,
    service_number_sort_key,
    wait_urgency,
)


def component_text(component):
    if component is None:
        return ""
    if isinstance(component, (str, int, float)):
        return str(component)
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        return " ".join(component_text(child) for child in children)
    return component_text(children)


def _arrival(minutes):
    return (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S")


SAMPLE_PAYLOAD = {
    "Services": [
        {
            "ServiceNo": "24",
            "Operator": "SBST",
            "NextBus": {
                "EstimatedArrival": _arrival(12),
                "DestinationCode": "64009",
                "Load": "SEA",
                "Feature": "WAB",
                "Type": "SD",
            },
            "NextBus2": {"EstimatedArrival": _arrival(24)},
            "NextBus3": {},
        },
        {
            "ServiceNo": "12",
            "Operator": "GAS",
            "NextBus": {
                "EstimatedArrival": _arrival(1),
                "DestinationCode": "10499",
                "Load": "LSD",
                "Feature": "WAB",
                "Type": "DD",
            },
        },
    ]
}

STOP_MAP = {
    "83139": "Opp Parkway Parade",
    "64009": "Tampines Int",
    "10499": "Kg Bahru Ter",
}


def test_wait_labels_and_urgency():
    assert format_arrival_time_minutes("") == "N/A"
    assert wait_urgency("Arriving") == "soon"
    assert wait_urgency("5 min") == "mid"
    assert wait_urgency("12 min") == "later"
    assert wait_urgency("Departed") == "gone"
    assert load_label("SEA") == "Seats"
    assert load_label("LSD") == "Crowded"


def test_service_sort_and_soonest_wait():
    assert service_number_sort_key("12A")[0] == 12
    soon = {"NextBus": {"EstimatedArrival": _arrival(2)}}
    later = {"NextBus": {"EstimatedArrival": _arrival(20)}}
    assert next_bus_wait_seconds(soon) < next_bus_wait_seconds(later)


def test_bus_stop_search_clears_service_search_input():
    stop_value, service_value = opposite_search_input_updates(
        "bus-stop-search-btn.n_clicks",
        "83139",
    )

    assert stop_value == "83139"
    assert service_value == ""


def test_bus_service_search_clears_stop_search_input():
    stop_value, service_value = opposite_search_input_updates(
        "bus-service-search-input.n_submit",
    )

    assert stop_value == ""
    assert service_value is no_update


def test_non_search_refresh_preserves_both_search_inputs():
    stop_value, service_value = opposite_search_input_updates(
        "bus-arrival-interval.n_intervals",
    )

    assert stop_value is no_update
    assert service_value is no_update


def test_arrival_board_uses_stop_name_and_destination():
    board = format_bus_arrival_display(
        SAMPLE_PAYLOAD,
        "83139",
        stop_map=STOP_MAP,
        sort_mode="soonest",
    )
    text = component_text(board)

    assert "Stop arrivals" in text
    assert "Opp Parkway Parade (83139)" in text
    assert "Towards Kg Bahru Ter" in text
    assert "Crowded" in text
    assert "Wheelchair" in text
    assert "Double deck" in text
    assert "SBST" not in text
    first_service = board.children[1].children[0]
    assert first_service.children[0].children == "12"


def test_arrival_board_can_sort_by_service_number():
    board = format_bus_arrival_display(
        SAMPLE_PAYLOAD,
        "83139",
        stop_map=STOP_MAP,
        sort_mode="service",
    )
    first_service = board.children[1].children[0]
    assert first_service.children[0].children == "12"
    second_service = board.children[1].children[1]
    assert second_service.children[0].children == "24"
