"""
Callback functions for handling nearest bus stop display using OneMap Nearby Transport API.
Reference: https://www.onemap.gov.sg/apidocs/nearbytransport

Uses ThreadPoolExecutor for async API fetching to improve performance.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from dash.dependencies import Input, Output
from dash import html
import dash_leaflet as dl
from callbacks.map_callback import _haversine_distance_m
from utils.async_fetcher import fetch_url

# Thread pool for async bus stop fetching
_bus_executor = ThreadPoolExecutor(max_workers=5)


def _get_onemap_headers():
    """Get headers for OneMap API requests."""
    api_token = os.getenv("ONEMAP_API_KEY")
    headers = {}
    if api_token:
        headers["Authorization"] = f"{api_token}"
    return headers


def _process_bus_stop_data(data, lat, lon, radius_m):
    """Process raw bus stop data and calculate distances."""
    if not data:
        return []
    
    processed_results = []
    for bus_stop in data:
        try:
            stop_lat = float(bus_stop.get('lat') or 0)
            stop_lon = float(bus_stop.get('lon') or 0)
            
            if stop_lat == 0 or stop_lon == 0:
                continue
            
            distance_m = _haversine_distance_m(lat, lon, stop_lat, stop_lon)
            
            if distance_m <= radius_m:
                processed_results.append({
                    'name': bus_stop.get('name') or 'Unknown Bus Stop',
                    'code': bus_stop.get('id') or '',
                    'distance_m': distance_m,
                    'latitude': stop_lat,
                    'longitude': stop_lon,
                    'raw_data': bus_stop
                })
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error processing bus stop data: {e}")
            continue
    
    processed_results.sort(key=lambda x: x['distance_m'])
    return processed_results


def fetch_nearby_bus_stops(lat: float, lon: float, radius_m: int = 500) -> list:
    """
    Fetch nearest bus stops using OneMap Nearby Transport API.
    Reference: https://www.onemap.gov.sg/apidocs/nearbytransport
    
    Uses the getNearestBusStops endpoint which returns bus stops within radius.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_m: Search radius in meters (default: 500)
    
    Returns:
        List of bus stop dictionaries with distance information
    """
    url = (
        f"https://www.onemap.gov.sg/api/public/nearbysvc/getNearestBusStops"
        f"?latitude={lat}&longitude={lon}&radius_in_meters={radius_m}"
    )
    print(url)
    
    data = fetch_url(url, _get_onemap_headers())
    
    if data is None:
        print(f"No bus stops found within {radius_m}m or API error")
        return []
    
    print(f"Found {len(data)} bus stops within {radius_m}m")
    return _process_bus_stop_data(data, lat, lon, radius_m)


def fetch_nearby_bus_stops_async(lat: float, lon: float, radius_m: int = 500):
    """
    Fetch nearest bus stops asynchronously (returns Future).
    Call .result() to get the data when needed.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_m: Search radius in meters (default: 500)
    
    Returns:
        Future that will contain list of bus stop dictionaries
    """
    return _bus_executor.submit(fetch_nearby_bus_stops, lat, lon, radius_m)


def _get_label_letter(index):
    """Get label letter (A, B, C, D, E) for index."""
    labels = ['A', 'B', 'C', 'D', 'E']
    return labels[index] if index < len(labels) else str(index + 1)


def create_bus_stop_markers(bus_stops):
    """Create map markers for bus stops with labels."""
    markers = []
    for idx, bus_stop in enumerate(bus_stops):
        lat = bus_stop.get('latitude')
        lon = bus_stop.get('longitude')
        name = bus_stop.get('name', 'Bus Stop')
        code = bus_stop.get('code', '')

        if lat is None or lon is None:
            continue

        # Get label letter
        label = _get_label_letter(idx)

        # Extract road name from raw_data if available, otherwise use N/A
        road_name = 'N/A'
        if 'raw_data' in bus_stop:
            raw = bus_stop['raw_data']
            # OneMap API might have road name in different fields
            road_name = raw.get('road', raw.get('roadName', raw.get('road_name', 'N/A')))
        
        # Build tooltip text with bus stop ID only
        tooltip_content = code if code else "N/A"

        # Create marker HTML with label
        marker_html = (
            f'<div style="width:32px;height:32px;background:#4CAF50;'
            f'border-radius:50%;border:3px solid #fff;'
            f'box-shadow:0 2px 8px rgba(76,175,80,0.6);'
            f'cursor:pointer;display:flex;align-items:center;'
            f'justify-content:center;font-size:14px;color:#fff;'
            f'font-weight:bold;position:relative;">'
            f'<span style="font-size:16px;">🚌</span>'
            f'<div style="position:absolute;top:-8px;right:-8px;'
            f'background:#FF5722;color:#fff;width:20px;height:20px;'
            f'border-radius:50%;border:2px solid #fff;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:12px;font-weight:bold;">{label}</div>'
            f'</div>'
        )

        marker_id = f"bus-stop-{lat}-{lon}-{idx}"

        markers.append(dl.DivMarker(
            id=marker_id,
            position=[lat, lon],
            iconOptions={
                'className': 'bus-stop-pin',
                'html': marker_html,
                'iconSize': [32, 32],
                'iconAnchor': [16, 16],
            },
            children=[dl.Tooltip(tooltip_content)]
        ))

    return markers


def register_busstop_callbacks(app):
    """
    Register callbacks for displaying nearest bus stops.
    """
    
    @app.callback(
        [Output('nearest-bus-stop-content', 'children'),
         Output('bus-stop-markers', 'children')],
        Input('input_search', 'value')
    )
    def update_nearest_bus_stop_content(search_value):
        """
        Update the nearest bus stop content based on selected location.
        
        Args:
            search_value: Selected value from search dropdown (format: 'lat,lon,address')
        
        Returns:
            HTML Div containing nearest bus stops within 500m
        """
        if not search_value:
            return html.P(
                "Select a location to view nearest bus stops",
                style={
                    "textAlign": "center",
                    "color": "#999",
                    "fontSize": "14px",
                    "fontStyle": "italic",
                    "padding": "20px"
                }
            ), []
        
        try:
            # Parse the search value to get coordinates
            parts = search_value.split(',', 2)
            lat = float(parts[0])
            lon = float(parts[1])
        except (ValueError, IndexError, TypeError):
            return html.P(
                "Invalid location coordinates",
                style={
                    "textAlign": "center",
                    "color": "#ff6b6b",
                    "fontSize": "14px",
                    "padding": "20px"
                }
            ), []
        
        # Fetch nearby bus stops within 500m
        bus_stops = fetch_nearby_bus_stops(lat, lon, radius_m=500)
        
        # Limit to top 5 nearest
        bus_stops = bus_stops[:5]
        
        if not bus_stops:
            return html.P(
                "No bus stops found within 500m",
                style={
                    "textAlign": "center",
                    "color": "#999",
                    "fontSize": "14px",
                    "fontStyle": "italic",
                    "padding": "20px"
                }
            ), []

        # Create markers for map
        markers = create_bus_stop_markers(bus_stops)

        # Build display items for each bus stop with labels
        bus_stop_items = []
        for idx, bus_stop in enumerate(bus_stops):
            name = bus_stop['name']
            code = bus_stop['code']
            distance_m = bus_stop['distance_m']

            # Get label letter
            label = _get_label_letter(idx)

            # Format distance display
            if distance_m < 1000:
                distance_str = f"{int(distance_m)}m"
            else:
                distance_str = f"{distance_m/1000:.2f}km"

            # Build display text with name and code if available
            display_name = name
            if code:
                display_name = f"{name} ({code})"

            bus_stop_items.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    label,
                                    style={
                                        "display": "inline-block",
                                        "width": "24px",
                                        "height": "24px",
                                        "lineHeight": "24px",
                                        "textAlign": "center",
                                        "backgroundColor": "#FF5722",
                                        "color": "#fff",
                                        "borderRadius": "50%",
                                        "fontSize": "12px",
                                        "fontWeight": "bold",
                                        "marginRight": "8px",
                                        "verticalAlign": "middle"
                                    }
                                ),
                                html.Span(
                                    display_name,
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "14px",
                                        "color": "#fff",
                                        "verticalAlign": "middle"
                                    }
                                )
                            ],
                            style={
                                "marginBottom": "4px",
                                "display": "flex",
                                "alignItems": "center"
                            }
                        ),
                        html.Div(
                            f"Distance: {distance_str}",
                            style={
                                "fontSize": "12px",
                                "color": "#60a5fa",
                                "fontWeight": "500"
                            }
                        )
                    ],
                    style={
                        "padding": "10px 12px",
                        "borderBottom": "1px solid #444",
                        "marginBottom": "6px",
                        "backgroundColor": "#1a1a1a",
                        "borderRadius": "4px"
                    }
                )
            )

        # Return all bus stop items and markers
        return bus_stop_items, markers

    # Callback for nearby transport page
    @app.callback(
        [Output('nearby-transport-bus-stop-content', 'children'),
         Output('nearby-bus-stop-markers', 'children')],
        Input('nearby-transport-search', 'value')
    )
    def update_nearby_transport_bus_stop_content(search_value):
        """
        Update the nearest bus stop content for nearby transport page based on selected location.
        
        Args:
            search_value: Selected value from search dropdown (format: 'lat,lon,address')
        
        Returns:
            HTML Div containing nearest bus stops within 500m
        """
        if not search_value:
            return html.P(
                "Select a location to view nearest bus stops",
                style={
                    "textAlign": "center",
                    "color": "#999",
                    "fontSize": "12px",
                    "fontStyle": "italic",
                    "padding": "15px"
                }
            ), []

        try:
            # Parse the search value to get coordinates
            parts = search_value.split(',', 2)
            lat = float(parts[0])
            lon = float(parts[1])
        except (ValueError, IndexError, TypeError):
            return html.P(
                "Invalid location coordinates",
                style={
                    "textAlign": "center",
                    "color": "#ff6b6b",
                    "fontSize": "12px",
                    "padding": "15px"
                }
            ), []

        # Fetch nearby bus stops within 500m
        bus_stops = fetch_nearby_bus_stops(lat, lon, radius_m=500)

        # Limit to top 5 nearest
        bus_stops = bus_stops[:5]

        if not bus_stops:
            return html.P(
                "No bus stops found within 500m",
                style={
                    "textAlign": "center",
                    "color": "#999",
                    "fontSize": "12px",
                    "fontStyle": "italic",
                    "padding": "15px"
                }
            ), []

        # Create markers for map
        markers = create_bus_stop_markers(bus_stops)

        # Build display items for each bus stop with labels
        bus_stop_items = []
        for idx, bus_stop in enumerate(bus_stops):
            name = bus_stop['name']
            code = bus_stop['code']
            distance_m = bus_stop['distance_m']

            # Get label letter
            label = _get_label_letter(idx)

            # Format distance display
            if distance_m < 1000:
                distance_str = f"{int(distance_m)}m"
            else:
                distance_str = f"{distance_m/1000:.2f}km"

            bus_stop_items.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    label,
                                    style={
                                        "display": "inline-block",
                                        "width": "24px",
                                        "height": "24px",
                                        "lineHeight": "24px",
                                        "textAlign": "center",
                                        "backgroundColor": "#FF5722",
                                        "color": "#fff",
                                        "borderRadius": "50%",
                                        "fontSize": "12px",
                                        "fontWeight": "bold",
                                        "marginRight": "8px"
                                    }
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            name,
                                            style={
                                                "fontWeight": "600",
                                                "fontSize": "14px",
                                                "color": "#fff",
                                                "marginBottom": "4px"
                                            }
                                        ),
                                        html.Div(
                                            f"Code: {code} | Distance: {distance_str}",
                                            style={
                                                "fontSize": "12px",
                                                "color": "#4CAF50",
                                                "fontWeight": "500"
                                            }
                                        )
                                    ],
                                    style={"flex": "1"}
                                )
                            ],
                            style={
                                "display": "flex",
                                "alignItems": "center"
                            }
                        )
                    ],
                    style={
                        "padding": "10px 12px",
                        "borderBottom": "1px solid #444",
                        "marginBottom": "6px",
                        "backgroundColor": "#1a1a1a",
                        "borderRadius": "4px"
                    }
                )
            )

        # Return all bus stop items and markers
        return bus_stop_items, markers

