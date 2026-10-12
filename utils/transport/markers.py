"""Dash Leaflet marker builders for transport data."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from dash import html
import dash_leaflet as dl

from utils.transport.faulty_lights import (
    locate_faulty_lights,
    normalize_faulty_lights,
)


def create_taxi_markers(data: Optional[Dict[str, Any]]) -> List[dl.CircleMarker]:
    """Create map markers for taxi locations."""
    markers = []
    if not data or "features" not in data:
        return markers
    features = data.get("features", [])
    if not features:
        return markers
    coordinates = features[0].get("geometry", {}).get("coordinates", [])
    for coord in coordinates:
        if len(coord) >= 2:
            lon, lat = coord[0], coord[1]
            markers.append(
                dl.CircleMarker(
                    center=[lat, lon],
                    radius=3,
                    color="#FFD700",
                    fill=True,
                    fillColor="#FFD700",
                    fillOpacity=0.7,
                    weight=1,
                )
            )
    return markers


def create_bus_stops_circle_markers(bus_stops_data: Optional[Dict[str, Any]]) -> List[dl.CircleMarker]:
    """Create lightweight circle markers for bus stops."""
    markers = []
    if not bus_stops_data or "value" not in bus_stops_data:
        return markers
    for bus_stop in bus_stops_data.get("value", []):
        try:
            latitude = float(bus_stop.get("Latitude", 0))
            longitude = float(bus_stop.get("Longitude", 0))
            bus_stop_code = bus_stop.get("BusStopCode", "N/A")
            description = bus_stop.get("Description", "N/A")
            if latitude == 0 or longitude == 0:
                continue
            markers.append(
                dl.CircleMarker(
                    id={"type": "bus-stop-marker", "index": bus_stop_code},
                    center=[latitude, longitude],
                    radius=8,
                    color="#4169E1",
                    fillColor="#4169E1",
                    fillOpacity=0.7,
                    weight=2,
                    children=[dl.Tooltip(f"🚏 {description} ({bus_stop_code}) - Click to view arrivals")],
                )
            )
        except (ValueError, TypeError, KeyError):
            continue
    return markers


def create_traffic_incidents_markers(
    incidents_data: Optional[Dict[str, Any]],
    faulty_lights_data: Optional[Dict[str, Any]] = None,
    normalized_alerts: Optional[List[Dict[str, Any]]] = None,
    alert_filter: str = "all",
) -> List[Any]:
    """Create shared markers for road incidents and signal alerts."""
    markers: List[Any] = []

    incidents = incidents_data.get("value", []) if isinstance(incidents_data, dict) else (incidents_data or [])
    if alert_filter in ("all", "incidents"):
        for incident in incidents:
            if not isinstance(incident, dict):
                continue
            try:
                lat = float(incident.get("Latitude") or incident.get("latitude") or incident.get("Lat") or 0)
                lon = float(incident.get("Longitude") or incident.get("longitude") or incident.get("Lon") or 0)
                if lat == 0 or lon == 0:
                    continue
            except (TypeError, ValueError):
                continue

            message = incident.get("Message") or incident.get("message") or incident.get("Type") or "Traffic incident"
            markers.append(
                dl.CircleMarker(
                    center=[lat, lon],
                    radius=8,
                    color="#F97316",
                    fill=True,
                    fillColor="#F97316",
                    fillOpacity=0.85,
                    weight=2,
                    children=[
                        dl.Tooltip(f"Road incident: {message}"),
                        dl.Popup(
                            html.Div(
                                [
                                    html.Strong("Road incident"),
                                    html.P(str(message)),
                                ]
                            )
                        ),
                    ],
                )
            )

    signal_alerts = normalized_alerts
    if signal_alerts is None:
        signal_alerts = locate_faulty_lights(
            normalize_faulty_lights(faulty_lights_data)
        )
    for alert in signal_alerts:
        status = alert.get("status", "fault")
        if alert_filter in ("fault", "maintenance") and status != alert_filter:
            continue
        if alert_filter == "incidents":
            continue
        lat = alert.get("latitude")
        lon = alert.get("longitude")
        if not lat or not lon:
            continue
        color = "#EF4444" if status == "fault" else "#FCD34D"
        start = alert.get("start")
        end = alert.get("end")
        time_text = (
            start.strftime("%d %b %Y, %H:%M")
            if isinstance(start, datetime)
            else "Unavailable"
        )
        if isinstance(end, datetime):
            time_text = f"{time_text} – {end.strftime('%d %b %Y, %H:%M')}"
        status_label = "Maintenance" if status == "maintenance" else "Fault"
        popup_lines = [
            html.Strong(f"{status_label}: {alert.get('type_label')}"),
            html.P(alert.get("location") or "Location unavailable"),
            html.Small(time_text),
        ]
        if alert.get("node_id"):
            popup_lines.append(html.Small(f"Node {alert['node_id']}"))
        if alert.get("location_is_approximate"):
            popup_lines.append(html.Em("Approximate location from OneMap"))
        markers.append(
            dl.CircleMarker(
                center=[lat, lon],
                radius=8,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.9,
                weight=2,
                children=[
                    dl.Tooltip(
                        f"{status_label}: {alert.get('location')}"
                    ),
                    dl.Popup(html.Div(popup_lines)),
                ],
            )
        )
    return markers
