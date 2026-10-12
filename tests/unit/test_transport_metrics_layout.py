"""Tests for Road & Transport Metrics & Map two-column layout."""

from components.transport_metrics_view import LAYER_CHIP_LABELS, transport_metrics_view
from components.transport_page import transport_page


REQUIRED_IDS = [
    "transport-content",
    "transport-info-panel",
    "transport-map-panel",
    "train-advisory-panel",
    "train-service-alerts-content",
    "taxi-availability-card",
    "taxi-count-value",
    "cctv-count-value",
    "speed-camera-count-value",
    "erp-count-value",
    "vms-count-value",
    "ev-charging-points-count-value",
    "traffic-incidents-count-value",
    "traffic-incidents-messages",
    "traffic-alert-filter",
    "traffic-alerts-freshness",
    "bus-stops-count-value",
    "bus-stops-disclaimer",
    "bus-services-count-value",
    "taxi-toggle-btn",
    "cctv-toggle-btn",
    "erp-toggle-btn",
    "traffic-incidents-toggle-btn",
    "vms-toggle-btn",
    "speed-camera-toggle-btn",
    "ev-charging-toggle-btn",
    "transport-bus-stops-toggle-btn",
    "transport-map",
    "taxi-markers",
    "taxi-toggle-state",
    "transport-interval",
]


def find_by_id(component, component_id):
    if getattr(component, "id", None) == component_id:
        return component
    children = getattr(component, "children", None)
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if child is None or isinstance(child, (str, int, float)):
            continue
        match = find_by_id(child, component_id)
        if match is not None:
            return match
    return None


def collect_ids(component):
    ids = []
    component_id = getattr(component, "id", None)
    if component_id:
        ids.append(component_id)
    children = getattr(component, "children", None)
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if child is None or isinstance(child, (str, int, float)):
            continue
        ids.extend(collect_ids(child))
    return ids


def test_content_is_two_columns_with_advisory_in_the_rail():
    view = transport_metrics_view()
    content = find_by_id(view, "transport-content")
    info = find_by_id(view, "transport-info-panel")
    map_panel = find_by_id(view, "transport-map-panel")
    advisory = find_by_id(info, "train-advisory-panel")

    assert content.className == "transport-metrics-content"
    assert info.className == "transport-metrics-rail"
    assert map_panel.className == "transport-map-panel"
    assert advisory is not None
    assert find_by_id(map_panel, "train-advisory-panel") is None
    assert len(content.children) == 2


def test_layer_chips_use_short_labels():
    view = transport_metrics_view()
    taxi = find_by_id(view, "taxi-toggle-btn")
    cameras = find_by_id(view, "cctv-toggle-btn")
    bus = find_by_id(view, "transport-bus-stops-toggle-btn")

    assert taxi.children == LAYER_CHIP_LABELS["taxi"]
    assert cameras.children == LAYER_CHIP_LABELS["cctv"]
    assert bus.children == LAYER_CHIP_LABELS["bus"]
    assert taxi.title == "Show Current Taxi Availability/Stands"


def test_page_keeps_metric_map_and_store_ids():
    page = transport_page()
    present = set(collect_ids(page))

    for component_id in REQUIRED_IDS:
        assert component_id in present
    assert find_by_id(page, "transport-travel-times-view") is not None
    assert find_by_id(page, "transport-cameras-view") is not None
