"""
Callback functions for handling transport information.
References:
- Taxi: https://api.data.gov.sg/v1/transport/taxi-availability
- Traffic Cameras: https://api.data.gov.sg/v1/transport/traffic-images
- ERP Gantries: https://data.gov.sg/datasets/d_753090823cc9920ac41efaa6530c5893/view
- PUB CCTV: https://data.gov.sg/datasets/d_1de1c45043183bec57e762d01c636eee/view
"""
import re
import os
import math
import base64
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from concurrent.futures import Future
from dash import Input, Output, State, html, dependencies
import dash_leaflet as dl
from utils.async_fetcher import fetch_url, fetch_async, fetch_url_2min_cached
from utils.data_download_helper import fetch_erp_gantry_data
from utils.map_utils import SG_MAP_CENTER
from callbacks.map_callback import _haversine_distance_m

# API URLs
TAXI_API_URL = "https://api.data.gov.sg/v1/transport/taxi-availability"
TRAFFIC_IMAGES_API_URL = "https://api.data.gov.sg/v1/transport/traffic-images"
TRAFFIC_INCIDENTS_URL = "https://datamall2.mytransport.sg/ltaodataservice/TrafficIncidents"
FAULTY_TRAFFIC_LIGHTS_URL = "https://datamall2.mytransport.sg/ltaodataservice/FaultyTrafficLights"
BICYCLE_PARKING_URL = "https://datamall2.mytransport.sg/ltaodataservice/BicycleParkingv2"
VMS_URL = "https://datamall2.mytransport.sg/ltaodataservice/VMS"
EV_CHARGING_URL = "https://datamall2.mytransport.sg/ltaodataservice/EVChargingPoints"
BUS_STOPS_URL = "https://datamall2.mytransport.sg/ltaodataservice/BusStops"
BUS_ROUTES_URL = "https://datamall2.mytransport.sg/ltaodataservice/BusRoutes"

# In-memory cache for static road infrastructure data
# These represent physical infrastructure that rarely changes
_road_infra_cache: Dict[str, Optional[Any]] = {
    'bus_stops': None,
    'bus_stops_bucket': None,  # YYYYMM bucket for monthly refresh
    'bus_routes': None,
    'bus_routes_bucket': None,  # YYYYMM bucket for monthly refresh
    'vms': None,
    'taxi_stands': None,
    'bicycle_parking': None,
    'bicycle_parking_bucket': None,  # YYYYMM bucket for monthly refresh
    'speed_camera_df': None,  # DataFrame cache
    'erp_gantries': None,  # Parsed ERP gantry data
}


def clear_road_infra_cache():
    """
    Clear all cached road infrastructure data.
    Useful for forcing a refresh of static data.
    """
    global _road_infra_cache
    _road_infra_cache = {
        'bus_stops': None,
        'bus_stops_bucket': None,
        'bus_routes': None,
        'bus_routes_bucket': None,
        'vms': None,
        'taxi_stands': None,
        'bicycle_parking': None,
        'bicycle_parking_bucket': None,
        'speed_camera_df': None,
        'erp_gantries': None,
    }
    print("Road infrastructure cache cleared")


def get_erp_gantry_data():
    """
    Get ERP gantry data (parsed).
    Uses in-memory cache since ERP gantries are static infrastructure.
    
    Returns:
        List of dictionaries with gantry information, or empty list if error
    """
    global _road_infra_cache
    
    # Return cached parsed data if available
    if _road_infra_cache['erp_gantries'] is not None:
        return _road_infra_cache['erp_gantries']
    
    # Fetch raw GeoJSON data
    geojson_data = fetch_erp_gantry_data()
    
    # Parse the data
    gantry_data = parse_erp_gantry_data(geojson_data)
    
    # Cache the parsed result
    if gantry_data:
        _road_infra_cache['erp_gantries'] = gantry_data
        print("ERP gantries data cached in memory")
    
    return gantry_data


def fetch_taxi_availability():
    """
    Fetch taxi availability data from Data.gov.sg API.
    
    Returns:
        Dictionary containing taxi location data or None if error
    """
    return fetch_url_2min_cached(TAXI_API_URL)


def create_taxi_markers(data):
    """
    Create map markers for taxi locations.
    
    Args:
        data: API response with taxi coordinates
    
    Returns:
        List of dl.CircleMarker components
    """
    markers = []
    
    if not data or 'features' not in data:
        return markers
    
    features = data.get('features', [])
    if not features:
        return markers
    
    # Get coordinates from first feature
    first_feature = features[0]
    geometry = first_feature.get('geometry', {})
    coordinates = geometry.get('coordinates', [])
    
    # Create markers for each taxi location
    # Coordinates are [lon, lat] format, need to swap for Leaflet [lat, lon]
    for coord in coordinates:
        if len(coord) >= 2:
            lon, lat = coord[0], coord[1]
            
            # Create small circle marker for each taxi (lighter yellow for taxi locations)
            markers.append(
                dl.CircleMarker(
                    center=[lat, lon],
                    radius=3,
                    color="#FFD700",  # Lighter yellow (gold)
                    fill=True,
                    fillColor="#FFD700",
                    fillOpacity=0.7,
                    weight=1,
                )
            )
    
    return markers


def format_taxi_count_display(data):
    """
    Format the taxi count display.
    
    Args:
        data: API response with taxi data
    
    Returns:
        HTML Div with taxi count information
    """
    if not data or 'features' not in data:
        return html.Div(
            [
                html.P(
                    "Error loading taxi data",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                    }
                )
            ]
        )
    
    features = data.get('features', [])
    if not features:
        return html.Div(
            [
                html.P(
                    "No taxi data available",
                    style={
                        "color": "#999",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                    }
                )
            ]
        )
    
    # Get taxi count and timestamp from properties
    first_feature = features[0]
    properties = first_feature.get('properties', {})
    taxi_count = properties.get('taxi_count', 0)
    timestamp = properties.get('timestamp', '')
    
    # Format timestamp
    if timestamp:
        # Parse and format timestamp (e.g., "2025-12-10T20:58:46+08:00")
        try:
            parsed_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            formatted_time = timestamp
    else:
        formatted_time = "Unknown"
    
    return html.Div(
        [
            # Large taxi count display
            html.Div(
                [
                    html.Span(
                        "🚕",
                        style={"fontSize": "2rem", "marginRight": "0.625rem", "lineHeight": "1"}
                    ),
                    html.Span(
                        f"{taxi_count:,}",
                        style={
                            "fontSize": "2.5rem",
                            "fontWeight": "bold",
                            "color": "#FFD700",
                            "lineHeight": "1",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "marginBottom": "0.625rem",
                    "flexWrap": "wrap",
                }
            ),
            html.P(
                "Available Taxis",
                style={
                    "color": "#fff",
                    "textAlign": "center",
                    "fontSize": "0.875rem",
                    "fontWeight": "600",
                    "margin": "0 0 0.625rem 0",
                }
            ),
            html.P(
                f"Last updated: {formatted_time}",
                style={
                    "color": "#888",
                    "textAlign": "center",
                    "fontSize": "0.6875rem",
                    "fontStyle": "italic",
                    "margin": "0",
                }
            ),
        ],
        style={
            "padding": "0.9375rem",
            "backgroundColor": "#2c3e50",
            "borderRadius": "0.5rem",
            "width": "100%",
            "boxSizing": "border-box",
            "overflow": "hidden",
        }
    )


def fetch_traffic_cameras():
    """
    Fetch traffic camera data from Data.gov.sg API.
    
    Returns:
        Dictionary containing camera data or None if error
    """
    return fetch_url_2min_cached(TRAFFIC_IMAGES_API_URL)


def parse_traffic_camera_data(data):
    """
    Parse traffic camera API response to extract camera metadata.
    
    Args:
        data: API response
    
    Returns:
        Dictionary mapping camera_id to metadata
    """
    camera_dict = {}
    
    if not data or 'items' not in data:
        return camera_dict
    
    items = data.get('items', [])
    if not items:
        return camera_dict
    
    cameras = items[0].get('cameras', [])
    
    for camera in cameras:
        camera_id = camera.get('camera_id', '')
        if camera_id:
            location = camera.get('location', {})
            camera_dict[camera_id] = {
                'timestamp': camera.get('timestamp', ''),
                'image_url': camera.get('image', ''),
                'lat': location.get('latitude'),
                'lon': location.get('longitude'),
            }
    
    return camera_dict


def create_cctv_markers(camera_data):
    """
    Create map markers for CCTV camera locations with image popups.
    
    Args:
        camera_data: Dictionary of camera metadata
    
    Returns:
        List of dl.Marker components with popups
    """
    markers = []
    
    for camera_id, info in camera_data.items():
        lat = info.get('lat')
        lon = info.get('lon')
        image_url = info.get('image_url', '')
        timestamp = info.get('timestamp', '')
        
        if lat is None or lon is None:
            continue

        # Format timestamp if available
        datetime_text = ""
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    # Try to parse and format the timestamp
                    parsed_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    datetime_text = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    datetime_text = str(timestamp)
            except (ValueError, AttributeError):
                datetime_text = str(timestamp) if timestamp else ""

        # Create popup content
        popup_children = [
            html.Strong(
                f"Camera {camera_id}",
                style={"fontSize": "0.875rem"}
            ),
            html.Br(),
        ]
        
        # Add lat/lon on next line
        if lat is not None and lon is not None:
            popup_children.append(
                html.Div(
                    f"(lat: {lat:.6f}, lon: {lon:.6f})",
                    style={"fontSize": "0.75rem", "color": "#888", "marginTop": "0.25rem"}
                )
            )
        
        # Add datetime if available
        if datetime_text:
            popup_children.append(
                html.Div(
                    f"Time: {datetime_text}",
                    style={"fontSize": "0.75rem", "color": "#888", "marginTop": "0.25rem"}
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
                }
            )
        )

        markers.append(
            dl.Marker(
                position=[lat, lon],
                children=[
                    dl.Tooltip(f"Camera {camera_id}"),
                    dl.Popup(
                        children=html.Div(
                            popup_children,
                            style={"textAlign": "center"}
                        ),
                        maxWidth=320,
                    ),
                ],
                icon={
                    "iconUrl": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
                    "shadowUrl": "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
                    "iconSize": [25, 41],
                    "iconAnchor": [12, 41],
                    "popupAnchor": [1, -34],
                    "shadowSize": [41, 41],
                },
            )
        )
    
    return markers


def format_cctv_count_display(camera_data):
    """
    Format the CCTV camera count display.
    
    Args:
        camera_data: Dictionary of camera metadata
    
    Returns:
        HTML Div with camera count information
    """
    if not camera_data:
        return html.Div(
            [
                html.P(
                    "Error loading camera data",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                    }
                )
            ]
        )
    
    camera_count = len(camera_data)
    
    # Get timestamp from first camera
    first_camera = next(iter(camera_data.values()), {})
    timestamp = first_camera.get('timestamp', '')
    
    if timestamp:
        try:
            parsed_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            formatted_time = timestamp
    else:
        formatted_time = "Unknown"
    
    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "📹",
                        style={"fontSize": "2rem", "marginRight": "0.625rem", "lineHeight": "1"}
                    ),
                    html.Span(
                        f"{camera_count}",
                        style={
                            "fontSize": "2.5rem",
                            "fontWeight": "bold",
                            "color": "#4CAF50",
                            "lineHeight": "1",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "marginBottom": "0.625rem",
                    "flexWrap": "wrap",
                }
            ),
            html.P(
                "Traffic Cameras",
                style={
                    "color": "#fff",
                    "textAlign": "center",
                    "fontSize": "0.875rem",
                    "fontWeight": "600",
                    "margin": "0 0 0.625rem 0",
                }
            ),
            html.P(
                f"Last updated: {formatted_time}",
                style={
                    "color": "#888",
                    "textAlign": "center",
                    "fontSize": "0.6875rem",
                    "fontStyle": "italic",
                    "margin": "0",
                }
            ),
            html.P(
                "Click markers on map to view live feed",
                style={
                    "color": "#4CAF50",
                    "textAlign": "center",
                    "fontSize": "0.625rem",
                    "margin": "0.625rem 0 0 0",
                }
            ),
        ],
        style={
            "padding": "0.9375rem",
            "backgroundColor": "#2c3e50",
            "borderRadius": "0.5rem",
            "width": "100%",
            "boxSizing": "border-box",
            "overflow": "hidden",
        }
    )


# fetch_erp_gantry_data is now imported from utils.data_download_helper


def extract_gantry_number(description_html):
    """
    Extract gantry number from HTML description field.
    
    Args:
        description_html: HTML string containing gantry attributes
    
    Returns:
        Gantry number string or "Unknown"
    """
    if not description_html:
        return "Unknown"

    # Look for GNTRY_NUM in the HTML table
    match = re.search(r'<th>GNTRY_NUM</th>\s*<td>([^<]*)</td>', description_html)
    if match:
        gantry_num = match.group(1).strip()
        return gantry_num if gantry_num else "Unknown"

    return "Unknown"


def parse_erp_gantry_data(geojson_data):
    """
    Parse ERP gantry GeoJSON data.
    
    Args:
        geojson_data: GeoJSON FeatureCollection
    
    Returns:
        List of dictionaries with gantry information
    """
    gantries = []

    if not geojson_data or 'features' not in geojson_data:
        return gantries

    features = geojson_data.get('features', [])

    for feature in features:
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})

        if geometry.get('type') != 'LineString':
            continue

        coordinates = geometry.get('coordinates', [])
        if len(coordinates) < 2:
            continue

        # Extract gantry number from description
        description = properties.get('Description', '')
        gantry_num = extract_gantry_number(description)
        unique_id = properties.get('Name', '')

        # LineString has two points - convert to [lat, lon] for Leaflet
        # GeoJSON coordinates are [lon, lat, z]
        line_coords = [[coord[1], coord[0]] for coord in coordinates]

        gantries.append({
            'gantry_num': gantry_num,
            'unique_id': unique_id,
            'coordinates': line_coords,
            'description': description,
        })

    return gantries


def create_erp_gantry_markers(gantry_data):
    """
    Create map polylines for ERP gantry locations.
    
    Args:
        gantry_data: List of gantry dictionaries
    
    Returns:
        List of dl.Polyline components
    """
    markers = []

    for gantry in gantry_data:
        coords = gantry.get('coordinates', [])
        gantry_num = gantry.get('gantry_num', 'Unknown')
        unique_id = gantry.get('unique_id', '')

        if not coords or len(coords) < 2:
            continue

        # Create tooltip text
        tooltip_text = f"ERP Gantry {gantry_num}"
        if unique_id and unique_id != f"kml_{gantry_num}":
            tooltip_text += f" (ID: {unique_id})"

        # Create polyline for the gantry (line between two points)
        markers.append(
            dl.Polyline(
                positions=coords,
                color="#FF6B6B",
                weight=8,
                opacity=0.9,
                children=[
                    dl.Tooltip(tooltip_text),
                ]
            )
        )

    return markers


