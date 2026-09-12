"""Shared WBGT data and presentation helpers."""

from datetime import datetime

from dash import html
import dash_leaflet as dl

from conf.api_urls import WBGT_URL
from utils.async_fetcher import _executor, fetch_url_2min_cached, get_default_headers


def fetch_wbgt_data_async():
    """Fetch WBGT data asynchronously using the shared 2-minute cache."""
    return _executor.submit(fetch_url_2min_cached, WBGT_URL, get_default_headers())


def _parse_timestamp(timestamp_str):
    if not timestamp_str:
        return ""
    try:
        parsed = datetime.fromisoformat(str(timestamp_str).replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(timestamp_str)


def _wbgt_color(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "#999"
    if value >= 33:
        return "#ff4d4d"
    if value >= 31:
        return "#ff9800"
    if value >= 28:
        return "#ffd166"
    return "#4ecdc4"


def _create_wbgt_row(station_name, wbgt, heat_stress):
    color = _wbgt_color(wbgt)
    return html.Div(
        [
            html.Div(station_name, style={"color": "#fff", "fontSize": "0.75rem", "flex": "1"}),
            html.Div(
                f"{wbgt}°C",
                style={"color": color, "fontSize": "0.875rem", "fontWeight": "700", "marginLeft": "0.5rem"},
            ),
            html.Div(
                heat_stress,
                style={"color": "#bbb", "fontSize": "0.6875rem", "marginLeft": "0.5rem"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "padding": "0.35rem 0",
            "borderBottom": "0.0625rem solid #3a4a5a",
        },
    )


def format_wbgt_display(data):
    """Format WBGT data for display."""
    if not data:
        return html.P("Error retrieving WBGT data", style={"color": "#ff6b6b", "textAlign": "center"})
    if data.get("code") not in [0, 1]:
        return html.P(
            f"Error retrieving WBGT data (Code: {data.get('code')})",
            style={"color": "#ff6b6b", "textAlign": "center"},
        )

    records = data.get("data", {}).get("records", [])
    if not records:
        return html.P("No WBGT data available", style={"color": "#ccc", "textAlign": "center"})

    record = records[0]
    readings = record.get("item", {}).get("readings", [])
    if not readings:
        return html.P("No WBGT readings available", style={"color": "#ccc", "textAlign": "center"})

    rows = [
        _create_wbgt_row(
            reading.get("station", {}).get("name", "Unknown"),
            reading.get("wbgt", "N/A"),
            reading.get("heatStress", "Unknown"),
        )
        for reading in sorted(readings, key=lambda item: item.get("station", {}).get("name", ""))
    ]

    return html.Div(
        [
            html.Div(rows, style={"display": "flex", "flexDirection": "column", "flex": "1", "overflowY": "auto"}),
            html.Div(
                f"Updated: {_parse_timestamp(record.get('updatedTimestamp', ''))}",
                style={
                    "textAlign": "center",
                    "color": "#888",
                    "fontSize": "0.6875rem",
                    "marginTop": "0.625rem",
                    "fontStyle": "italic",
                },
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "height": "100%", "overflow": "hidden"},
    )


def _create_single_wbgt_marker(reading):
    station = reading.get("station", {})
    location = station.get("location", {})
    try:
        lat = float(location.get("latitude"))
        lon = float(location.get("longitude"))
    except (TypeError, ValueError):
        return None

    wbgt = reading.get("wbgt", "N/A")
    heat_stress = reading.get("heatStress", "Unknown")
    color = _wbgt_color(wbgt)
    return dl.CircleMarker(
        center=[lat, lon],
        radius=8,
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.8,
        weight=2,
        children=[dl.Tooltip(f"{station.get('name', 'Unknown')}: {wbgt}°C ({heat_stress})")],
    )


def create_wbgt_markers(data):
    """Create map markers for WBGT stations."""
    if not data or data.get("code") != 0:
        return []
    records = data.get("data", {}).get("records", [])
    if not records:
        return []
    readings = records[0].get("item", {}).get("readings", [])
    markers = [_create_single_wbgt_marker(reading) for reading in readings]
    return [marker for marker in markers if marker is not None]
