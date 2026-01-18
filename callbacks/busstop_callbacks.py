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


def fetch_nearby_bus_stops(lat: float, lon: float, radius_m: int = 500):
    """
    Fetch nearest bus stops using OneMap Nearby Transport API.
    Reference: https://www.onemap.gov.sg/apidocs/nearbytransport
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_m: Search radius in meters (default: 500)
    
    Returns:
        List of bus stop dictionaries with distance information
    """
    try:
        # OneMap Nearby Transport API endpoint for bus stops
        url = f"https://www.onemap.gov.sg/api/public/nearbysvc/getNearestBusStops?latitude={lat}&longitude={lon}&radius_in_meters={radius_m}"
        
        headers = _get_onemap_headers()
        response_data = fetch_url(url, headers=headers)
        
        if not response_data:
            return []
        
        # Process the response data (API may return dict or list)
        if isinstance(response_data, dict):
            bus_stops = response_data.get('results', [])
        elif isinstance(response_data, list):
            bus_stops = response_data
        else:
            print(f"Unexpected bus stop response type: {type(response_data)}")
            return []
        return _process_bus_stop_data(bus_stops, lat, lon, radius_m)
        
    except Exception as e:
        print(f"Error fetching nearby bus stops: {e}")
        return []


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
            f'<div style="width:2rem;height:2rem;background:#4CAF50;'
            f'border-radius:50%;border:0.1875rem solid #fff;'
            f'box-shadow:0 0.125rem 0.5rem rgba(76,175,80,0.6);'
            f'cursor:pointer;display:flex;align-items:center;'
            f'justify-content:center;font-size:0.875rem;color:#fff;'
            f'font-weight:bold;position:relative;">'
            f'<span style="font-size:1rem;">🚌</span>'
            f'<div style="position:absolute;top:-0.5rem;right:-0.5rem;'
            f'background:#FF5722;color:#fff;width:1.25rem;height:1.25rem;'
            f'border-radius:50%;border:0.125rem solid #fff;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:0.75rem;font-weight:bold;">{label}</div>'
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
                    "fontSize": "0.875rem",
                    "fontStyle": "italic",
                    "padding": "0.5rem"
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
                    "fontSize": "0.875rem",
                    "padding": "0.5rem"
                }
            ), []
        
        # Fetch nearby bus stops within 500m
        future = fetch_nearby_bus_stops_async(lat, lon, radius_m=500)
        bus_stops = future.result() if future else []
        
        # Limit to top 5 nearest
        bus_stops = bus_stops[:5]
        
        if not bus_stops:
            return html.P(
                "No bus stops found within 500m",
                style={
                    "textAlign": "center",
                    "color": "#999",
                    "fontSize": "0.875rem",
                    "fontStyle": "italic",
                    "padding": "0.5rem"
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
                                        "width": "1.5rem",
                                        "height": "1.5rem",
                                        "lineHeight": "1.5rem",
                                        "textAlign": "center",
                                        "backgroundColor": "#FF5722",
                                        "color": "#fff",
                                        "borderRadius": "50%",
                                        "fontSize": "0.75rem",
                                        "fontWeight": "bold",
                                        "marginRight": "0.5rem",
                                        "verticalAlign": "middle"
                                    }
                                ),
                                html.Span(
                                    display_name,
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "0.875rem",
                                        "color": "#fff",
                                        "verticalAlign": "middle"
                                    }
                                )
                            ],
                            style={
                                "marginBottom": "0.25rem",
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

        # Return all bus stop items and markers with H4 title
        output = [
            html.H4(
                "Top 5 Nearest Bus Stops",
                style={
                    "textAlign": "center",
                    "marginBottom": "0.625rem",
                    "color": "#fff",
                    "fontWeight": "700",
                    "fontSize": "0.875rem"
                }
            ),
            *bus_stop_items
        ]
        return output, markers

    # Callback for nearby transport page
    @app.callback(
        [Output('nearby-transport-bus-stop-column', 'children'),
         Output('nearby-bus-stop-markers', 'children')],
        Input('nearby-transport-location-store', 'data')
    )
    def update_nearby_transport_bus_stop_content(location_data):
        """
        Update the nearest bus stop content for nearby transport page based on selected location.
        
        Args:
            location_data: Dictionary containing {'lat': float, 'lon': float} of selected location
        
        Returns:
            HTML Div containing nearest bus stops within 500m
        """
        if not location_data:
            return [
                html.H4(
                    "Top 5 Nearest Bus Stops",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "Select a location to view nearest bus stops",
                    style={
                        "textAlign": "center",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic",
                        "padding": "0.9375rem"
                    }
                )
            ], []

        try:
            lat = float(location_data.get('lat'))
            lon = float(location_data.get('lon'))
        except (ValueError, TypeError, KeyError):
            return [
                html.H4(
                    "Top 5 Nearest Bus Stops",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "Invalid location coordinates",
                    style={
                        "textAlign": "center",
                        "color": "#ff6b6b",
                        "fontSize": "0.75rem",
                        "padding": "0.9375rem"
                    }
                )
            ], []

        # Fetch nearby bus stops within 500m
        future = fetch_nearby_bus_stops_async(lat, lon, radius_m=500)
        bus_stops = future.result() if future else []

        # Limit to top 5 nearest
        bus_stops = bus_stops[:5]

        if not bus_stops:
            return [
                html.H4(
                    "Top 5 Nearest Bus Stops",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "No bus stops found within 500m",
                    style={
                        "textAlign": "center",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic",
                        "padding": "0.9375rem"
                    }
                )
            ], []

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
                                                "fontSize": "0.875rem",
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

        # Return all bus stop items and markers with H4 title
        output = [
            html.H4(
                "Top 5 Nearest Bus Stops",
                style={
                    "textAlign": "center",
                    "marginBottom": "0.625rem",
                    "color": "#fff",
                    "fontWeight": "700",
                    "fontSize": "0.875rem"
                }
            ),
            *bus_stop_items
        ]
        return output, markers

