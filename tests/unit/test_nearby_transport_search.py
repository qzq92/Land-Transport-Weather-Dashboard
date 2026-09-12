"""Tests for Nearby Facilities Enter-to-search location lookup."""

from callbacks.map_callback import (
    format_onemap_dropdown_options,
    nearby_search_dropdown_update,
)
from components.nearby_transport_page import nearby_transport_page


SAMPLE_RESULTS = [
    {
        "ADDRESS": "1 RAFFLES PLACE SINGAPORE 048616",
        "BUILDING": "ONE RAFFLES PLACE",
        "POSTAL": "048616",
        "LATITUDE": "1.284",
        "LONGITUDE": "103.851",
    },
    {
        "ADDRESS": "6 RAFFLES BOULEVARD SINGAPORE 039594",
        "BUILDING": "MARINA SQUARE",
        "POSTAL": "039594",
        "LATITUDE": "1.291",
        "LONGITUDE": "103.857",
    },
]


def test_format_onemap_dropdown_options_uses_address_and_coordinates():
    options = format_onemap_dropdown_options(SAMPLE_RESULTS, include_postal=False)

    assert len(options) == 2
    assert options[0]["label"].startswith("ONE RAFFLES PLACE")
    assert options[0]["value"].startswith("1.284,103.851,")
    assert "048616" not in options[0]["value"].split(",")[:2]


def test_short_or_empty_query_does_not_search(monkeypatch):
    def fail_if_called(_query):
        raise AssertionError("OneMap should not be called until the query is complete")

    monkeypatch.setattr(
        "callbacks.map_callback.search_location_via_onemap_info_async",
        fail_if_called,
    )

    assert nearby_search_dropdown_update("") == ([], None)
    assert nearby_search_dropdown_update("ab") == ([], None)


def test_single_match_is_selected_after_submit(monkeypatch):
    class ImmediateFuture:
        def result(self):
            return SAMPLE_RESULTS[:1]

    monkeypatch.setattr(
        "callbacks.map_callback.search_location_via_onemap_info_async",
        lambda _query: ImmediateFuture(),
    )

    options, selected = nearby_search_dropdown_update("raffles place")

    assert len(options) == 1
    assert selected == options[0]["value"]


def test_multiple_matches_wait_for_user_selection(monkeypatch):
    class ImmediateFuture:
        def result(self):
            return SAMPLE_RESULTS

    monkeypatch.setattr(
        "callbacks.map_callback.search_location_via_onemap_info_async",
        lambda _query: ImmediateFuture(),
    )

    options, selected = nearby_search_dropdown_update("raffles")

    assert len(options) == 2
    assert selected is None


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


def test_nearby_page_uses_enter_to_search_controls():
    page = nearby_transport_page()
    info = find_by_id(page, "nearby-transport-info-panel")
    query = find_by_id(info, "nearby-transport-search-query")
    button = find_by_id(info, "nearby-transport-search-btn")
    results = find_by_id(info, "nearby-transport-search")

    wrap = find_by_id(info, "nearby-transport-search-matches-wrap")

    assert query is not None
    assert button is not None
    assert wrap is not None
    assert wrap.className == "nearby-search-matches-wrap"
    assert results.className == "nearby-search-matches"
    assert "press Enter" in query.placeholder


def test_nearby_match_list_wraps_full_suggestion_text():
    page = nearby_transport_page()
    results = find_by_id(page, "nearby-transport-search")

    assert results.className == "nearby-search-matches"
    assert getattr(results, "optionHeight", None) is None
