"""Tests for the compact Daily Health air-quality legend and PSI colouring."""

from callbacks.weather_indices_callback import (
    format_psi_display,
    get_pollutant_category,
    get_psi_category,
)
from components.air_quality_legend import build_air_quality_legend_column
from components.weather_indices_page import weather_indices_page
from conf.weather_indices_config import (
    AIR_QUALITY_BANDS,
    AIR_QUALITY_BAND_COLORS,
    AIR_QUALITY_BAND_LABELS,
    POLLUTANT_CATEGORY_MAP,
    POLLUTANT_THRESHOLD_ROWS,
    POLLUTANT_UNITS,
    PSI_MAP_COLUMNS,
    PSI_TABLE_COLUMNS,
    UNKNOWN_CATEGORY,
)


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


def component_text(component):
    """Flatten visible text from a Dash component tree."""
    texts = []

    def walk(node):
        if node is None or isinstance(node, (int, float)):
            return
        if isinstance(node, str):
            texts.append(node)
            return
        children = getattr(node, "children", None)
        if isinstance(children, (list, tuple)):
            for child in children:
                walk(child)
        else:
            walk(children)

    walk(component)
    return " ".join(texts)


def collect_div_styles(component):
    """Collect (children, style) pairs for html.Div nodes."""
    pairs = []

    def walk(node):
        if node is None or isinstance(node, (str, int, float)):
            return
        if getattr(node, "style", None) is not None and getattr(node, "children", None) is not None:
            pairs.append((node.children, node.style))
        children = getattr(node, "children", None)
        if isinstance(children, (list, tuple)):
            for child in children:
                walk(child)
        else:
            walk(children)

    walk(component)
    return pairs


def _psi_payload():
    regions = ["north", "south", "east", "west", "central"]
    return {
        "code": 0,
        "data": {
            "items": [
                {
                    "updatedTimestamp": "2026-09-12T12:00:00+08:00",
                    "readings": {
                        "psi_twenty_four_hourly": {region: 40 for region in regions},
                        "pm25_twenty_four_hourly": {region: 20 for region in regions},
                        "pm10_twenty_four_hourly": {region: 120 for region in regions},
                        "so2_twenty_four_hourly": {region: 10 for region in regions},
                        "co_eight_hour_max": {region: 1 for region in regions},
                        "o3_eight_hour_max": {region: 250 for region in regions},
                        "no2_one_hour_max": {region: 2500 for region in regions},
                    },
                }
            ]
        },
    }


def test_config_derives_legend_bands_from_psi_categories():
    assert [band[0] for band in AIR_QUALITY_BANDS] == list(AIR_QUALITY_BAND_LABELS)
    assert [band[2] for band in AIR_QUALITY_BANDS] == list(AIR_QUALITY_BAND_COLORS)
    assert AIR_QUALITY_BANDS[0][1] == "0-50"
    assert AIR_QUALITY_BANDS[-1][1] == "301+"
    assert POLLUTANT_THRESHOLD_ROWS[0][0] == "PM2.5"
    assert POLLUTANT_THRESHOLD_ROWS[0][1] == POLLUTANT_UNITS["pm25_twenty_four_hourly"]
    assert POLLUTANT_THRESHOLD_ROWS[0][2][-1] == "150+"
    map_keys = [key for key, _label in PSI_MAP_COLUMNS]
    table_keys = [key for key, _label in PSI_TABLE_COLUMNS]
    assert map_keys == table_keys
    assert set(map_keys) == set(POLLUTANT_CATEGORY_MAP)


def test_psi_and_pollutant_categories_use_the_same_five_bands():
    good = (AIR_QUALITY_BAND_COLORS[0], AIR_QUALITY_BAND_LABELS[0])
    moderate = (AIR_QUALITY_BAND_COLORS[1], AIR_QUALITY_BAND_LABELS[1])
    unhealthy = (AIR_QUALITY_BAND_COLORS[2], AIR_QUALITY_BAND_LABELS[2])
    very_unhealthy = (AIR_QUALITY_BAND_COLORS[3], AIR_QUALITY_BAND_LABELS[3])
    hazardous = (AIR_QUALITY_BAND_COLORS[4], AIR_QUALITY_BAND_LABELS[4])

    assert get_psi_category(40) == good
    assert get_psi_category(75) == moderate
    assert get_pollutant_category("psi_twenty_four_hourly", 40) == get_psi_category(40)
    assert get_pollutant_category("pm25_twenty_four_hourly", 10) == good
    assert get_pollutant_category("pm25_twenty_four_hourly", 20) == moderate
    assert get_pollutant_category("pm10_twenty_four_hourly", 120) == unhealthy
    assert get_pollutant_category("o3_eight_hour_max", 250) == very_unhealthy
    assert get_pollutant_category("no2_one_hour_max", 2500) == hazardous
    assert get_pollutant_category("unknown_key", 10) == UNKNOWN_CATEGORY
    assert get_pollutant_category("pm25_twenty_four_hourly", None) == UNKNOWN_CATEGORY
    assert get_psi_category("not-a-number") == UNKNOWN_CATEGORY


def test_legend_column_keeps_callback_ids_and_hides_specialist_table():
    column = build_air_quality_legend_column()
    scale = find_by_id(column, "psi-color-categories")
    guide = find_by_id(column, "pollutant-legend")
    table_container = find_by_id(column, "psi-metrics-table-container")
    table_content = find_by_id(column, "psi-metrics-table-content")

    assert scale is not None
    assert guide is not None
    assert table_container is not None
    assert table_content is not None
    assert table_container.style["display"] == "none"
    assert guide.open is False
    assert find_by_id(guide, "psi-metrics-table-container") is None
    assert "Air quality (PSI)" in component_text(scale)
    assert "How are these colours decided?" in component_text(guide)
    for name, _unit, _ranges in POLLUTANT_THRESHOLD_ROWS:
        assert name in component_text(guide)


def test_weather_indices_page_exposes_legend_and_toggle_ids():
    page = weather_indices_page()
    assert find_by_id(page, "psi-color-categories") is not None
    assert find_by_id(page, "pollutant-legend") is not None
    assert find_by_id(page, "psi-metrics-table-container") is not None
    assert find_by_id(page, "toggle-psi-display-mode") is not None
    map_panel = find_by_id(page, "weather-indices-map-panel")
    assert map_panel.style["flex"] == "3"


def test_psi_table_colours_each_reading_by_category():
    table = format_psi_display(_psi_payload())
    styles_by_text = {
        children: style.get("color")
        for children, style in collect_div_styles(table)
        if isinstance(children, str)
    }

    assert styles_by_text["40"] == AIR_QUALITY_BAND_COLORS[0]
    assert styles_by_text["20 µg/m³"] == AIR_QUALITY_BAND_COLORS[1]
    assert styles_by_text["120 µg/m³"] == AIR_QUALITY_BAND_COLORS[2]
    assert styles_by_text["10 µg/m³"] == AIR_QUALITY_BAND_COLORS[0]
    assert styles_by_text["1 mg/m³"] == AIR_QUALITY_BAND_COLORS[0]
    assert styles_by_text["250 µg/m³"] == AIR_QUALITY_BAND_COLORS[3]
    assert styles_by_text["2500 µg/m³"] == AIR_QUALITY_BAND_COLORS[4]