# fetch_pub_cctv_data is now imported from utils.data_download_helper


def fetch_taxi_stands_data():
    """
    Fetch Taxi Stands data from LTA DataMall API.
    Uses in-memory cache since taxi stands are static infrastructure.
    
    Returns:
        Dictionary containing taxi stands data or None if error
    """
    global _road_infra_cache
    
    # Return cached data if available
    if _road_infra_cache['taxi_stands'] is not None:
        return _road_infra_cache['taxi_stands']
    
    taxi_stands_url = "https://datamall2.mytransport.sg/ltaodataservice/TaxiStands"
    api_key = os.getenv("LTA_API_KEY")
    
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    data = fetch_url(taxi_stands_url, headers)
    
    # Cache the result
    if data:
        _road_infra_cache['taxi_stands'] = data
        print("Taxi stands data cached in memory")
    
    return data


def create_taxi_stands_markers(taxi_stands_data):
    """
    Create map markers for Taxi Stand locations.
    
    Args:
        taxi_stands_data: Dictionary containing taxi stands response from LTA API
    
    Returns:
        List of dl.CircleMarker components
    """
    if not taxi_stands_data:
        return []

    markers = []
    
    # Extract taxi stands from response
    stands = []
    if isinstance(taxi_stands_data, dict):
        if "value" in taxi_stands_data:
            stands = taxi_stands_data.get("value", [])
        elif isinstance(taxi_stands_data, list):
            stands = taxi_stands_data
    elif isinstance(taxi_stands_data, list):
        stands = taxi_stands_data
    
    for stand in stands:
        try:
            latitude = float(stand.get('Latitude', 0))
            longitude = float(stand.get('Longitude', 0))
            taxi_code = stand.get('TaxiCode', 'N/A')
            name = stand.get('Name', 'N/A')
            bfa = stand.get('Bfa', 'N/A')
            ownership = stand.get('Ownership', 'N/A')
            stand_type = stand.get('Type', 'N/A')
            
            if latitude == 0 or longitude == 0:
                continue
            
            # Create tooltip with bulleted points
            tooltip_text = (
                f"• Name: {taxi_code}({name})\n"
                f"• Barrier Free: {bfa}\n"
                f"• Owner: {ownership}\n"
                f"• Type: {stand_type}"
            )
            
            # Create text box label for taxi stand (similar to carpark)
            # Use taxi_code as the label, or a shortened name if code is N/A
            label_text = taxi_code if taxi_code != 'N/A' else (name[:8] if len(name) > 8 else name)
            
            marker_html = (
                f'<div style="position:relative;display:flex;flex-direction:column;'
                f'align-items:center;">'
                f'<div style="background:#FFA500;color:#fff;padding:0.25rem 0.5rem;'
                f'border-radius:0.25rem;border:0.125rem solid #fff;'
                f'box-shadow:0 0.125rem 0.5rem rgba(255,165,0,0.6);'
                f'font-size:0.6875rem;font-weight:bold;white-space:nowrap;">'
                f'{label_text}</div>'
                f'<div style="width:0;height:0;border-left:0.5rem solid transparent;'
                f'border-right:0.5rem solid transparent;border-top:0.5rem solid #FFA500;'
                f'margin-top:-0.125rem;"></div>'
                f'</div>'
            )
            
            marker_id = f"taxi-stand-{taxi_code}-{latitude}-{longitude}"
            
            markers.append(
                dl.DivMarker(
                    id=marker_id,
                    position=[latitude, longitude],
                    iconOptions={
                        'className': 'taxi-stand-pin',
                        'html': marker_html,
                        'iconSize': [60, 40],
                        'iconAnchor': [30, 40],
                    },
                    children=[
                        dl.Tooltip(html.Pre(tooltip_text, style={"margin": "0", "fontFamily": "inherit"})),
                    ]
                )
            )
        except (ValueError, TypeError, KeyError):
            continue
            
    return markers


def format_taxi_stands_count_display(taxi_stands_data):
    """
    Format the Taxi Stands count display.
    
    Args:
        taxi_stands_data: Dictionary containing taxi stands response from LTA API
    
    Returns:
        HTML Div with taxi stands count information
    """
    if not taxi_stands_data:
        return html.Div(
            [
                html.P(
                    "Error loading taxi stands data",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "padding": "1.25rem",
                        "fontSize": "0.75rem",
                    }
                )
            ]
        )
    
    # Extract count from response
    stands = []
    if isinstance(taxi_stands_data, dict):
        if "value" in taxi_stands_data:
            stands = taxi_stands_data.get("value", [])
        elif isinstance(taxi_stands_data, list):
            stands = taxi_stands_data
    elif isinstance(taxi_stands_data, list):
        stands = taxi_stands_data
    
    count = len(stands)
    return html.Div(
        [
            html.P(
                f"Total taxi stands: {count}",
                style={
                    "color": "#fff",
                    "textAlign": "center",
                    "padding": "0.625rem",
                    "fontSize": "0.875rem",
                    "fontWeight": "600",
                    "margin": "0",
                }
            )
        ]
    )


def format_combined_taxi_display(taxi_data, taxi_stands_data):
    """
    Format the combined taxi locations and stands count display.
    
    Args:
        taxi_data: API response with taxi location data
        taxi_stands_data: Dictionary containing taxi stands response from LTA API
    
    Returns:
        HTML Div with combined taxi locations and stands count information
    """
    # Get taxi count
    taxi_count = 0
    timestamp = "Unknown"
    if taxi_data and 'features' in taxi_data:
        features = taxi_data.get('features', [])
        if features:
            first_feature = features[0]
            properties = first_feature.get('properties', {})
            taxi_count = properties.get('taxi_count', 0)
            timestamp = properties.get('timestamp', '')
    
    # Get taxi stands count
    stands_count = 0
    if taxi_stands_data:
        stands = []
        if isinstance(taxi_stands_data, dict):
            if "value" in taxi_stands_data:
                stands = taxi_stands_data.get("value", [])
            elif isinstance(taxi_stands_data, list):
                stands = taxi_stands_data
        elif isinstance(taxi_stands_data, list):
            stands = taxi_stands_data
        stands_count = len(stands)
    
    # Format timestamp
    if timestamp and timestamp != "Unknown":
        try:
            parsed_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            formatted_time = timestamp
    else:
        formatted_time = "Unknown"
    
    return html.Div(
        [
            # Side by side layout for taxi locations and stands
            html.Div(
                [
                    # Left side: Taxi locations
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        "🚕",
                                        style={"fontSize": "1.5rem", "marginRight": "0.5rem", "lineHeight": "1"}
                                    ),
                                    html.Span(
                                        f"{taxi_count:,}",
                                        style={
                                            "fontSize": "2rem",
                                            "fontWeight": "bold",
                                            "color": "#FFD700",  # Lighter yellow
                                            "lineHeight": "1",
                                        }
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "marginBottom": "0.25rem",
                                }
                            ),
                            html.P(
                                "Available Taxis",
                                style={
                                    "color": "#fff",
                                    "textAlign": "center",
                                    "fontSize": "0.75rem",
                                    "fontWeight": "600",
                                    "margin": "0",
                                }
                            ),
                        ],
                        style={
                            "flex": "1",
                            "display": "flex",
                            "flexDirection": "column",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "padding": "0.5rem",
                        }
                    ),
                    # Right side: Taxi stands
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        "🚕",
                                        style={"fontSize": "1.5rem", "marginRight": "0.5rem", "lineHeight": "1"}
                                    ),
                                    html.Span(
                                        f"{stands_count}",
                                        style={
                                            "fontSize": "2rem",
                                            "fontWeight": "bold",
                                            "color": "#FFA500",  # Darker yellow/orange
                                            "lineHeight": "1",
                                        }
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "marginBottom": "0.25rem",
                                }
                            ),
                            html.P(
                                "Taxi Stands",
                                style={
                                    "color": "#fff",
                                    "textAlign": "center",
                                    "fontSize": "0.75rem",
                                    "fontWeight": "600",
                                    "margin": "0",
                                }
                            ),
                        ],
                        style={
                            "flex": "1",
                            "display": "flex",
                            "flexDirection": "column",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "padding": "0.5rem",
                            "borderLeft": "0.0625rem solid #5a6a7a",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "flexDirection": "row",
                    "width": "100%",
                    "marginBottom": "0.5rem",
                }
            ),
            html.P(
                f"Last updated: {formatted_time}",
                style={
                    "color": "#888",
                    "textAlign": "center",
                    "fontSize": "0.6875rem",
                    "fontStyle": "italic",
                    "margin": "0",
                }
            ),
        ],
        style={
            "padding": "0.9375rem",
            "backgroundColor": "#2c3e50",
            "borderRadius": "0.5rem",
            "width": "100%",
            "boxSizing": "border-box",
            "overflow": "hidden",
            "display": "flex",
            "flexDirection": "column",
            "height": "100%",
        }
    )


def fetch_traffic_incidents_data():
    """
    Fetch traffic incidents from LTA DataMall API.
    
    Returns:
        Dictionary containing traffic incidents data or None if error
    """
    api_key = os.getenv("LTA_API_KEY")
    
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    return fetch_url_2min_cached(TRAFFIC_INCIDENTS_URL, headers)


def fetch_vms_data() -> Optional[Dict[str, Any]]:
    """
    Fetch VMS (Variable Message Signs) data from LTA DataMall API.
    Uses in-memory cache since VMS locations are static infrastructure.
    
    Returns:
        Dictionary containing VMS data or None if error
    """
    global _road_infra_cache
    
    # Return cached data if available
    if _road_infra_cache['vms'] is not None:
        return _road_infra_cache['vms']
    
    api_key = os.getenv("LTA_API_KEY")
    
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    data = fetch_url(VMS_URL, headers)
    
    # Cache the result
    if data:
        _road_infra_cache['vms'] = data
        print("VMS data cached in memory")
    
    return data


def fetch_vms_data_async() -> Optional[Future]:
    """
    Fetch VMS data asynchronously (returns Future).
    Call .result() to get the data when needed.
    
    Returns:
        Future object that will contain the VMS data, or None if error
    """
    api_key = os.getenv("LTA_API_KEY")
    
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    return fetch_async(VMS_URL, headers)


def fetch_bus_stops_data() -> Optional[Dict[str, Any]]:
    """
    Fetch all bus stops data from LTA DataMall API with optimized parallel pagination.
    Uses in-memory cache with monthly refresh since bus stops are static infrastructure.
    Strategy:
    1. First fetch 5000 records (10 pages) in parallel (skip=0, 500, 1000, ..., 4500)
    2. Check if last page returned full 500 records
    3. If yes, continue fetching subsequent pages in parallel batches
    
    Returns:
        Dictionary containing all bus stops data with combined 'value' list, or None if error
    """
    global _road_infra_cache
    
    # Monthly cache bucket (YYYYMM) - bus stops update monthly
    current_bucket = datetime.now().year * 100 + datetime.now().month
    
    # Return cached data if available and still within the same month
    if (
        _road_infra_cache['bus_stops'] is not None
        and _road_infra_cache.get('bus_stops_bucket') == current_bucket
    ):
        return _road_infra_cache['bus_stops']
    
    # If not cached, proceed with fetching
    api_key = os.getenv("LTA_API_KEY")
    
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    from utils.async_fetcher import _executor
    from concurrent.futures import as_completed
    
    all_bus_stops = []
    page_size = 500
    initial_batch_size = 5000  # Known minimum: 5000 records
    max_skip = 6000  # Maximum skip value to limit total records fetched
    
    # Step 1: Fetch first 5000 records in parallel (10 pages)
    print("Fetching first 5000 bus stops in parallel...")
    initial_skip_values = list(range(0, initial_batch_size, page_size))  # [0, 500, 1000, ..., 4500]
    
    # Create URLs for initial batch
    initial_urls = []
    for skip in initial_skip_values:
        url = f"{BUS_STOPS_URL}?$skip={skip}" if skip > 0 else BUS_STOPS_URL
        initial_urls.append((url, skip))
    
    # Submit all initial requests to thread pool
    futures = {
        _executor.submit(fetch_url, url, headers): skip
        for url, skip in initial_urls
    }
    
    # Collect results and sort by skip value
    initial_results = {}
    for future in as_completed(futures):
        skip = futures[future]
        try:
            page_data = future.result()
            if page_data and 'value' in page_data:
                initial_results[skip] = page_data.get('value', [])
        except Exception as e:
            print(f"Error fetching bus stops (skip={skip}): {e}")
            initial_results[skip] = []
    
    # Combine results in order
    for skip in sorted(initial_results.keys()):
        bus_stops = initial_results[skip]
        all_bus_stops.extend(bus_stops)
        print(f"Fetched {len(bus_stops)} bus stops (skip={skip}), total so far: {len(all_bus_stops)}")
    
    # Step 2: Check if we need to continue fetching
    # Check the last page (skip=4500) to see if it returned full 500 records
    last_page_size = len(initial_results.get(4500, []))
    current_skip = initial_batch_size
    
    # Continue fetching in parallel batches only if last page returned exactly 500 records
    # (If it returned < 500, we've reached the end. If exactly 500, check next batch)
    # Also stop if we've reached the maximum skip limit
    while last_page_size == page_size and current_skip < max_skip:
        print(f"Last page was full ({last_page_size} records), fetching next batch starting at skip={current_skip}...")
        
        # Calculate batch skip values, but limit to max_skip
        batch_end = min(current_skip + initial_batch_size, max_skip + page_size)
        batch_skip_values = [skip for skip in range(current_skip, batch_end, page_size) if skip <= max_skip]
        
        # If no valid skip values, stop
        if not batch_skip_values:
            break
        
        # Create URLs for this batch
        batch_urls = []
        for skip in batch_skip_values:
            url = f"{BUS_STOPS_URL}?$skip={skip}"
            batch_urls.append((url, skip))
        
        # Submit all batch requests to thread pool
        batch_futures = {
            _executor.submit(fetch_url, url, headers): skip
            for url, skip in batch_urls
        }
        
        # Collect results
        batch_results = {}
        for future in as_completed(batch_futures):
            skip = batch_futures[future]
            try:
                page_data = future.result()
                if page_data and 'value' in page_data:
                    batch_results[skip] = page_data.get('value', [])
                else:
                    batch_results[skip] = []
            except Exception as e:
                print(f"Error fetching bus stops (skip={skip}): {e}")
                batch_results[skip] = []
        
        # Combine results in order
        for skip in sorted(batch_results.keys()):
            bus_stops = batch_results[skip]
            if not bus_stops:
                # Empty page means we've reached the end
                last_page_size = 0
                break
            
            all_bus_stops.extend(bus_stops)
            print(f"Fetched {len(bus_stops)} bus stops (skip={skip}), total so far: {len(all_bus_stops)}")
            
            # Update last_page_size for next iteration check
            last_page_size = len(bus_stops)
            
            # If this page returned <= 500 records, it's the last page - stop immediately
            # Don't fetch the next batch since we've reached the end
            if last_page_size <= page_size:
                break
        
        # If we got <= 500 records (or empty), we've reached the end - stop fetching
        if last_page_size <= page_size:
            break
        
        # Move to next batch
        current_skip += initial_batch_size
    
    print(f"Total bus stops fetched: {len(all_bus_stops)}")
    
    # Return in the same format as the API response
    result = {'value': all_bus_stops}
    
    # Cache the result with monthly bucket
    if result:
        _road_infra_cache['bus_stops'] = result
        _road_infra_cache['bus_stops_bucket'] = current_bucket
        print(f"Bus stops data cached in memory: {len(all_bus_stops)} stops (bucket: {current_bucket})")
    
    return result


