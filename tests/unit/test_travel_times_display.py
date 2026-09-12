"""Tests for grouped expressway travel-time timelines."""

from pathlib import Path

from callbacks.travel_times_callback import format_travel_times_table
from components.travel_times_board import (
    _direction_row,
    build_travel_times_board,
    format_expressway_exit_label,
    format_route_destination_label,
    group_summaries_by_expressway,
)
from components.travel_times_page import travel_times_view


def flatten_text(component):
    if component is None:
        return ""
    if isinstance(component, (str, int, float)):
        return str(component)
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        return " ".join(flatten_text(child) for child in children)
    return flatten_text(children)


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


def find_by_class(component, class_name):
    classes = getattr(component, "className", "") or ""
    if class_name in classes.split():
        return component
    children = getattr(component, "children", None)
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if child is None or isinstance(child, (str, int, float)):
            continue
        match = find_by_class(child, class_name)
        if match is not None:
            return match
    return None


def collect_classes(component):
    classes = []
    class_name = getattr(component, "className", None)
    if class_name:
        classes.extend(class_name.split())
    children = getattr(component, "children", None)
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if child is None or isinstance(child, (str, int, float)):
            continue
        classes.extend(collect_classes(child))
    return classes


ECP_EAST = {
    "expressway": "ECP",
    "direction": "2",
    "direction_text": "East",
    "origin": "ROCHOR RD",
    "destination": "MAXWELL RD",
    "total_time": 12,
    "level": "slow",
    "chains": [
        [
            {
                "StartPoint": "ROCHOR RD",
                "EndPoint": "MAXWELL RD",
                "EstTime": "12",
            }
        ]
    ],
    "segment_count": 1,
}

AYE_WEST = {
    "expressway": "AYE",
    "direction": "1",
    "direction_text": "West",
    "origin": "TUAS CHECKPOINT",
    "destination": "AYE/MCE",
    "total_time": 3,
    "level": "clear",
    "chains": [
        [
            {
                "StartPoint": "TUAS CHECKPOINT",
                "EndPoint": "TELOK BLANGAH",
                "EstTime": "2",
            },
            {
                "StartPoint": "TELOK BLANGAH",
                "EndPoint": "AYE/MCE",
                "EstTime": "1",
            },
        ]
    ],
    "segment_count": 2,
}

AYE_EAST = {
    "expressway": "AYE",
    "direction": "2",
    "direction_text": "East",
    "origin": "AYE/MCE",
    "destination": "TUAS CHECKPOINT",
    "total_time": 4,
    "level": "clear",
    "chains": [
        [
            {
                "StartPoint": "AYE/MCE",
                "EndPoint": "TUAS CHECKPOINT",
                "EstTime": "4",
            }
        ]
    ],
    "segment_count": 1,
}


def test_exit_label_uses_code_and_bracketed_exit():
    assert format_expressway_exit_label("ECP", "ROCHOR RD") == "ECP (ROCHOR RD)"
    assert format_expressway_exit_label("  pie ", None) == "pie (N/A)"


def test_destination_label_is_separate_from_origin():
    assert format_route_destination_label("MAXWELL RD", "East") == (
        "to MAXWELL RD · (East)"
    )
    assert format_route_destination_label("MAXWELL RD", "") == "to MAXWELL RD"


def test_direction_row_shows_origin_hops_without_accordion():
    row = _direction_row(ECP_EAST)
    text = flatten_text(row)
    classes = collect_classes(row)

    assert "ECP (ROCHOR RD)" in text
    assert "12 min" in text
    assert "MAXWELL RD" in text
    assert "East Coast" not in text
    assert "travel-times-route" not in classes
    assert "travel-times-heat" not in classes
    assert row.className == "travel-times-direction"


def test_board_groups_aye_directions_under_one_section():
    board = build_travel_times_board([ECP_EAST, AYE_EAST, AYE_WEST])
    text = flatten_text(board)
    sections = find_by_class(board, "travel-times-sections")
    first_section = sections.children[0]
    first_text = flatten_text(first_section)

    assert first_section.children[0].children[0].children == "AYE"
    assert "Ayer Rajah" in first_text
    assert "West" in first_text
    assert "East" in first_text
    assert "AYE (TUAS CHECKPOINT)" in first_text
    assert "2 min" in first_text
    assert "TELOK BLANGAH" in first_text
    assert text.index("AYE") < text.index("ECP")


def test_group_order_uses_known_expressway_then_direction():
    grouped = group_summaries_by_expressway([ECP_EAST, AYE_EAST, AYE_WEST])

    assert [code for code, _routes in grouped] == ["AYE", "ECP"]
    assert [route["direction_text"] for route in grouped[0][1]] == ["West", "East"]


def test_format_table_shows_visible_hops_for_ecp():
    table = format_travel_times_table(
        {
            "value": [
                {
                    "Name": "ECP",
                    "Direction": "2",
                    "StartPoint": "ROCHOR RD",
                    "EndPoint": "MAXWELL RD",
                    "EstTime": "12",
                }
            ]
        }
    )
    text = flatten_text(table)
    classes = collect_classes(table)

    assert table.className == "travel-times-board"
    assert "ECP (ROCHOR RD)" in text
    assert "12 min" in text
    assert "travel-times-snapshot" not in classes
    assert "travel-times-route" not in classes
    assert "travel-times-heat" not in classes


def test_page_keeps_callback_ids_and_board_classes():
    page = travel_times_view()
    container = find_by_id(page, "travel-times-table-container")

    assert page.className == "travel-times-page"
    assert container.className == "travel-times-table"
    assert find_by_id(page, "travel-times-expressway-filter") is not None
    assert find_by_id(page, "travel-times-interval") is not None


def test_stylesheet_uses_section_timeline_and_dashboard_colours():
    css = (Path(__file__).resolve().parents[2] / "assets" / "travel_times.css").read_text(
        encoding="utf-8"
    )

    assert ".travel-times-section" in css
    assert ".travel-times-timeline" in css
    assert ".travel-times-pill" in css
    assert ".travel-times-route" not in css
    assert ".travel-times-heat" not in css
    assert "background-color: #1a2a3a" in css
    assert "background-color: #2a3a4a" in css
