"""Dash Leaflet marker builders for transport data."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from dash import html
import dash_leaflet as dl

from utils.transport.cache import load_lta_camera_id_mapping
from conf.api_urls import LEAFLET_MARKER_ICON_GREEN_URL, LEAFLET_MARKER_SHADOW_URL


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


def create_cctv_markers(camera_data: Dict[str, Dict[str, Any]]) -> List[dl.Marker]:
    """Create CCTV camera markers with image popups."""
    markers = []
    camera_id_mapping = load_lta_camera_id_mapping()
    icon_url = LEAFLET_MARKER_ICON_GREEN_URL

    for camera_id, info in camera_data.items():
        lat = info.get("lat")
        lon = info.get("lon")
        if lat is None or lon is None:
            continue

        image_url = info.get("image_url", "")
        timestamp = info.get("timestamp", "")
        location_desc = camera_id_mapping.get(str(camera_id), f"Camera {camera_id}")
        datetime_text = ""
        if timestamp:
            try:
                parsed_datetime = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                datetime_text = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError):
                datetime_text = str(timestamp)

        popup_children = [html.Strong(location_desc, style={"fontSize": "0.875rem"})]
        if datetime_text:
            popup_children.append(
                html.Div(
                    f"Time: {datetime_text}",
                    style={"fontSize": "0.75rem", "color": "#888", "marginTop": "0.25rem"},
                )
            )
        popup_children.append(
            html.Img(
                src=image_url,
                style={
                    "width": "17.5rem",
                    "height": "auto",
                    "marginTop": "0.5rem",
                    "borderRadius": "0.25rem",
                },
            )
        )

        tooltip_text = "\n".join([location_desc] + ([f"Time: {datetime_text}"] if datetime_text else []))
        markers.append(
            dl.Marker(
                position=[lat, lon],
                children=[
                    dl.Tooltip(tooltip_text),
                    dl.Popup(html.Div(popup_children, style={"textAlign": "center"}), maxWidth=320),
                ],
                icon={
                    "iconUrl": icon_url,
                    "shadowUrl": LEAFLET_MARKER_SHADOW_URL,
                    "iconSize": [25, 41],
                    "iconAnchor": [12, 41],
                    "popupAnchor": [1, -34],
                    "shadowSize": [41, 41],
                },
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
) -> List[dl.CircleMarker]:
    """Create map markers for traffic incidents and faulty traffic lights."""
    markers: List[dl.CircleMarker] = []

    incidents = incidents_data.get("value", []) if isinstance(incidents_data, dict) else (incidents_data or [])
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
                children=[dl.Tooltip(f"🚦 {message}")],
            )
        )

    faulty_lights = faulty_lights_data.get("value", []) if isinstance(faulty_lights_data, dict) else (faulty_lights_data or [])
    for light in faulty_lights:
        if not isinstance(light, dict):
            continue
        try:
            lat = float(light.get("Latitude") or light.get("latitude") or 0)
            lon = float(light.get("Longitude") or light.get("longitude") or 0)
            if lat == 0 or lon == 0:
                continue
        except (TypeError, ValueError):
            continue

        message = light.get("Message") or light.get("message") or "Faulty traffic light"
        markers.append(
            dl.CircleMarker(
                center=[lat, lon],
                radius=7,
                color="#FCD34D",
                fill=True,
                fillColor="#FCD34D",
                fillOpacity=0.9,
                weight=2,
                children=[dl.Tooltip(f"🚥 {message}")],
            )
        )
    return markers