def fetch_bus_routes_data() -> Optional[Dict[str, Any]]:
    """
    Fetch all bus routes data from LTA DataMall API with optimized parallel pagination.
    Uses in-memory cache with monthly refresh since bus routes are static infrastructure.
    
    Returns:
        Dictionary containing all bus routes data with combined 'value' list, or None if error
    """
    global _road_infra_cache
    
    # Monthly cache bucket (YYYYMM) - bus routes update monthly
    current_bucket = datetime.now().year * 100 + datetime.now().month
    
    # Return cached data if available and still within the same month
    if (
        _road_infra_cache['bus_routes'] is not None
        and _road_infra_cache.get('bus_routes_bucket') == current_bucket
    ):
        return _road_infra_cache['bus_routes']
    
    # If not cached, proceed with fetching
    api_key = os.getenv("LTA_API_KEY")
    
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    from utils.async_fetcher import _executor, fetch_url
    from concurrent.futures import as_completed
    
    all_bus_routes = []
    page_size = 500
    batch_size = 5000
    max_skip = 40000  # Safety limit
    
    current_skip = 0
    while current_skip < max_skip:
        print(f"Fetching bus routes batch starting at skip={current_skip}...")
        skip_values = list(range(current_skip, min(current_skip + batch_size, max_skip), page_size))
        
        # Create futures for this batch
        futures = {
            _executor.submit(fetch_url, f"{BUS_ROUTES_URL}?$skip={skip}" if skip > 0 else BUS_ROUTES_URL, headers): skip
            for skip in skip_values
        }
        
        batch_results = {}
        for future in as_completed(futures):
            skip = futures[future]
            try:
                page_data = future.result()
                if page_data and 'value' in page_data:
                    batch_results[skip] = page_data.get('value', [])
                else:
                    batch_results[skip] = []
            except Exception as e:
                print(f"Error fetching bus routes (skip={skip}): {e}")
                batch_results[skip] = []
        
        # Combine results from this batch in order and check for end of data
        reached_end = False
        for skip in sorted(skip_values):
            data = batch_results.get(skip, [])
            all_bus_routes.extend(data)
            if len(data) < page_size:
                reached_end = True
                break
        
        if reached_end:
            break
            
        current_skip += batch_size
        
    print(f"Total bus route segments fetched: {len(all_bus_routes)}")
    
    # Return in the same format as the API response
    result = {'value': all_bus_routes}
    
    # Cache the result with monthly bucket
    if result:
        _road_infra_cache['bus_routes'] = result
        _road_infra_cache['bus_routes_bucket'] = current_bucket
        print(f"Bus routes data cached in memory: {len(all_bus_routes)} segments (bucket: {current_bucket})")
    
    return result


def fetch_bus_routes_data_async() -> Optional[Future]:
    """
    Fetch all bus routes data asynchronously (returns Future).
    Call .result() to get the data when needed.
    
    Returns:
        Future object that will contain all bus routes data, or None if error
    """
    from utils.async_fetcher import _executor
    
    # Submit the synchronous function to thread pool
    return _executor.submit(fetch_bus_routes_data)


def get_bus_services_count() -> int:
    """
    Get count of unique bus services from bus routes data.
    
    Returns:
        Number of unique bus services
    """
    routes_data = fetch_bus_routes_data()
    
    if not routes_data or 'value' not in routes_data:
        return 0
    
    routes = routes_data.get('value', [])
    
    # Extract unique service numbers
    service_numbers = set()
    for route in routes:
        service_no = route.get('ServiceNo', '')
        if service_no:
            service_numbers.add(service_no)
    
    return len(service_numbers)


def create_bus_stops_markers(bus_stops_data: Optional[Dict[str, Any]]) -> List[dl.DivMarker]:
    """
    Create map markers for bus stop locations.
    
    Args:
        bus_stops_data: Dictionary containing bus stops response from LTA API
    
    Returns:
        List of dl.DivMarker components
    """
    markers = []
    
    if not bus_stops_data or 'value' not in bus_stops_data:
        return markers
    
    bus_stops = bus_stops_data.get('value', [])
    
    for bus_stop in bus_stops:
        try:
            latitude = float(bus_stop.get('Latitude', 0))
            longitude = float(bus_stop.get('Longitude', 0))
            bus_stop_code = bus_stop.get('BusStopCode', 'N/A')
            road_name = bus_stop.get('RoadName', 'N/A')
            description = bus_stop.get('Description', 'N/A')
            
            if latitude == 0 or longitude == 0:
                continue
            
            # Create tooltip with generic message
            tooltip_text = "Click to show more details of this bus stop"
            
            marker_id = f"bus-stop-marker-{bus_stop_code}"
            
            # Create clickable circle marker using DivMarker with a button
            marker_html = (
                f'<div style="position:relative;width:10px;height:10px;'
                f'border-radius:50%;background-color:#4169E1;'
                f'border:2px solid #4169E1;opacity:0.7;cursor:pointer;">'
                f'</div>'
            )
            
            markers.append(
                dl.DivMarker(
                    id=marker_id,
                    position=[latitude, longitude],
                    iconOptions={
                        'className': 'bus-stop-marker',
                        'html': marker_html,
                        'iconSize': [10, 10],
                        'iconAnchor': [5, 5],
                    },
                    children=[
                        dl.Tooltip(tooltip_text),
                        html.Button(
                            id={"type": "bus-stop-marker-btn", "index": bus_stop_code},
                            n_clicks=0,
                            style={
                                "position": "absolute",
                                "width": "100%",
                                "height": "100%",
                                "top": "0",
                                "left": "0",
                                "border": "none",
                                "background": "transparent",
                                "cursor": "pointer",
                                "padding": "0",
                                "margin": "0",
                            }
                        ),
                    ]
                )
            )
        except (ValueError, TypeError, KeyError):
            continue
    
    return markers


def calculate_bus_stop_viewport_bounds(center_lat: float, center_lon: float, zoom: int) -> Dict[str, float]:
    """
    Calculate viewport bounds based on center and zoom level.
    
    Args:
        center_lat: Latitude of viewport center
        center_lon: Longitude of viewport center
        zoom: Current zoom level
    
    Returns:
        Dictionary with 'north', 'south', 'east', 'west' bounds
    """
    # Approximate viewport size in degrees
    # At zoom level z, the world is 256 * 2^z pixels wide
    viewport_width_pixels = 800
    viewport_height_pixels = 600
    
    # Degrees per pixel at this zoom level (at equator)
    degrees_per_pixel = 360 / (256 * (2 ** zoom))
    
    # Calculate lat/lon offsets (rough approximation)
    lat_offset = (viewport_height_pixels / 2) * degrees_per_pixel
    lon_offset = (viewport_width_pixels / 2) * degrees_per_pixel / math.cos(math.radians(center_lat))
    
    return {
        'north': center_lat + lat_offset,
        'south': center_lat - lat_offset,
        'east': center_lon + lon_offset,
        'west': center_lon - lon_offset
    }


def filter_bus_stops_by_viewport(
    bus_stops_data: Optional[Dict[str, Any]], 
    center_lat: float, 
    center_lon: float, 
    zoom: int
) -> List[Dict[str, Any]]:
    """
    Filter bus stops data by viewport bounds.
    
    Args:
        bus_stops_data: Dictionary containing bus stops data
        center_lat: Latitude of viewport center
        center_lon: Longitude of viewport center
        zoom: Current zoom level
    
    Returns:
        List of filtered bus stops within viewport
    """
    if not bus_stops_data or 'value' not in bus_stops_data:
        return []
    
    bus_stops = bus_stops_data.get('value', [])
    bounds = calculate_bus_stop_viewport_bounds(center_lat, center_lon, zoom)
    
    filtered_stops = []
    for bus_stop in bus_stops:
        try:
            lat = float(bus_stop.get('Latitude', 0))
            lon = float(bus_stop.get('Longitude', 0))
            
            if lat == 0 or lon == 0:
                continue
            
            # Check if point is within viewport
            if (bounds['south'] <= lat <= bounds['north'] and 
                bounds['west'] <= lon <= bounds['east']):
                filtered_stops.append(bus_stop)
        except (ValueError, TypeError):
            continue
    
    return filtered_stops


def create_bus_stops_circle_markers(bus_stops_data: Optional[Dict[str, Any]]) -> List[dl.CircleMarker]:
    """
    Create simple CircleMarker components for bus stop locations.
    Lightweight markers for better performance when zoomed in.
    Click detection is handled separately via map click events.
    
    Args:
        bus_stops_data: Dictionary containing bus stops response from LTA API
    
    Returns:
        List of dl.CircleMarker components
    """
    markers = []
    
    if not bus_stops_data or 'value' not in bus_stops_data:
        return markers
    
    bus_stops = bus_stops_data.get('value', [])
    
    for bus_stop in bus_stops:
        try:
            latitude = float(bus_stop.get('Latitude', 0))
            longitude = float(bus_stop.get('Longitude', 0))
            bus_stop_code = bus_stop.get('BusStopCode', 'N/A')
            description = bus_stop.get('Description', 'N/A')
            
            if latitude == 0 or longitude == 0:
                continue
            
            tooltip_text = f"🚏 {description} ({bus_stop_code}) - Click to view arrivals"
            
            markers.append(
                dl.CircleMarker(
                    id={'type': 'bus-stop-marker', 'index': bus_stop_code},
                    center=[latitude, longitude],
                    radius=8,
                    color="#4169E1",
                    fillColor="#4169E1",
                    fillOpacity=0.7,
                    weight=2,
                    children=[
                        dl.Tooltip(tooltip_text)
                    ]
                )
            )
        except (ValueError, TypeError, KeyError):
            continue
            
    return markers


def find_nearest_bus_stop(click_lat: float, click_lon: float, bus_stops_data: Optional[Dict[str, Any]], max_distance_m: float = 50.0) -> Optional[str]:
    """
    Find the nearest bus stop to a click location.
    
    Args:
        click_lat: Latitude of click location
        click_lon: Longitude of click location
        bus_stops_data: Dictionary containing bus stops data
        max_distance_m: Maximum distance in meters to consider a bus stop as clicked
    
    Returns:
        Bus stop code if found within max_distance_m, None otherwise
    """
    if not bus_stops_data or 'value' not in bus_stops_data:
        return None
    
    bus_stops = bus_stops_data.get('value', [])
    nearest_code = None
    nearest_distance = float('inf')
    
    for bus_stop in bus_stops:
        try:
            lat = float(bus_stop.get('Latitude', 0))
            lon = float(bus_stop.get('Longitude', 0))
            
            if lat == 0 or lon == 0:
                continue
            
            # Calculate distance using haversine formula
            distance = _haversine_distance_m(click_lat, click_lon, lat, lon)
            
            if distance < nearest_distance and distance <= max_distance_m:
                nearest_distance = distance
                nearest_code = bus_stop.get('BusStopCode')
        except (ValueError, TypeError):
            continue
    
    return nearest_code


def fetch_bus_stops_data_async() -> Optional[Future]:
    """
    Fetch all bus stops data asynchronously with pagination (returns Future).
    The API returns 500 records per page. This function fetches all pages
    until less than 500 records are returned.
    Call .result() to get the data when needed.
    
    Returns:
        Future object that will contain all bus stops data, or None if error
    """
    # Import executor from async_fetcher module
    from utils.async_fetcher import _executor
    
    # Submit the synchronous paginated function to thread pool
    return _executor.submit(fetch_bus_stops_data)


def load_speed_camera_data() -> pd.DataFrame:
    """
    Format bus service search results for display.
    
    Args:
        service_no: Bus service number to search for
        routes_data: Dictionary containing bus routes data from LTA API
    
    Returns:
        HTML Div containing formatted bus service route information
    """
    if not routes_data or 'value' not in routes_data:
        return html.Div(
            html.P(
                "Unable to fetch bus routes data. Please try again.",
                style={
                    "color": "#999",
                    "textAlign": "center",
                    "fontSize": "0.75rem",
                    "margin": "0.5rem 0",
                }
            )
        )
    
    routes = routes_data.get('value', [])
    
    # Filter routes for the specified service number
    service_routes = [route for route in routes if route.get('ServiceNo', '').upper() == service_no.upper().strip()]
    
    if not service_routes:
        return html.Div(
            html.P(
                f"No routes found for service {service_no}",
                style={
                    "color": "#ff6b6b",
                    "textAlign": "center",
                    "fontSize": "0.75rem",
                    "margin": "0.5rem 0",
                }
            )
        )
    
    # Extract bus timing information from first route (timing is same across all segments)
    timing_info = None
    if service_routes:
        timing_info = service_routes[0]
    
    # Group routes by direction
    directions = {}
    for route in service_routes:
        direction = route.get('Direction', 'N/A')
        if direction not in directions:
            directions[direction] = []
        directions[direction].append(route)
    
    # Sort routes by direction and stop sequence
    result_items = []
    
    # Add bus timing table if timing info is available
    if timing_info:
        timing_table = _create_bus_timing_table(timing_info)
        if timing_table:
            result_items.append(timing_table)
    
    for direction in sorted(directions.keys()):
        direction_routes = sorted(directions[direction], key=lambda x: int(x.get('StopSequence', 0)))
        print(direction_routes)
        # Get origin and destination
        origin_code = direction_routes[0].get('OriginCode', 'N/A') if direction_routes else 'N/A'
        destination_code = direction_routes[-1].get('DestinationCode', 'N/A') if direction_routes else 'N/A'
        
        # Get bus stop names if available
        bus_stops_data = fetch_bus_stops_data()
        origin_name = 'N/A'
        destination_name = 'N/A'
        
        if bus_stops_data and 'value' in bus_stops_data:
            for bs in bus_stops_data['value']:
                if bs.get('BusStopCode') == origin_code:
                    origin_name = bs.get('Description', 'N/A')
                if bs.get('BusStopCode') == destination_code:
                    destination_name = bs.get('Description', 'N/A')
        
        direction_label = "Direction 1" if direction == 1 else "Direction 2" if direction == 2 else f"Direction {direction}"
        
        # Create direction header
        direction_header = html.Div(
            style={
                "backgroundColor": "#3a4a5a",
                "padding": "0.5rem",
                "borderRadius": "0.25rem",
                "marginBottom": "0.5rem",
            },
            children=[
                html.Div(
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "0.25rem",
                    },
                    children=[
                        html.Span(
                            direction_label,
                            style={
                                "color": "#4169E1",
                                "fontWeight": "bold",
                                "fontSize": "0.75rem",
                            }
                        ),
                        html.Span(
                            f"From: {origin_name} ({origin_code})",
                            style={
                                "color": "#ccc",
                                "fontSize": "0.65rem",
                            }
                        ),
                        html.Span(
                            f"To: {destination_name} ({destination_code})",
                            style={
                                "color": "#ccc",
                                "fontSize": "0.65rem",
                            }
                        ),
                        html.Span(
                            f"Total stops: {len(direction_routes)}",
                            style={
                                "color": "#999",
                                "fontSize": "0.625rem",
                                "fontStyle": "italic",
                            }
                        ),
                        html.Span(
                            _format_route_distance(direction_routes),
                            style={
                                "color": "#999",
                                "fontSize": "0.625rem",
                                "fontStyle": "italic",
                            }
                        ),
                    ]
                )
            ]
        )
        
        result_items.append(direction_header)
    
    if not result_items:
        return html.Div(
            html.P(
                f"No route information available for service {service_no}",
                style={
                    "color": "#999",
                    "textAlign": "center",
                    "fontSize": "0.75rem",
                    "margin": "0.5rem 0",
                }
            )
        )
    
    return html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "0.5rem",
        },
        children=[
            html.Div(
                f"Service {service_no} - {len(directions)} direction(s)",
                style={
                    "color": "#fff",
                    "fontWeight": "bold",
                    "fontSize": "0.8125rem",
                    "marginBottom": "0.5rem",
                    "textAlign": "center",
                }
            ),
            *result_items
        ]
    )


