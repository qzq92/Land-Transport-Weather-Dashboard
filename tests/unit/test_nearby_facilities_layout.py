"""Tests for Nearby Facilities grouped sidebar, compact rows, and markers."""

import dash_leaflet as dl

from callbacks.transport_callback import (
    _build_facility_list_column,
    _build_facility_markers,
)
from components.nearby_list_items import (
    NEARBY_EMPTY_COPY,
    nearby_compact_row,
    nearby_empty_message,
)
from components.nearby_transport_page import nearby_transport_page


NEARBY_COLUMN_IDS = [
    "nearby-transport-bus-stop-column",
    "nearby-transport-mrt-column",
    "nearby-transport-taxi-stand-column",
    "nearby-transport-carpark-column",
    "nearby-transport-bicycle-column",
    "nearby-transport-ev-charging-column",
    "nearby-transport-parks-column",
    "nearby-transport-sports-fields-column",
    "nearby-transport-recycling-bins-column",
    "nearby-transport-hawker-centres-column",
]

NEARBY_LAYER_AND_STORE_IDS = [
    "nearby-transport-search-marker",
    "nearby-bus-stop-markers",
    "nearby-mrt-markers",
    "nearby-taxi-stand-markers",
    "nearby-carpark-markers",
    "nearby-bicycle-markers",
    "nearby-ev-charging-markers",
    "nearby-parks-markers",
    "nearby-sports-fields-markers",
    "nearby-recycling-bins-markers",
    "nearby-hawker-centres-markers",
    "nearby-transport-location-store",
    "nearby-parks-toggle-state",
    "nearby-sports-fields-toggle-state",
    "nearby-recycling-bins-toggle-state",
    "nearby-hawker-centres-toggle-state",
    "nearby-transport-interval",
    "nearby-transport-map",
]

TAB_VALUES = [
    "nearby-getting-around",
    "nearby-park-and-charge",
    "nearby-amenities",
]


def find_by_id(component, component_id):
    """Find a Dash component by ID within a component tree."""
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


def flatten_text(component):
    """Collect visible string children from a Dash component tree."""
    if isinstance(component, str):
        return [component]
    if isinstance(component, (list, tuple)):
        texts = []
        for child in component:
            texts.extend(flatten_text(child))
        return texts
    if isinstance(component, (int, float)) or component is None:
        return []
    children = getattr(component, "children", None)
    if children is None:
        return []
    return flatten_text(children)


def test_nearby_page_exposes_grouped_tabs_and_column_ids():
    page = nearby_transport_page()
    tabs = find_by_id(page, "nearby-facilities-tabs")

    assert tabs is not None
    assert tabs.value == "nearby-getting-around"
    assert [tab.value for tab in tabs.children] == TAB_VALUES
    for column_id in NEARBY_COLUMN_IDS:
        assert find_by_id(page, column_id) is not None
    for component_id in NEARBY_LAYER_AND_STORE_IDS:
        assert find_by_id(page, component_id) is not None


def test_search_lives_in_sidebar_and_amenity_toggles_are_not_on_the_map():
    page = nearby_transport_page()
    info = find_by_id(page, "nearby-transport-info-panel")
    map_panel = find_by_id(page, "nearby-transport-map-panel")
    amenities_tab = next(
        tab
        for tab in find_by_id(page, "nearby-facilities-tabs").children
        if tab.value == "nearby-amenities"
    )

    assert find_by_id(info, "nearby-transport-search-query") is not None
    assert find_by_id(map_panel, "nearby-transport-search-query") is None
    assert find_by_id(map_panel, "nearby-transport-overlay-controls") is None
    assert find_by_id(amenities_tab, "nearby-parks-toggle-btn") is not None
    assert find_by_id(amenities_tab, "nearby-hawker-centres-toggle-btn") is not None


def test_sidebar_is_wider_and_content_uses_full_height():
    page = nearby_transport_page()
    content = find_by_id(page, "nearby-transport-content")
    info = find_by_id(page, "nearby-transport-info-panel")

    assert content.style["height"] == "100%"
    assert info.style["flex"] == "0 0 30rem"
    assert info.style["minWidth"] == "26rem"


def test_empty_columns_use_shared_search_copy():
    page = nearby_transport_page()
    bus_column = find_by_id(page, "nearby-transport-bus-stop-column")

    assert NEARBY_EMPTY_COPY in flatten_text(bus_column)
    assert "Select a location" not in " ".join(flatten_text(bus_column))


def test_compact_row_shows_name_and_distance_only():
    row = nearby_compact_row("Bedok Park", "240m")
    text = " ".join(flatten_text(row))

    assert "Bedok Park" in text
    assert "240m" in text
    assert "Distance:" not in text
    assert nearby_empty_message().children == NEARBY_EMPTY_COPY


def test_facility_list_omits_address_and_markers_keep_it_in_popup():
    points = [
        {
            "name": "Bedok Park",
            "lat": 1.3366,
            "lon": 103.9257,
            "address": "718 BEDOK RESERVOIR ROAD",
        }
    ]

    column = _build_facility_list_column(
        "Nearby Parks (Top 5)",
        points,
        (1.3366, 103.9257),
        None,
    )
    column_text = " ".join(flatten_text(column))
    assert "Bedok Park" in column_text
    assert "718 BEDOK RESERVOIR ROAD" not in column_text

    low_zoom = _build_facility_markers(points, "#22c55e", zoom=11)
    assert low_zoom == []

    markers = _build_facility_markers(points, "#22c55e", zoom=15)
    assert len(markers) == 1
    assert isinstance(markers[0], dl.DivMarker)
    popup_text = " ".join(flatten_text(markers[0]))
    assert "718 BEDOK RESERVOIR ROAD" in popup_text
