"""Tests for the combined Transit navigation and refresh behavior."""

from callbacks.tab_navigation_callback import (
    _TAB_KEYS,
    get_transit_sub_tab_state,
)
from components.banner_component import build_dashboard_banner
from components.transit_page import transit_page


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


def test_banner_exposes_one_transit_tab():
    navigation = find_by_id(build_dashboard_banner(), "navigation-tabs")
    values = [tab.value for tab in navigation.children]

    assert "transit" in values
    assert "bus-arrival" not in values
    assert "analytics-forecast" not in values
    assert values.count("transit") == 1


def test_transit_page_defaults_to_station_crowd():
    page = transit_page()
    sub_tabs = find_by_id(page, "transit-sub-tabs")
    crowd_view = find_by_id(page, "transit-crowd-view")
    bus_view = find_by_id(page, "transit-bus-view")

    assert sub_tabs.value == "transit-crowd"
    assert crowd_view.style["display"] == "flex"
    assert bus_view.style["display"] == "none"
    assert find_by_id(page, "bus-arrival-page-interval").disabled is True
    assert find_by_id(page, "bus-arrival-interval").disabled is True


def test_transit_sub_tab_state_pauses_hidden_bus_refreshes():
    crowd_state = get_transit_sub_tab_state("transit-crowd")
    bus_state = get_transit_sub_tab_state("transit-bus")

    assert crowd_state[0]["display"] == "flex"
    assert crowd_state[1]["display"] == "none"
    assert crowd_state[2:] == (True, True)
    assert bus_state[0]["display"] == "none"
    assert bus_state[1]["display"] == "flex"
    assert bus_state[2:] == (False, False)


def test_lazy_navigation_uses_transit_instead_of_legacy_tabs():
    assert "transit" in _TAB_KEYS
    assert "bus-arrival" not in _TAB_KEYS
    assert "analytics-forecast" not in _TAB_KEYS