def fetch_bus_stops_data_async() -> Optional[Future]:
    """
    Fetch all bus stops data asynchronously with pagination (returns Future).
    The API returns 500 records per page. This function fetches all pages
    until less than 500 records are returned.
    Call .result() to get the data when needed.
    
    Returns:
        Future object that will contain all bus stops data, or None if error
    """
    # Import executor from async_fetcher module
    from utils.async_fetcher import _executor
    
    # Submit the synchronous paginated function to thread pool
    return _executor.submit(fetch_bus_stops_data)


def load_speed_camera_data() -> pd.DataFrame:
    """
    Load speed camera data from CSV file.
    Uses in-memory cache since speed camera locations are static infrastructure.
    
    Returns:
        DataFrame with speed camera data
    """
    global _road_infra_cache
    
    # Return cached data if available
    if _road_infra_cache['speed_camera_df'] is not None:
        return _road_infra_cache['speed_camera_df']
    
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'speed_camera.csv')
    
    try:
        df = pd.read_csv(csv_path)
        # Cache the result
        _road_infra_cache['speed_camera_df'] = df
        print("Speed camera data cached in memory")
        return df
    except Exception as e:
        print(f"Error loading speed camera data: {e}")
        return pd.DataFrame()


def get_fixed_speed_camera_count() -> int:
    """
    Get count of fixed speed cameras from CSV.
    
    Returns:
        Number of fixed speed cameras
    """
    df = load_speed_camera_data()
    if df.empty:
        return 0
    
    # Filter for Fixed Speed Camera type
    fixed_cameras = df[df['type_of_speed_camera'] == 'Fixed Speed Camera']
    return len(fixed_cameras)


def create_fixed_speed_camera_markers() -> List[dl.CircleMarker]:
    """
    Create map markers for fixed speed camera locations from CSV.
    
    Returns:
        List of dl.CircleMarker components
    """
    markers = []
    df = load_speed_camera_data()
    
    if df.empty:
        return markers
    
    # Filter for Fixed Speed Camera type
    fixed_cameras = df[df['type_of_speed_camera'] == 'Fixed Speed Camera']
    
    for _, row in fixed_cameras.iterrows():
        try:
            lat = float(row.get('location_latitude', 0))
            lon = float(row.get('location_longitude', 0))
            location = str(row.get('location', 'Unknown Location'))
            
            if lat == 0 or lon == 0:
                continue
            
            # Create circle marker with location tooltip
            markers.append(
                dl.CircleMarker(
                    center=[lat, lon],
                    radius=6,
                    color="#81C784",  # Light green for speed cameras
                    fill=True,
                    fillColor="#81C784",
                    fillOpacity=0.7,
                    weight=2,
                    children=[
                        dl.Tooltip(html.Pre(f"Fixed Speed Camera\n{location}", style={"margin": "0", "fontFamily": "inherit"})),
                    ]
                )
            )
        except (ValueError, TypeError, KeyError):
            continue
            
    return markers


def create_vms_markers(vms_data: Optional[Dict[str, Any]]) -> List[dl.CircleMarker]:
    """
    Create map markers for VMS (Variable Message Signs) locations.
    
    Args:
        vms_data: Dictionary containing VMS response from LTA API
    
    Returns:
        List of dl.CircleMarker components
    """
    markers = []
    
    if not vms_data or 'value' not in vms_data:
        return markers
    
    vms_locations = vms_data.get('value', [])
    
    for vms in vms_locations:
        try:
            latitude = float(vms.get('Latitude', 0))
            longitude = float(vms.get('Longitude', 0))
            equipment_id = vms.get('EquipmentID', 'N/A')
            message = vms.get('Message', 'N/A')
            
            if latitude == 0 or longitude == 0:
                continue
            
            # Create tooltip with EquipmentID and Message in specified format
            tooltip_html = (
                f"ID: {equipment_id}\n"
                f"Message: {message}"
            )
            
            # Create circle marker for VMS (using silver color)
            markers.append(
                dl.CircleMarker(
                    center=[latitude, longitude],
                    radius=6,
                    color="#C0C0C0",  # Silver for VMS
                    fill=True,
                    fillColor="#C0C0C0",
                    fillOpacity=0.7,
                    weight=2,
                    children=[
                        dl.Tooltip(tooltip_html),
                    ]
                )
            )
        except (ValueError, TypeError, KeyError):
            continue
    
    return markers


def fetch_faulty_traffic_lights_data():
    """
    Fetch faulty traffic lights from LTA DataMall API.
    
    Returns:
        Dictionary containing faulty traffic lights data or None if error
    """
    api_key = os.getenv("LTA_API_KEY")
    
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    return fetch_url_2min_cached(FAULTY_TRAFFIC_LIGHTS_URL, headers)


def get_postal_code_from_coords(lat: float = None, lon: float = None, location_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Get postal code from location data (extracted from search value) or coordinates.
    Priority: location_data postal_code > location_data value field > reverse geocoding API.
    
    Args:
        lat: Latitude in degrees (optional, used as fallback)
        lon: Longitude in degrees (optional, used as fallback)
        location_data: Dictionary containing location data with optional 'postal_code' or 'value' field
    
    Returns:
        Postal code as string (6 digits), or empty string if not found
    """
    # First, try to extract from location_data postal_code field
    if location_data and isinstance(location_data, dict):
        postal_code = location_data.get('postal_code', '')
        if postal_code:
            # Ensure it's a 6-digit string
            postal_str = str(postal_code).strip()
            if len(postal_str) == 6 and postal_str.isdigit():
                return postal_str
    
    # Second, try to extract from location_data value field (format: lat,lon,address,postal)
    if location_data and isinstance(location_data, dict):
        value = location_data.get('value', '')
        if value:
            try:
                parts = value.split(',')
                if len(parts) > 3:
                    postal_code = parts[3].strip()
                    if len(postal_code) == 6 and postal_code.isdigit():
                        return postal_code
            except (ValueError, IndexError):
                pass
    
    # Fallback: Use reverse geocoding API if coordinates are provided
    if lat is not None and lon is not None:
        import requests
        try:
            # OneMap reverse geocoding API
            url = f"https://www.onemap.gov.sg/api/public/revgeocode?latitude={lat}&longitude={lon}"
            
            api_token = os.getenv("ONEMAP_API_KEY")
            headers = {}
            if api_token:
                headers["Authorization"] = api_token
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if results:
                    # Get postal code from first result
                    postal_code = results[0].get('POSTAL_CODE', '')
                    return postal_code
        except Exception as e:
            print(f"Error getting postal code from coordinates: {e}")
    
    return ""


def fetch_ev_charging_points(postal_code: str):
    """
    Fetch EV charging points data from LTA DataMall API using postal code.
    
    Args:
        postal_code: Postal code as string
    
    Returns:
        Dictionary containing EV charging points data or None if error
    """
    import requests
    if not postal_code:
        return None
    
    api_key = os.getenv("LTA_API_KEY")
    
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    params = {
        "PostalCode": postal_code
    }
    
    print(f"EV Charging Points API Request:")
    print(f"  URL: {EV_CHARGING_URL}")
    print(f"  Parameters: {params}")
    
    try:
        response = requests.get(EV_CHARGING_URL, headers=headers, params=params, timeout=10)
        print(f"  Response Status Code: {response.status_code}")
        
        if 200 <= response.status_code < 300:
            data = response.json()
            print(f"  Response JSON: {data}")
            
            # Print summary information
            if isinstance(data, dict):
                value_data = data.get('value', {})
                if isinstance(value_data, dict):
                    ev_list = value_data.get('evLocationsData', [])
                    print(f"  Number of locations found: {len(ev_list)}")
                    if ev_list:
                        print(f"  First charging point sample: {ev_list[0]}")
                else:
                    print(f"  Warning: 'value' is not a dictionary, type: {type(value_data)}")
            else:
                print(f"  Warning: Response is not a dictionary, type: {type(data)}")
            
            return data
        else:
            print(f"  Response Text: {response.text}")
        print(f"EV charging API request failed: status={response.status_code}")
    except (requests.exceptions.RequestException, ValueError) as error:
        print(f"Error fetching EV charging points data: {error}")
        import traceback
        traceback.print_exc()
    return None


def create_ev_charging_markers(ev_data):
    """
    Create map markers for EV charging point locations.
    
    Args:
        ev_data: Dictionary containing EV charging points response from LTA API
    
    Returns:
        List of dl.CircleMarker components
    """
    markers = []
    
    # Ensure ev_data is a dictionary
    if not ev_data or not isinstance(ev_data, dict):
        return markers
    
    if 'value' not in ev_data:
        return markers
    
    value_data = ev_data.get('value', {})
    if not isinstance(value_data, dict):
        return markers
        
    locations = value_data.get('evLocationsData', [])
    
    # Ensure locations is a list
    if not isinstance(locations, list):
        return markers
    
    for loc in locations:
        try:
            # Ensure loc is a dictionary
            if not isinstance(loc, dict):
                continue
                
            # Handle both TitleCase and lowercase keys as the API or data format might vary
            lat = float(loc.get('latitude') or loc.get('Latitude', 0))
            lon = float(loc.get('longitude') or loc.get('Longitude', 0))
            address = loc.get('address') or loc.get('Address', 'N/A')
            
            if lat == 0 or lon == 0:
                continue
            
            # Build tooltip content
            tooltip_content = []
            tooltip_content.append(html.B(f"Address: {address}"))
            tooltip_content.append(html.Br())
            
            charging_points = loc.get('chargingPoints', [])
            if not isinstance(charging_points, list):
                charging_points = []
                
            if not charging_points:
                loc_status = loc.get('status') or loc.get('Status', 'N/A')
                tooltip_content.append(f"Status: {loc_status}")
            else:
                for i, cp in enumerate(charging_points):
                    if i > 0:
                        tooltip_content.append(html.Hr(style={"margin": "5px 0"}))
                        
                    cp_status_raw = cp.get('status') or cp.get('Status', '')
                    if cp_status_raw == '1':
                        cp_status = "Available"
                    elif cp_status_raw == '0':
                        cp_status = "Occupied"
                    else:
                        cp_status = cp_status_raw or "N/A"
                        
                    operator = cp.get('operator') or cp.get('Operator', 'N/A')
                    position = cp.get('position') or cp.get('Position', 'N/A')
                    
                    plug_types = cp.get('plugTypes', [])
                    if isinstance(plug_types, list) and plug_types:
                        for j, pt in enumerate(plug_types):
                            if j > 0:
                                tooltip_content.append(html.Br())
                                tooltip_content.append("---")
                                tooltip_content.append(html.Br())
                            
                            plug_type = pt.get('plugType') or pt.get('PlugType', 'N/A')
                            power_rating = pt.get('powerRating') or pt.get('PowerRating', 'N/A')
                            speed = pt.get('chargingSpeed') or pt.get('ChargingSpeed', 'N/A')
                            price = pt.get('price') or pt.get('Price', 'N/A')
                            price_type = pt.get('priceType') or pt.get('PriceType', '')
                            
                            tooltip_content.extend([
                                f"Status: {cp_status}", html.Br(),
                                f"Operator: {operator}", html.Br(),
                                f"Position: {position}", html.Br(),
                                f"PlugType (rating): {plug_type}({power_rating})", html.Br(),
                                f"ChargingSpeed: {speed}", html.Br(),
                                f"Price: {price}{price_type}"
                            ])
                    else:
                        tooltip_content.extend([
                            f"Status: {cp_status}", html.Br(),
                            f"Operator: {operator}", html.Br(),
                            f"Position: {position}"
                        ])

            # Create EV charger icon SVG
            ev_charger_svg = (
                '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                '<rect x="4" y="6" width="16" height="12" rx="2" fill="#00BFFF" opacity="0.9" stroke="#0066CC" stroke-width="1.5"/>'
                '<circle cx="8" cy="12" r="1.5" fill="#fff"/>'
                '<circle cx="16" cy="12" r="1.5" fill="#fff"/>'
                '<path d="M 6 2 L 6 6 M 18 2 L 18 6" stroke="#00BFFF" stroke-width="2" stroke-linecap="round"/>'
                '<path d="M 10 18 L 10 20 M 14 18 L 14 20" stroke="#00BFFF" stroke-width="2" stroke-linecap="round"/>'
                '<path d="M 12 20 L 12 22" stroke="#00BFFF" stroke-width="2" stroke-linecap="round"/>'
                '</svg>'
            )
            ev_charger_svg_base64 = base64.b64encode(ev_charger_svg.encode()).decode()
            
            ev_charger_icon = {
                "iconUrl": f"data:image/svg+xml;base64,{ev_charger_svg_base64}",
                "iconSize": [24, 24],
                "iconAnchor": [12, 24],
                "popupAnchor": [0, -24],
            }
            
            # Create marker with EV charger icon
            markers.append(
                dl.Marker(
                    position=[lat, lon],
                    icon=ev_charger_icon,
                    children=[
                        dl.Tooltip(html.Div(tooltip_content, style={"fontSize": "11px", "maxWidth": "250px"})),
                    ]
                )
            )
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            print(f"Error processing EV charging point: {e}, loc type: {type(loc)}")
            continue
    
    return markers


def create_traffic_incidents_markers(incidents_data, faulty_lights_data=None):
    """
    Create map markers for traffic incidents and faulty traffic lights.
    
    Args:
        incidents_data: Dictionary containing traffic incidents response from LTA API
        faulty_lights_data: Optional dictionary containing faulty traffic lights response
    
    Returns:
        List of dl.CircleMarker components
    """
    markers = []
    
    # Extract incidents
    incidents = []
    if incidents_data:
        if isinstance(incidents_data, dict):
            if 'value' in incidents_data:
                incidents = incidents_data.get('value', [])
            elif isinstance(incidents_data, list):
                incidents = incidents_data
        elif isinstance(incidents_data, list):
            incidents = incidents_data
    
    # Create markers for traffic incidents
    for incident in incidents:
        if not isinstance(incident, dict):
            continue
        
        try:
            # Try different possible keys for coordinates
            latitude = (
                float(incident.get('Latitude', 0)) or
                float(incident.get('latitude', 0)) or
                float(incident.get('Lat', 0)) or
                float(incident.get('lat', 0)) or
                0
            )
            longitude = (
                float(incident.get('Longitude', 0)) or
                float(incident.get('longitude', 0)) or
                float(incident.get('Lon', 0)) or
                float(incident.get('lon', 0)) or
                0
            )
            
            if latitude == 0 or longitude == 0:
                continue
            
            # Get incident message - prioritize Message field for full details
            incident_message = (
                incident.get('Message') or
                incident.get('message') or
                incident.get('Type') or
                incident.get('type') or
                incident.get('IncidentType') or
                incident.get('incidentType') or
                'Unknown Incident'
            )
            
            # Create tooltip with full incident message
            tooltip_html = f"🚦 {incident_message}"
            
            # Categorize incident type based on message content
            incident_message_lower = str(incident_message).lower()
            
            # Determine incident category
            is_road_block = (
                'road block' in incident_message_lower or
                'roadblock' in incident_message_lower or
                'blocked' in incident_message_lower or
                'closure' in incident_message_lower or
                'closed' in incident_message_lower
            )
            
            is_road_work = (
                'road work' in incident_message_lower or
                'roadwork' in incident_message_lower or
                'construction' in incident_message_lower or
                'maintenance' in incident_message_lower or
                'repair' in incident_message_lower
            )
            
            is_accident_breakdown = (
                'accident' in incident_message_lower or
                'breakdown' in incident_message_lower or
                'vehicle' in incident_message_lower or
                'collision' in incident_message_lower or
                'crash' in incident_message_lower
            )
            
            # Create appropriate icon based on category
            if is_road_block:
                # Road block icon - red barrier with X (road closure)
                road_block_svg = (
                    '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                    '<rect x="2" y="2" width="20" height="20" fill="#DC2626" stroke="#991B1B" stroke-width="2" rx="2"/>'
                    '<line x1="6" y1="6" x2="18" y2="18" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>'
                    '<line x1="18" y1="6" x2="6" y2="18" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>'
                    '<rect x="4" y="4" width="16" height="16" fill="none" stroke="#FFFFFF" stroke-width="1.5" rx="1"/>'
                    '</svg>'
                )
                icon_svg_base64 = base64.b64encode(road_block_svg.encode()).decode()
                icon_size = [24, 24]
                icon_anchor = [12, 24]
                popup_anchor = [0, -24]
                
            elif is_road_work:
                # Road work icon - orange/yellow striped construction cone
                road_work_svg = (
                    '<svg width="20" height="28" viewBox="0 0 20 28" xmlns="http://www.w3.org/2000/svg">'
                    '<path d="M 10 2 L 18 26 L 2 26 Z" fill="#F97316" stroke="#EA580C" stroke-width="1.5"/>'
                    '<path d="M 10 6 L 16 24 L 4 24 Z" fill="#FB923C"/>'
                    '<rect x="6" y="10" width="8" height="2" fill="#FFFFFF" rx="1"/>'
                    '<rect x="6" y="14" width="8" height="2" fill="#FFFFFF" rx="1"/>'
                    '<rect x="6" y="18" width="8" height="2" fill="#FFFFFF" rx="1"/>'
                    '<circle cx="10" cy="28" r="2" fill="#1F2937"/>'
                    '</svg>'
                )
                icon_svg_base64 = base64.b64encode(road_work_svg.encode()).decode()
                icon_size = [20, 28]
                icon_anchor = [10, 28]
                popup_anchor = [0, -28]
                
            elif is_accident_breakdown:
                # Accident/breakdown icon - red car crash with exclamation
                accident_svg = (
                    '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                    '<circle cx="12" cy="12" r="11" fill="#EF4444" stroke="#DC2626" stroke-width="2"/>'
                    '<path d="M 6 14 L 6 18 L 18 18 L 18 14 L 15 10 L 9 10 Z" fill="#FFFFFF" stroke="#1F2937" stroke-width="1.5"/>'
                    '<circle cx="9" cy="18" r="2" fill="#1F2937"/>'
                    '<circle cx="15" cy="18" r="2" fill="#1F2937"/>'
                    '<path d="M 8 10 L 9 7 L 15 7 L 16 10" fill="#FEF3C7" stroke="#1F2937" stroke-width="1"/>'
                    '<line x1="12" y1="7" x2="12" y2="10" stroke="#DC2626" stroke-width="2" stroke-linecap="round"/>'
                    '<line x1="12" y1="5" x2="12" y2="3" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>'
                    '<circle cx="12" cy="2" r="1" fill="#FFFFFF"/>'
                    '</svg>'
                )
                icon_svg_base64 = base64.b64encode(accident_svg.encode()).decode()
                icon_size = [24, 24]
                icon_anchor = [12, 24]
                popup_anchor = [0, -24]
                
            else:
                # Other incidents - yellow warning triangle with exclamation
                other_svg = (
                    '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                    '<path d="M 12 2 L 22 20 L 2 20 Z" fill="#FCD34D" stroke="#F59E0B" stroke-width="2"/>'
                    '<path d="M 12 6 L 12 14" stroke="#92400E" stroke-width="2.5" stroke-linecap="round"/>'
                    '<circle cx="12" cy="17" r="1.5" fill="#92400E"/>'
                    '</svg>'
                )
                icon_svg_base64 = base64.b64encode(other_svg.encode()).decode()
                icon_size = [24, 24]
                icon_anchor = [12, 24]
                popup_anchor = [0, -24]
            
            incident_icon = {
                "iconUrl": f"data:image/svg+xml;base64,{icon_svg_base64}",
                "iconSize": icon_size,
                "iconAnchor": icon_anchor,
                "popupAnchor": popup_anchor,
            }
            
            markers.append(
                dl.Marker(
                    position=[latitude, longitude],
                    icon=incident_icon,
                    children=[
                        dl.Tooltip(tooltip_html),
                    ]
                )
            )
        except (ValueError, TypeError, KeyError):
            continue
    
    # Add faulty traffic lights if provided
    if faulty_lights_data:
        faulty_lights = []
        if isinstance(faulty_lights_data, dict):
            if 'value' in faulty_lights_data:
                faulty_lights = faulty_lights_data.get('value', [])
            elif isinstance(faulty_lights_data, list):
                faulty_lights = faulty_lights_data
        elif isinstance(faulty_lights_data, list):
            faulty_lights = faulty_lights_data
        
        for light in faulty_lights:
            if not isinstance(light, dict):
                continue
            
            try:
                latitude = (
                    float(light.get('Latitude', 0)) or
                    float(light.get('latitude', 0)) or
                    float(light.get('Lat', 0)) or
                    float(light.get('lat', 0)) or
                    0
                )
                longitude = (
                    float(light.get('Longitude', 0)) or
                    float(light.get('longitude', 0)) or
                    float(light.get('Lon', 0)) or
                    float(light.get('lon', 0)) or
                    0
                )
                
                if latitude == 0 or longitude == 0:
                    continue
                
                node_id = (
                    light.get('NodeID') or
                    light.get('nodeID') or
                    light.get('node_id') or
                    'N/A'
                )
                
                tooltip_html = f"🚦 Faulty Traffic Light Node ID: {node_id}"
                
                # Use traffic light icon for faulty traffic lights
                faulty_light_svg = (
                    '<svg width="20" height="24" viewBox="0 0 20 24" xmlns="http://www.w3.org/2000/svg">'
                    '<rect x="6" y="2" width="8" height="18" fill="#1F2937" stroke="#374151" stroke-width="1.5" rx="1"/>'
                    '<circle cx="10" cy="7" r="2.5" fill="#EF4444"/>'
                    '<circle cx="10" cy="12" r="2.5" fill="#FCD34D"/>'
                    '<circle cx="10" cy="17" r="2.5" fill="#10B981" fill-opacity="0.3"/>'
                    '<rect x="8" y="20" width="4" height="2" fill="#1F2937" rx="0.5"/>'
                    '<line x1="10" y1="7" x2="10" y2="7" stroke="#FFFFFF" stroke-width="1" stroke-linecap="round"/>'
                    '<line x1="10" y1="12" x2="10" y2="12" stroke="#FFFFFF" stroke-width="1" stroke-linecap="round"/>'
                    '</svg>'
                )
                icon_svg_base64 = base64.b64encode(faulty_light_svg.encode()).decode()
                icon_size = [20, 24]
                icon_anchor = [10, 24]
                popup_anchor = [0, -24]
                
                faulty_light_icon = {
                    "iconUrl": f"data:image/svg+xml;base64,{icon_svg_base64}",
                    "iconSize": icon_size,
                    "iconAnchor": icon_anchor,
                    "popupAnchor": popup_anchor,
                }
                
                markers.append(
                    dl.Marker(
                        position=[latitude, longitude],
                        icon=faulty_light_icon,
                        children=[
                            dl.Tooltip(tooltip_html),
                        ]
                    )
                )
            except (ValueError, TypeError, KeyError):
                continue
    
    return markers


def format_traffic_incidents_count_display(incidents_data, faulty_lights_data=None):
    """
    Format the traffic incidents count display.
    
    Args:
        incidents_data: Dictionary containing traffic incidents response from LTA API
        faulty_lights_data: Optional dictionary containing faulty traffic lights response
    
    Returns:
        HTML Div with traffic incidents count information
    """
    # Extract incidents
    incidents = []
    if incidents_data:
        if isinstance(incidents_data, dict):
            if 'value' in incidents_data:
                incidents = incidents_data.get('value', [])
            elif isinstance(incidents_data, list):
                incidents = incidents_data
        elif isinstance(incidents_data, list):
            incidents = incidents_data
    
    # Count incidents by type
    incident_counts = {}
    for incident in incidents:
        if isinstance(incident, dict):
            incident_type = (
                incident.get('Type') or
                incident.get('type') or
                incident.get('Message') or
                incident.get('message') or
                incident.get('IncidentType') or
                incident.get('incidentType') or
                'Unknown'
            )
            incident_counts[incident_type] = incident_counts.get(incident_type, 0) + 1
    
    # Count faulty traffic lights
    faulty_lights_count = 0
    if faulty_lights_data:
        faulty_lights = []
        if isinstance(faulty_lights_data, dict):
            if 'value' in faulty_lights_data:
                faulty_lights = faulty_lights_data.get('value', [])
            elif isinstance(faulty_lights_data, list):
                faulty_lights = faulty_lights_data
        elif isinstance(faulty_lights_data, list):
            faulty_lights = faulty_lights_data
        
        # Count unique NodeID instances
        node_ids = set()
        for light in faulty_lights:
            if isinstance(light, dict):
                node_id = (
                    light.get('NodeID') or
                    light.get('nodeID') or
                    light.get('node_id') or
                    None
                )
                if node_id:
                    node_ids.add(str(node_id))
        faulty_lights_count = len(node_ids)
        if faulty_lights_count > 0:
            incident_counts['Faulty Traffic Lights'] = faulty_lights_count
    
    total_count = len(incidents) + faulty_lights_count
    
    if not incident_counts:
        return html.Div(
            [
                html.P(
                    "No traffic incidents reported",
                    style={
                        "color": "#999",
                        "textAlign": "center",
                        "padding": "0.625rem",
                        "fontSize": "0.875rem",
                        "fontWeight": "600",
                        "margin": "0",
                    }
                )
            ]
        )
    
    # Create display with incident types
    incident_items = []
    for incident_type, count in sorted(incident_counts.items()):
        incident_items.append(
            html.Div(
                [
                    html.Span(
                        incident_type,
                        style={
                            "color": "#fff",
                            "fontSize": "0.75rem",
                            "fontWeight": "600",
                        }
                    ),
                    html.Span(
                        f"{count}",
                        style={
                            "color": "#FF6B6B",
                            "fontSize": "0.875rem",
                            "fontWeight": "bold",
                            "marginLeft": "0.5rem",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "0.25rem 0",
                    "borderBottom": "0.0625rem solid #5a6a7a",
                }
            )
        )
    
    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "🚦",
                        style={"fontSize": "2rem", "marginRight": "0.625rem", "lineHeight": "1"}
                    ),
                    html.Span(
                        f"{total_count}",
                        style={
                            "fontSize": "2.5rem",
                            "fontWeight": "bold",
                            "color": "#FF6B6B",
                            "lineHeight": "1",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "marginBottom": "0.625rem",
                    "flexWrap": "wrap",
                }
            ),
            html.P(
                "Total Incidents",
                style={
                    "color": "#fff",
                    "textAlign": "center",
                    "fontSize": "0.875rem",
                    "fontWeight": "600",
                    "margin": "0 0 0.625rem 0",
                }
            ),
            html.Div(
                incident_items,
                style={
                    "overflowY": "auto",
                    "maxHeight": "200px",
                }
            ),
        ],
        style={
            "padding": "0.9375rem",
            "backgroundColor": "#2c3e50",
            "borderRadius": "0.5rem",
            "width": "100%",
            "boxSizing": "border-box",
            "overflow": "hidden",
        }
    )


def format_erp_count_display(gantry_data):
    """
    Format the ERP gantry count display.
    
    Args:
        gantry_data: List of gantry dictionaries
    
    Returns:
        HTML Div with gantry count information
    """
    if not gantry_data:
        return html.Div(
            [
                html.P(
                    "Error loading ERP gantry data",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                    }
                )
            ]
        )

    gantry_count = len(gantry_data)

    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "🚧",
                        style={"fontSize": "2rem", "marginRight": "0.625rem", "lineHeight": "1"}
                    ),
                    html.Span(
                        f"{gantry_count}",
                        style={
                            "fontSize": "2.5rem",
                            "fontWeight": "bold",
                            "color": "#FF6B6B",
                            "lineHeight": "1",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "marginBottom": "0.625rem",
                    "flexWrap": "wrap",
                }
            ),
            html.P(
                "ERP Gantries",
                style={
                    "color": "#fff",
                    "textAlign": "center",
                    "fontSize": "0.875rem",
                    "fontWeight": "600",
                    "margin": "0 0 0.625rem 0",
                }
            ),
            html.P(
                "Red lines show gantry locations",
                style={
                    "color": "#888",
                    "textAlign": "center",
                    "fontSize": "0.6875rem",
                    "fontStyle": "italic",
                    "margin": "0",
                }
            ),
        ],
        style={
            "padding": "0.9375rem",
            "backgroundColor": "#2c3e50",
            "borderRadius": "0.5rem",
            "width": "100%",
            "boxSizing": "border-box",
            "overflow": "hidden",
        }
    )


def fetch_nearby_taxi_stands(lat: float, lon: float, radius_m: int = 300) -> list:
    """
    Fetch nearby taxi stands data from LTA DataMall API within specified radius.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_m: Search radius in meters (default: 300)
    
    Returns:
        List of taxi stand dictionaries with distance information, sorted by distance
    """
    # Fetch all taxi stands data
    taxi_stands_data = fetch_taxi_stands_data()
    
    if not taxi_stands_data:
        return []
    
    # Extract taxi stands from response
    stands = []
    if isinstance(taxi_stands_data, dict):
        if "value" in taxi_stands_data:
            stands = taxi_stands_data.get("value", [])
        elif isinstance(taxi_stands_data, list):
            stands = taxi_stands_data
    elif isinstance(taxi_stands_data, list):
        stands = taxi_stands_data
    
    processed_results = []
    
    for stand in stands:
        try:
            stand_lat = float(stand.get('Latitude', 0))
            stand_lon = float(stand.get('Longitude', 0))
            
            if stand_lat == 0 or stand_lon == 0:
                continue
            
            # Calculate distance using haversine formula
            distance_m = _haversine_distance_m(lat, lon, stand_lat, stand_lon)
            
            # Only include stands within the specified radius
            if distance_m <= radius_m:
                processed_results.append({
                    'taxi_code': stand.get('TaxiCode', 'N/A'),
                    'name': stand.get('Name', 'N/A'),
                    'bfa': stand.get('Bfa', 'N/A'),
                    'ownership': stand.get('Ownership', 'N/A'),
                    'stand_type': stand.get('Type', 'N/A'),
                    'latitude': stand_lat,
                    'longitude': stand_lon,
                    'distance_m': distance_m,
                    'raw_data': stand
                })
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error processing taxi stand data: {e}")
            continue
    
    # Sort by distance (closest first)
    processed_results.sort(key=lambda x: x['distance_m'])
    
    return processed_results


def _get_label_letter(index):
    """Get label letter (A, B, C, D, E) for index."""
    labels = ['A', 'B', 'C', 'D', 'E']
    return labels[index] if index < len(labels) else str(index + 1)


def create_nearby_taxi_stands_markers(nearby_taxi_stands: list) -> list:
    """
    Create map markers for nearby taxi stands from processed list.

    Args:
        nearby_taxi_stands: List of taxi stand dictionaries returned by fetch_nearby_taxi_stands()

    Returns:
        List of dl.Marker components
    """
    if not nearby_taxi_stands:
        return []

    markers = []
    for idx, stand in enumerate(nearby_taxi_stands):
        try:
            lat = float(stand.get('latitude', 0))
            lon = float(stand.get('longitude', 0))
            if lat == 0 or lon == 0:
                continue

            taxi_code = stand.get('taxi_code', 'N/A')
            name = stand.get('name', 'N/A')
            stand_type = stand.get('stand_type', 'N/A')
            ownership = stand.get('ownership', 'N/A')
            bfa = stand.get('bfa', 'N/A')
            distance_m = float(stand.get('distance_m', 0))
            distance_str = f"{int(distance_m)}m" if distance_m < 1000 else f"{distance_m/1000:.2f}km"

            # Get label letter (A, B, C, D, E)
            label = _get_label_letter(idx)

            tooltip_text = (
                f"• Taxi Stand: {taxi_code} ({name})\n"
                f"• Distance: {distance_str}\n"
                f"• Type: {stand_type}\n"
                f"• Ownership: {ownership}\n"
                f"• BFA: {bfa}"
            )

            # Create marker HTML with taxi icon and label badge (similar to bus stops)
            marker_html = (
                f'<div style="width:32px;height:32px;background:#FFA500;'
                f'border-radius:50%;border:3px solid #fff;'
                f'box-shadow:0 2px 8px rgba(255,165,0,0.6);'
                f'cursor:pointer;display:flex;align-items:center;'
                f'justify-content:center;font-size:14px;color:#fff;'
                f'font-weight:bold;position:relative;">'
                f'<span style="font-size:16px;">🚕</span>'
                f'<div style="position:absolute;top:-8px;right:-8px;'
                f'background:#FF5722;color:#fff;width:20px;height:20px;'
                f'border-radius:50%;border:2px solid #fff;'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:12px;font-weight:bold;">{label}</div>'
                f'</div>'
            )
            
            marker_id = f"taxi-stand-nearby-{taxi_code}-{lat}-{lon}"
            
            markers.append(
                dl.DivMarker(
                    id=marker_id,
                    position=[lat, lon],
                    iconOptions={
                        'className': 'taxi-stand-pin',
                        'html': marker_html,
                        'iconSize': [60, 40],
                        'iconAnchor': [30, 40],
                    },
                    children=[dl.Tooltip(html.Pre(tooltip_text, style={"margin": "0", "fontFamily": "inherit"}))]
                )
            )
        except (ValueError, TypeError):
            continue

    return markers


def register_transport_callbacks(app):
    """
    Register callbacks for transport information.
    
    Args:
        app: Dash app instance
    """
    
    @app.callback(
        [Output('taxi-toggle-state', 'data'),
         Output('taxi-toggle-btn', 'style'),
         Output('taxi-toggle-btn', 'children')],
        Input('taxi-toggle-btn', 'n_clicks'),
        State('taxi-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_taxi_display(_n_clicks, current_state):
        """Toggle taxi markers display on/off."""
        new_state = not current_state
        
        if new_state:
            # Active state - yellow background
            style = {
                "backgroundColor": "#FFD700",
                "border": "none",
                "borderRadius": "0.25rem",
                "color": "#000",
                "cursor": "pointer",
                "padding": "0.375rem 0.75rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Hide Current Taxi Availability/Stands"
        else:
            # Inactive state - outline
            style = {
                "backgroundColor": "transparent",
                "border": "0.125rem solid #FFD700",
                "borderRadius": "0.25rem",
                "color": "#FFD700",
                "cursor": "pointer",
                "padding": "0.25rem 0.625rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Show Current Taxi Availability/Stands"
        
        return new_state, style, text
    
    @app.callback(
        [Output('taxi-markers', 'children'),
         Output('taxi-count-value', 'children'),
         Output('taxi-legend', 'style')],
        [Input('taxi-toggle-state', 'data'),
         Input('transport-interval', 'n_intervals')]
    )
    def update_taxi_display(show_taxis, n_intervals):
        """Update taxi locations and stands markers and count display."""
        _ = n_intervals  # Used for periodic refresh
        
        # Always fetch data to display counts
        taxi_data = fetch_taxi_availability()
        taxi_stands_data = fetch_taxi_stands_data()
        
        # Extract count values (always calculate)
        taxi_count = 0
        if taxi_data and 'features' in taxi_data:
            features = taxi_data.get('features', [])
            if features:
                first_feature = features[0]
                properties = first_feature.get('properties', {})
                taxi_count = properties.get('taxi_count', 0)
        
        stands_count = 0
        if taxi_stands_data:
            stands = []
            if isinstance(taxi_stands_data, dict):
                if "value" in taxi_stands_data:
                    stands = taxi_stands_data.get("value", [])
                elif isinstance(taxi_stands_data, list):
                    stands = taxi_stands_data
            elif isinstance(taxi_stands_data, list):
                stands = taxi_stands_data
            stands_count = len(stands)
        
        # Format as "taxi/taxi stands"
        count_value = html.Div(
            html.Span(f"{taxi_count:,}/{stands_count}", style={"color": "#FFD700"}),
                style={
                "backgroundColor": "rgb(58, 74, 90)",
                "padding": "0.25rem 0.5rem",
                "borderRadius": "0.25rem",
            }
        )
        
        # Legend style - show when toggle is on
        legend_style = {
            "position": "absolute",
            "top": "0.625rem",
            "right": "0.625rem",
            "backgroundColor": "rgba(26, 42, 58, 0.9)",
            "borderRadius": "0.5rem",
            "padding": "0.625rem",
            "zIndex": "1000",
            "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
            "display": "block" if show_taxis else "none",
        }
        
        # Only show markers if toggle is on
        if not show_taxis:
            return [], count_value, legend_style
        
        # Create markers for both
        taxi_markers = create_taxi_markers(taxi_data)
        taxi_stands_markers = create_taxi_stands_markers(taxi_stands_data)
        
        # Combine all markers
        all_markers = taxi_markers + taxi_stands_markers
        
        return all_markers, count_value, legend_style

    @app.callback(
        [Output('cctv-toggle-state', 'data'),
         Output('cctv-toggle-btn', 'style'),
         Output('cctv-toggle-btn', 'children')],
        Input('cctv-toggle-btn', 'n_clicks'),
        State('cctv-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_cctv_display(_n_clicks, current_state):
        """Toggle CCTV markers display on/off."""
        new_state = not current_state
        
        if new_state:
            # Active state - green background
            style = {
                "backgroundColor": "#4CAF50",
                "border": "none",
                "borderRadius": "0.25rem",
                "color": "#fff",
                "cursor": "pointer",
                "padding": "0.375rem 0.75rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Hide LTA Traffic Cameras Location"
        else:
            # Inactive state - outline
            style = {
                "backgroundColor": "transparent",
                "border": "0.125rem solid #4CAF50",
                "borderRadius": "0.25rem",
                "color": "#4CAF50",
                "cursor": "pointer",
                "padding": "0.25rem 0.625rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Show LTA Traffic Cameras Location"
        
        return new_state, style, text

    @app.callback(
        [Output('cctv-markers', 'children'),
         Output('cctv-count-value', 'children')],
        [Input('cctv-toggle-state', 'data'),
         Input('transport-interval', 'n_intervals')]
    )
    def update_cctv_display(show_cctv, n_intervals):
        """Update CCTV markers and count display."""
        _ = n_intervals  # Used for periodic refresh
        
        # Always fetch data to display counts
        data = fetch_traffic_cameras()
        camera_data = parse_traffic_camera_data(data)
        
        # Extract count (always calculate)
        camera_count = len(camera_data) if camera_data else 0
        count_value = html.Div(
            html.Span(f"{camera_count}", style={"color": "#4CAF50"}),
                style={
                "backgroundColor": "rgb(58, 74, 90)",
                "padding": "0.25rem 0.5rem",
                "borderRadius": "0.25rem",
            }
        )
        
        # Only show markers if toggle is on
        if not show_cctv:
            return [], count_value
        
        # Create markers
        markers = create_cctv_markers(camera_data)
        
        return markers, count_value

    @app.callback(
        [Output('erp-toggle-state', 'data'),
         Output('erp-toggle-btn', 'style'),
         Output('erp-toggle-btn', 'children')],
        Input('erp-toggle-btn', 'n_clicks'),
        State('erp-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_erp_display(_n_clicks, current_state):
        """Toggle ERP gantry markers display on/off."""
        new_state = not current_state

        if new_state:
            # Active state - red background
            style = {
                "backgroundColor": "#FF6B6B",
                "border": "none",
                "borderRadius": "0.25rem",
                "color": "#fff",
                "cursor": "pointer",
                "padding": "0.375rem 0.75rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Hide ERP Gantries Location"
        else:
            # Inactive state - outline
            style = {
                "backgroundColor": "transparent",
                "border": "0.125rem solid #FF6B6B",
                "borderRadius": "0.25rem",
                "color": "#FF6B6B",
                "cursor": "pointer",
                "padding": "0.25rem 0.625rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Show ERP Gantries Location"

        return new_state, style, text

    @app.callback(
        [Output('erp-markers', 'children'),
         Output('erp-count-value', 'children')],
        [Input('erp-toggle-state', 'data'),
         Input('transport-interval', 'n_intervals')]
    )
    def update_erp_display(show_erp, n_intervals):
        """Update ERP gantry markers and count display."""
        _ = n_intervals  # Used for periodic refresh

        # Get parsed gantry data (uses cache)
        gantry_data = get_erp_gantry_data()
        
        # Extract count (always calculate)
        gantry_count = len(gantry_data) if gantry_data else 0
        count_value = html.Div(
            html.Span(f"{gantry_count}", style={"color": "#FF6B6B"}),
                style={
                "backgroundColor": "rgb(58, 74, 90)",
                "padding": "0.25rem 0.5rem",
                "borderRadius": "0.25rem",
            }
        )

        # Only show markers if toggle is on
        if not show_erp:
            return [], count_value

        # Create markers
        markers = create_erp_gantry_markers(gantry_data)

        return markers, count_value

    @app.callback(
        [Output('traffic-incidents-toggle-state', 'data'),
         Output('traffic-incidents-toggle-btn', 'style'),
         Output('traffic-incidents-toggle-btn', 'children')],
        Input('traffic-incidents-toggle-btn', 'n_clicks'),
        State('traffic-incidents-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_traffic_incidents_display(_n_clicks, current_state):
        """Toggle Traffic Incidents markers display on/off."""
        new_state = not current_state

        if new_state:
            # Active state - orange background
            style = {
                "backgroundColor": "#FF9800",
                "border": "none",
                "borderRadius": "0.25rem",
                "color": "#fff",
                "cursor": "pointer",
                "padding": "0.375rem 0.75rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Hide Traffic Incidents"
        else:
            # Inactive state - outline
            style = {
                "backgroundColor": "transparent",
                "border": "0.125rem solid #FF9800",
                "borderRadius": "0.25rem",
                "color": "#FF9800",
                "cursor": "pointer",
                "padding": "0.25rem 0.625rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Show Traffic Incidents"

        return new_state, style, text

    @app.callback(
        [Output('traffic-incidents-markers', 'children'),
         Output('traffic-incidents-count-value', 'children'),
         Output('traffic-incidents-messages', 'children'),
         Output('traffic-incidents-messages', 'style'),
         Output('traffic-incidents-legend', 'style')],
        [Input('traffic-incidents-toggle-state', 'data'),
         Input('transport-interval', 'n_intervals')]
    )
    def update_traffic_incidents_display(show_incidents, n_intervals):
        """Update Traffic Incidents markers and count display."""
        _ = n_intervals  # Used for periodic refresh

        # Always fetch data to display counts
        incidents_data = fetch_traffic_incidents_data()
        faulty_lights_data = fetch_faulty_traffic_lights_data()
        
        # Extract count (always calculate)
        incidents = []
        if isinstance(incidents_data, dict):
            if "value" in incidents_data:
                incidents = incidents_data.get("value", [])
            elif isinstance(incidents_data, list):
                incidents = incidents_data
        elif isinstance(incidents_data, list):
            incidents = incidents_data
        
        faulty_lights = []
        if faulty_lights_data:
            if isinstance(faulty_lights_data, dict):
                if "value" in faulty_lights_data:
                    faulty_lights = faulty_lights_data.get("value", [])
                elif isinstance(faulty_lights_data, list):
                    faulty_lights = faulty_lights_data
            elif isinstance(faulty_lights_data, list):
                faulty_lights = faulty_lights_data
        
        total_count = len(incidents) + len(faulty_lights)
        count_value = html.Div(
            html.Span(f"{total_count}", style={"color": "#FF9800"}),
            style={
                "backgroundColor": "rgb(58, 74, 90)",
                "padding": "0.25rem 0.5rem",
                "borderRadius": "0.25rem",
            }
        )

        # Collect all incident messages
        message_items = []
        for incident in incidents:
            if not isinstance(incident, dict):
                continue
            incident_message = (
                incident.get('Message') or
                incident.get('message') or
                incident.get('Type') or
                incident.get('type') or
                incident.get('IncidentType') or
                incident.get('incidentType') or
                'Unknown Incident'
            )
            message_items.append(
                html.Div(
                    html.Span(
                        f"• {incident_message}",
                        style={
                            "color": "#ccc",
                            "fontSize": "0.6875rem",
                            "lineHeight": "1.4",
                        }
                    ),
                    style={
                        "padding": "4px 0",
                        "borderBottom": "1px solid rgba(255, 255, 255, 0.1)",
                    }
                )
            )
        
        # Add faulty traffic lights messages
        for light in faulty_lights:
            if not isinstance(light, dict):
                continue
            node_id = (
                light.get('NodeID') or
                light.get('nodeID') or
                light.get('node_id') or
                'N/A'
            )
            message_items.append(
                html.Div(
                    html.Span(
                        f"• Faulty Traffic Light (Node ID: {node_id})",
                        style={
                            "color": "#ccc",
                            "fontSize": "0.6875rem",
                            "lineHeight": "1.4",
                        }
                    ),
                    style={
                        "padding": "4px 0",
                        "borderBottom": "1px solid rgba(255, 255, 255, 0.1)",
                    }
                )
            )
        
        # Messages container
        if message_items:
            messages_display = html.Div(
                message_items,
                style={
                    "padding": "8px",
                    "backgroundColor": "rgb(58, 74, 90)",
                    "borderRadius": "0.25rem",
                }
            )
            messages_style = {
                "maxHeight": "150px",
                "overflowY": "auto",
                "display": "block",
            }
        else:
            messages_display = html.Div(
                html.Span(
                    "No incidents reported",
                style={
                    "color": "#999",
                        "fontSize": "11px",
                    "fontStyle": "italic",
                    }
                ),
                style={
                    "padding": "8px",
                    "textAlign": "center",
                }
            )
            messages_style = {
                "maxHeight": "150px",
                "overflowY": "auto",
                "display": "block",
            }

        # Legend style based on toggle state
        if show_incidents:
            legend_style = {
                "position": "absolute",
                "top": "0.625rem",
                "right": "0.625rem",
                "backgroundColor": "rgba(26, 42, 58, 0.9)",
                "borderRadius": "0.5rem",
                "padding": "0.625rem",
                "zIndex": "1000",
                "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
                "display": "block",
            }
        else:
            legend_style = {
                "position": "absolute",
                "top": "0.625rem",
                "right": "0.625rem",
                "backgroundColor": "rgba(26, 42, 58, 0.9)",
                "borderRadius": "0.5rem",
                "padding": "0.625rem",
                "zIndex": "1000",
                "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
                "display": "none",
            }

        # Only show markers if toggle is on
        if not show_incidents:
            return [], count_value, messages_display, messages_style, legend_style

        # Create markers
        markers = create_traffic_incidents_markers(incidents_data, faulty_lights_data)

        return markers, count_value, messages_display, messages_style, legend_style

    # Callback for nearby transport page - taxi stands (within 300m)
    @app.callback(
        [Output('nearby-transport-taxi-stand-column', 'children'),
         Output('nearby-taxi-stand-markers', 'children')],
        [Input('nearby-transport-map', 'viewport'),
         Input('nearby-transport-location-store', 'data')]
    )
    def update_nearby_transport_taxi_stands(viewport, location_data):
        """
        Update taxi stands display for nearby transport page based on selected location.
        Shows taxi stands within 300m of the selected location.
        """
        # Prefer viewport center (so panning/zooming updates nearby results)
        center = None
        if isinstance(viewport, dict):
            center = viewport.get('center')

        if isinstance(center, (list, tuple)) and len(center) == 2:
            center_lat, center_lon = center[0], center[1]
        else:
            if not location_data:
                return [
                    html.H4(
                        "Nearby 300m Taxi Stands",
                        style={
                            "textAlign": "center",
                            "marginBottom": "0.625rem",
                            "color": "#fff",
                            "fontWeight": "700",
                            "fontSize": "0.875rem"
                        }
                    ),
                    html.P(
                        "Select a location to view nearest taxi stands",
                        style={
                            "textAlign": "center",
                            "padding": "0.9375rem",
                            "color": "#999",
                            "fontSize": "0.75rem",
                            "fontStyle": "italic"
                        }
                    )
                ], []

            try:
                center_lat = float(location_data.get('lat'))
                center_lon = float(location_data.get('lon'))
            except (ValueError, TypeError, KeyError, AttributeError):
                return [
                    html.H4(
                        "Nearby 300m Taxi Stands",
                        style={
                            "textAlign": "center",
                            "marginBottom": "0.625rem",
                            "color": "#fff",
                            "fontWeight": "700",
                            "fontSize": "0.875rem"
                        }
                    ),
                    html.Div(
                        "Invalid coordinates",
                        style={
                            "padding": "0.625rem",
                            "color": "#ff6b6b",
                            "fontSize": "0.75rem",
                            "textAlign": "center"
                        }
                    )
                ], []

        print(f"Searching for taxi stands near ({center_lat}, {center_lon}) within 300m (viewport-driven)")
        nearby_stands = fetch_nearby_taxi_stands(center_lat, center_lon, radius_m=300)
        print(f"Found {len(nearby_stands)} taxi stands within 300m")

        if not nearby_stands:
            return [
                html.H4(
                    "Nearby 300m Taxi Stands",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "No taxi stands found within 300m",
                    style={
                        "textAlign": "center",
                        "padding": "0.9375rem",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic"
                    }
                )
            ], []

        markers = create_nearby_taxi_stands_markers(nearby_stands)

        stand_items = []
        for stand in nearby_stands:
            taxi_code = stand.get('taxi_code', 'N/A')
            name = stand.get('name', 'N/A')
            distance_m = stand.get('distance_m', 0)
            lat = stand.get('latitude', 0)
            lon = stand.get('longitude', 0)

            if distance_m < 1000:
                distance_str = f"{int(distance_m)}m"
            else:
                distance_str = f"{distance_m/1000:.2f}km"

            location_str = f"{lat:.6f}, {lon:.6f}" if lat and lon else "N/A"

            stand_items.append(
                html.Div(
                    [
                        html.Div(
                            f"{taxi_code} ({name})",
                            style={
                                "fontSize": "0.8125rem",
                                "color": "#fff",
                                "fontWeight": "600",
                                "marginBottom": "0.25rem"
                            }
                        ),
                        html.Div(
                            f"Distance: {distance_str}",
                            style={
                                "fontSize": "0.75rem",
                                "color": "#FFD700",
                                "fontWeight": "500",
                                "marginBottom": "2px"
                            }
                        ),
                        html.Div(
                            f"Location: {location_str}",
                            style={
                                "fontSize": "0.75rem",
                                "color": "#ccc",
                            }
                        )
                    ],
                    style={
                        "padding": "0.625rem 0.75rem",
                        "borderBottom": "0.0625rem solid #444",
                        "marginBottom": "0.375rem",
                        "backgroundColor": "#1a1a1a",
                        "borderRadius": "0.25rem"
                    }
                )
            )

        # Return stand items with H4 title
        output = [
            html.H4(
                "Nearby 300m Taxi Stands",
                style={
                    "textAlign": "center",
                    "marginBottom": "0.625rem",
                    "color": "#fff",
                    "fontWeight": "700",
                    "fontSize": "0.875rem"
                }
            ),
            *stand_items
        ]
        return output, markers

    # Callback for nearby transport page - bicycle parking
    @app.callback(
        [Output('nearby-transport-bicycle-column', 'children'),
         Output('nearby-bicycle-markers', 'children')],
        [Input('nearby-transport-map', 'viewport'),
         Input('nearby-transport-location-store', 'data')]
    )
    def update_nearby_transport_bicycle_parking(viewport, location_data):
        """
        Update bicycle parking display for nearby transport page based on selected location.
        Shows bicycle parking within 300m of the selected location.
        
        Args:
            viewport: Viewport information from map
            location_data: Dictionary containing {'lat': float, 'lon': float} of selected location
        
        Returns:
            HTML Div containing bicycle parking information and markers
        """
        from callbacks.bicycle_parking_helper import fetch_bicycle_parking_from_api, create_nearby_bicycle_parking_markers
        
        # Prefer viewport center (so panning/zooming updates nearby results)
        center = None
        if isinstance(viewport, dict):
            center = viewport.get('center')

        if isinstance(center, (list, tuple)) and len(center) == 2:
            center_lat, center_lon = center[0], center[1]
        else:
            if not location_data:
                return [
                    html.H4(
                        "Nearby 300m Bicycle Parking",
                        style={
                            "textAlign": "center",
                            "marginBottom": "0.625rem",
                            "color": "#fff",
                            "fontWeight": "700",
                            "fontSize": "0.875rem"
                        }
                    ),
                    html.P(
                        "Select a location to view nearest bicycle parking",
                        style={
                            "textAlign": "center",
                            "padding": "0.9375rem",
                            "color": "#999",
                            "fontSize": "0.75rem",
                            "fontStyle": "italic"
                        }
                    )
                ], []

            # Fallback to stored lat/lon (e.g., from search)
            try:
                center_lat = float(location_data.get('lat'))
                center_lon = float(location_data.get('lon'))
            except (ValueError, TypeError, KeyError, AttributeError):
                return [
                    html.H4(
                        "Nearby 300m Bicycle Parking",
                        style={
                            "textAlign": "center",
                            "marginBottom": "0.625rem",
                            "color": "#fff",
                            "fontWeight": "700",
                            "fontSize": "0.875rem"
                        }
                    ),
                    html.Div(
                        "Invalid coordinates",
                        style={
                            "padding": "0.625rem",
                            "color": "#ff6b6b",
                            "fontSize": "0.75rem",
                            "textAlign": "center"
                        }
                    )
                ], []

        # Fetch bicycle parking from API within 300m
        nearby_parking = fetch_bicycle_parking_from_api(center_lat, center_lon, dist_m=300, haversine_func=_haversine_distance_m)

        if not nearby_parking:
            return [
                html.H4(
                    "Nearby 300m Bicycle Parking",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "No bicycle parking found within 300m",
                    style={
                        "textAlign": "center",
                        "padding": "0.9375rem",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic"
                    }
                )
            ], []

        # Create markers for map
        markers = create_nearby_bicycle_parking_markers(nearby_parking)

        # Build display components for each nearby bicycle parking
        parking_items = []

        for parking in nearby_parking:
            description = parking.get('description', 'N/A')
            rack_type = parking.get('rack_type', 'N/A')
            rack_count = parking.get('rack_count', 'N/A')
            distance_m = parking.get('distance_m', 0)

            # Format distance display
            if distance_m < 1000:
                distance_str = f"{int(distance_m)}m"
            else:
                distance_str = f"{distance_m/1000:.2f}km"

            # Create card for each bicycle parking location
            parking_items.append(
                html.Div(
                    [
                        html.Div(
                            description,
                            style={
                                "fontSize": "0.8125rem",
                                "color": "#fff",
                                "fontWeight": "600",
                                "marginBottom": "0.25rem"
                            }
                        ),
                        html.Div(
                            f"RackType: {rack_type}",
                            style={
                                "fontSize": "0.75rem",
                                "color": "#ccc",
                                "marginBottom": "0.125rem"
                            }
                        ),
                        html.Div(
                            f"RackCount: {rack_count}",
                            style={
                                "fontSize": "0.75rem",
                                "color": "#ccc",
                                "marginBottom": "0.25rem"
                            }
                        ),
                        html.Div(
                            f"Distance: {distance_str}",
                            style={
                                "fontSize": "0.75rem",
                                "color": "#60a5fa",
                                "fontWeight": "500"
                            }
                        )
                    ],
                    style={
                        "padding": "0.625rem 0.75rem",
                        "borderBottom": "0.0625rem solid #444",
                        "marginBottom": "0.375rem",
                        "backgroundColor": "#1a1a1a",
                        "borderRadius": "0.25rem"
                    }
                )
            )

        # Return parking items with H4 title
        output = [
            html.H4(
                "Nearby 300m Bicycle Parking",
                style={
                    "textAlign": "center",
                    "marginBottom": "0.625rem",
                    "color": "#fff",
                    "fontWeight": "700",
                    "fontSize": "0.875rem"
                }
            ),
            *parking_items
        ]
        return output, markers

    # Callback for nearby transport page - EV charging points
    @app.callback(
        [Output('nearby-transport-ev-charging-column', 'children'),
         Output('nearby-ev-charging-markers', 'children')],
        Input('nearby-transport-location-store', 'data')
    )
    def update_nearby_transport_ev_charging(location_data):
        """
        Update EV charging points display for nearby transport page based on selected location.
        Uses postal code from the selected location to fetch EV charging points.
        
        Args:
            location_data: Dictionary containing {'lat': float, 'lon': float} of selected location
        
        Returns:
            HTML Div containing EV charging points information and markers
        """
        if not location_data:
            return [
                html.H4(
                    "Nearby EV Charging Points",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "Select a location to view nearby EV charging points",
                    style={
                        "textAlign": "center",
                        "padding": "0.9375rem",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic"
                    }
                )
            ], []

        try:
            center_lat = float(location_data.get('lat'))
            center_lon = float(location_data.get('lon'))
        except (ValueError, TypeError, KeyError):
            return [
                html.H4(
                    "Nearby EV Charging Points",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.Div(
                    "Invalid coordinates",
                    style={
                        "padding": "0.625rem",
                        "color": "#ff6b6b",
                        "fontSize": "0.75rem",
                        "textAlign": "center"
                    }
                )
            ], []

        # Get postal code from location_data (extracted from search value)
        postal_code = get_postal_code_from_coords(center_lat, center_lon, location_data)
        
        if not postal_code:
            return [
                html.H4(
                    "Nearby EV Charging Points",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "Unable to determine postal code for selected location",
                    style={
                        "textAlign": "center",
                        "padding": "0.9375rem",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic"
                    }
                )
            ], []

        # Fetch EV charging points using postal code
        print(f"Fetching EV charging points for postal code: {postal_code}")
        ev_data = fetch_ev_charging_points(postal_code)
        
        # Ensure ev_data is a dictionary
        if not ev_data or not isinstance(ev_data, dict) or 'value' not in ev_data:
            return [
                html.H4(
                    "Nearby EV Charging Points",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "No EV charging points found for this postal code",
                    style={
                        "textAlign": "center",
                        "padding": "0.9375rem",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic"
                    }
                )
            ], []

        value_data = ev_data.get('value', {})
        if not isinstance(value_data, dict):
            return [
                html.H4(
                    "Nearby EV Charging Points",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "No EV charging points found for this postal code",
                    style={
                        "textAlign": "center",
                        "padding": "0.9375rem",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic"
                    }
                )
            ], []

        locations = value_data.get('evLocationsData', [])
        
        # Ensure locations is a list
        if not isinstance(locations, list) or not locations:
            return [
                html.H4(
                    "Nearby EV Charging Points",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "No EV charging points found for this postal code",
                    style={
                        "textAlign": "center",
                        "padding": "0.9375rem",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic"
                    }
                )
            ], []

        # Create markers for map
        markers = create_ev_charging_markers(ev_data)

        # Build display components for each EV charging point
        charging_items = []

        for loc in locations:
            # Ensure loc is a dictionary
            if not isinstance(loc, dict):
                print(f"Skipping invalid location (not a dict): {loc}, type: {type(loc)}")
                continue
                
            address = loc.get('address') or loc.get('Address', 'N/A')
            
            # For the list display, we might want to show a summary or the first charging point
            charging_points = loc.get('chargingPoints', [])
            cp_details = []
            
            if isinstance(charging_points, list) and charging_points:
                for cp in charging_points:
                    cp_status_raw = cp.get('status') or cp.get('Status', '')
                    if cp_status_raw == '1':
                        cp_status = "Available"
                        cp_color = "#4CAF50"  # Green
                    elif cp_status_raw == '0':
                        cp_status = "Occupied"
                        cp_color = "#ff6b6b"  # Red
                    else:
                        cp_status = cp_status_raw or "N/A"
                        cp_color = "#999"  # Gray
                    
                    operator = cp.get('operator') or cp.get('Operator', 'N/A')
                    position = cp.get('position') or cp.get('Position', 'N/A')
                    
                    cp_details.append(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span(f"{cp_status}", style={"color": cp_color, "fontWeight": "bold"}),
                                        html.Span(f" | {operator}", style={"color": "#ccc", "fontSize": "0.7rem"}),
                                    ],
                                    style={"marginBottom": "2px"}
                                ),
                                html.Div(f"Pos: {position}", style={"color": "#aaa", "fontSize": "0.65rem"})
                            ],
                            style={"marginTop": "4px", "paddingLeft": "8px", "borderLeft": f"2px solid {cp_color}"}
                        )
                    )

            # Create card for each EV charging location
            charging_items.append(
                html.Div(
                    [
                        html.Div(
                            address,
                            style={
                                "fontSize": "0.8125rem",
                                "color": "#fff",
                                "fontWeight": "600",
                                "marginBottom": "0.25rem"
                            }
                        ),
                        html.Div(cp_details)
                    ],
                    style={
                        "padding": "0.625rem 0.75rem",
                        "borderBottom": "0.0625rem solid #444",
                        "marginBottom": "0.375rem",
                        "backgroundColor": "#1a1a1a",
                        "borderRadius": "0.25rem"
                    }
                )
            )

        # Return all charging items and markers
        # Return charging items with H4 title
        return [
            html.H4(
                "Nearby EV Charging Points",
                style={
                    "textAlign": "center",
                    "marginBottom": "0.625rem",
                    "color": "#fff",
                    "fontWeight": "700",
                    "fontSize": "0.875rem"
                }
            ),
            *charging_items
        ], markers

    # VMS (Variable Message Signs) callbacks
    @app.callback(
        [Output('vms-toggle-state', 'data'),
         Output('vms-toggle-btn', 'style'),
         Output('vms-toggle-btn', 'children')],
        Input('vms-toggle-btn', 'n_clicks'),
        State('vms-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_vms_display(_n_clicks: Optional[int], current_state: bool) -> Tuple[bool, Dict[str, Any], str]:
        """Toggle VMS markers display on/off."""
        new_state = not current_state
        
        if new_state:
            # Active state - silver background
            style = {
                "backgroundColor": "#C0C0C0",
                "border": "none",
                "borderRadius": "0.25rem",
                "color": "#000",
                "cursor": "pointer",
                "padding": "0.375rem 0.75rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Hide VMS Display boards Locations"
        else:
            # Inactive state - outline
            style = {
                "backgroundColor": "transparent",
                "border": "0.125rem solid #C0C0C0",
                "borderRadius": "0.25rem",
                "color": "#C0C0C0",
                "cursor": "pointer",
                "padding": "0.25rem 0.625rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Show VMS Display boards Locations"
        
        return new_state, style, text

    @app.callback(
        [Output('vms-markers', 'children'),
         Output('vms-count-value', 'children')],
        [Input('vms-toggle-state', 'data'),
         Input('transport-interval', 'n_intervals')]
    )
    def update_vms_display(show_vms: bool, n_intervals: int) -> Tuple[List[dl.CircleMarker], html.Div]:
        """Update VMS markers and count display."""
        _ = n_intervals  # Used for periodic refresh

        # Always fetch data to display counts (using async)
        future = fetch_vms_data_async()
        data: Optional[Dict[str, Any]] = future.result() if future else None
        
        # Extract count (always calculate)
        vms_count = 0
        if isinstance(data, dict):
            vms_locations = data.get('value', [])
            vms_count = len(vms_locations)
        
        count_value = html.Div(
            html.Span(f"{vms_count}", style={"color": "#C0C0C0"}),
            style={
                "backgroundColor": "rgb(58, 74, 90)",
                "padding": "0.25rem 0.5rem",
                "borderRadius": "0.25rem",
            }
        )

        # Only show markers if toggle is on
        if not show_vms:
            return [], count_value

        # Create markers
        markers = create_vms_markers(data)

        return markers, count_value

    @app.callback(
        [Output('bus-stops-markers', 'children'),
         Output('bus-stops-count-value', 'children'),
         Output('bus-stop-zoom-message', 'style'),
         Output('bus-stop-zoom-message', 'children'),
         Output('bus-stops-disclaimer', 'style')],
        [Input('bus-stops-toggle-state', 'data'),
         Input('transport-map', 'zoom'),
         Input('transport-map', 'center'),
         Input('transport-interval', 'n_intervals')]
    )
    def update_bus_stops_display(show_bus_stops: bool, zoom: Optional[int], center: Optional[List], n_intervals: int):
        """
        Update bus stops markers, count display, and zoom feedback.
        Only renders bus stops within the current viewport when zoomed to level 15+.
        Always shows total count in the metric card.
        """
        _ = n_intervals  # Used for periodic refresh
        
        # Default zoom and center if not available
        current_zoom = zoom if zoom is not None else 11
        
        # Parse center coordinates - handle both list and dict formats
        if center is None:
            center_lat, center_lon = SG_MAP_CENTER[0], SG_MAP_CENTER[1]
        elif isinstance(center, dict):
            # Handle dict format {'lat': 1.23, 'lng': 103.45} or {'lat': 1.23, 'lon': 103.45}
            lat = center.get('lat')
            lon = center.get('lng') or center.get('lon')
            try:
                center_lat = float(lat) if lat is not None else SG_MAP_CENTER[0]
                center_lon = float(lon) if lon is not None else SG_MAP_CENTER[1]
            except (ValueError, TypeError):
                center_lat, center_lon = SG_MAP_CENTER[0], SG_MAP_CENTER[1]
        elif isinstance(center, (list, tuple)) and len(center) >= 2:
            # Handle list/tuple format [1.23, 103.45]
            try:
                center_lat = float(center[0])
                center_lon = float(center[1])
            except (ValueError, TypeError, IndexError):
                center_lat, center_lon = SG_MAP_CENTER[0], SG_MAP_CENTER[1]
        else:
            center_lat, center_lon = SG_MAP_CENTER[0], SG_MAP_CENTER[1]
        
        # Overlay styles
        overlay_show = {
            "position": "absolute",
            "top": "50%",
            "left": "50%",
            "transform": "translate(-50%, -50%)",
            "backgroundColor": "rgba(0, 0, 0, 0.8)",
            "color": "#fbbf24",
            "padding": "1rem 2rem",
            "borderRadius": "0.5rem",
            "zIndex": "1000",
            "textAlign": "center",
            "display": "block",
            "fontWeight": "600",
            "fontSize": "1rem",
            "border": "0.0625rem solid #fbbf24",
        }
        overlay_hide = {"display": "none"}
        
        # Always fetch data to calculate total count
        future = fetch_bus_stops_data_async()
        data: Optional[Dict[str, Any]] = future.result() if future else None
        
        # Calculate total count (always shown in metric card)
        bus_stops_count = 0
        if isinstance(data, dict):
            bus_stops_list = data.get('value', [])
            if isinstance(bus_stops_list, list):
                bus_stops_count = len(bus_stops_list)
        
        # Count card always shows total count
        count_card = html.Div(
            html.Span(f"{bus_stops_count}", style={"color": "#4169E1"}),
            style={
                "backgroundColor": "rgb(58, 74, 90)",
                "padding": "0.25rem 0.5rem",
                "borderRadius": "0.25rem",
            }
        )
        
        # Disclaimer styles
        disclaimer_hide = {"display": "none"}
        disclaimer_show = {"display": "block"}
        
        # If toggle is OFF, return empty markers and hide disclaimer
        if not show_bus_stops:
            return [], count_card, overlay_hide, "", disclaimer_hide
            
        # Toggle is ON - Check zoom level
        if current_zoom < 15:
            overlay_text = f"Zoom in to level 15+ to view bus stops (Current: {current_zoom})"
            return [], count_card, overlay_show, overlay_text, disclaimer_show
            
        # Toggle is ON and Zoom is >= 15 - Filter and render markers within viewport
        filtered_stops = filter_bus_stops_by_viewport(data, center_lat, center_lon, current_zoom)
        
        # Create filtered data dict for marker creation
        filtered_data = {'value': filtered_stops} if filtered_stops else None
        
        markers = create_bus_stops_circle_markers(filtered_data)
        return markers, count_card, overlay_hide, "", disclaimer_show

    @app.callback(
        [Output('bus-stops-toggle-state', 'data'),
         Output('bus-stops-toggle-btn', 'style'),
         Output('bus-stops-toggle-btn', 'children')],
        Input('bus-stops-toggle-btn', 'n_clicks'),
        State('bus-stops-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_bus_stops_display(_n_clicks: Optional[int], current_state: bool) -> Tuple[bool, Dict[str, Any], str]:
        """Toggle Bus Stops markers display on/off."""
        new_state = not current_state
        
        if new_state:
            # Active state - royal blue background
            style = {
                "backgroundColor": "#4169E1",
                "border": "none",
                "borderRadius": "0.25rem",
                "color": "#fff",
                "cursor": "pointer",
                "padding": "0.375rem 0.75rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Hide Bus Stop Locations"
        else:
            # Inactive state - outline
            style = {
                "backgroundColor": "transparent",
                "border": "0.125rem solid #4169E1",
                "borderRadius": "0.25rem",
                "color": "#4169E1",
                "cursor": "pointer",
                "padding": "0.25rem 0.625rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Show Bus Stop Locations"
        
        return new_state, style, text

    # SPF Speed Camera callbacks
    @app.callback(
        [Output('speed-camera-toggle-state', 'data'),
         Output('speed-camera-toggle-btn', 'style'),
         Output('speed-camera-toggle-btn', 'children')],
        Input('speed-camera-toggle-btn', 'n_clicks'),
        State('speed-camera-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_speed_camera_display(_n_clicks: Optional[int], current_state: bool) -> Tuple[bool, Dict[str, Any], str]:
        """Toggle SPF Speed Camera markers display on/off."""
        new_state = not current_state
        
        if new_state:
            # Active state - light green background
            style = {
                "backgroundColor": "#81C784",
                "border": "none",
                "borderRadius": "0.25rem",
                "color": "#fff",
                "cursor": "pointer",
                "padding": "0.375rem 0.75rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Hide SPF Speed Camera Locations"
        else:
            # Inactive state - outline
            style = {
                "backgroundColor": "transparent",
                "border": "0.125rem solid #81C784",
                "borderRadius": "0.25rem",
                "color": "#81C784",
                "cursor": "pointer",
                "padding": "0.25rem 0.625rem",
                "fontSize": "0.75rem",
                "fontWeight": "600",
            }
            text = "Show SPF Speed Camera Locations"
        
        return new_state, style, text

    @app.callback(
        [Output('speed-camera-markers', 'children'),
         Output('speed-camera-count-value', 'children')],
        [Input('speed-camera-toggle-state', 'data'),
         Input('transport-interval', 'n_intervals')]
    )
    def update_speed_camera_display(show_speed_camera: bool, n_intervals: int) -> Tuple[List[dl.CircleMarker], html.Div]:
        """Update SPF Speed Camera markers and count display."""
        _ = n_intervals  # Used for periodic refresh

        # Always calculate count
        speed_camera_count = get_fixed_speed_camera_count()
        
        count_value = html.Div(
            html.Span(f"{speed_camera_count}", style={"color": "#A5D6A7"}),
            style={
                "backgroundColor": "rgb(58, 74, 90)",
                "padding": "0.25rem 0.5rem",
                "borderRadius": "0.25rem",
            }
        )

        # Only show markers if toggle is on
        if not show_speed_camera:
            return [], count_value

        # Create markers
        markers = create_fixed_speed_camera_markers()

        return markers, count_value


