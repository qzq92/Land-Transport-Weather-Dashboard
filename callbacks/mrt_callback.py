"""
Callback functions for handling nearest MRT/LRT station display using OneMap Nearby Transport API.
Reference: https://www.onemap.gov.sg/apidocs/nearbytransport
"""
import requests
from dash.dependencies import Input, Output
from dash import html
from callbacks.map_callback import _haversine_distance_m
from callbacks.mrt_crowd_callback import fetch_all_station_crowd_data
from utils.async_fetcher import run_in_thread
#from auth.onemap_api import get_onemap_token
import os

# Crowd level colors (matching mrt_crowd_callback)
CROWD_COLORS = {
    'l': '#32CD32',  # Low - Green
    'm': '#FFD700',  # Moderate - Yellow/Gold
    'h': '#FF4500',  # High - Orange Red
    'NA': '#888888',  # Not Available - Grey
}

# Crowd level labels
CROWD_LABELS = {
    'l': 'Low',
    'm': 'Moderate',
    'h': 'High',
    'NA': 'Not Available',
}



@run_in_thread
def fetch_nearby_mrt_stations_async(lat: float, lon: float, radius_m: int = 500) -> list:
    """
    Fetch nearest MRT/LRT stations using OneMap Nearby Transport API.
    Reference: https://www.onemap.gov.sg/apidocs/nearbytransport
    
    Uses the getNearestMrtStops endpoint which returns MRT/LRT stations within radius.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        radius_m: Search radius in meters (default: 500)
    
    Returns:
        List of MRT/LRT station dictionaries with distance information
    """
    try:
        # OneMap Nearby Transport API endpoint for MRT/LRT stations
        url = f"https://www.onemap.gov.sg/api/public/nearbysvc/getNearestMrtStops?latitude={lat}&longitude={lon}&radius_in_meters={radius_m}"

        print(url)
        
        # Get API token from auth module - uses cached token if valid, no re-authentication needed
        # Token is already cached from app startup, this just retrieves it
        api_token = os.getenv("ONEMAP_API_KEY")
        
        headers = {}
        if api_token:
            # OneMap API expects Authorization header with Bearer token format
            headers["Authorization"] = f"{api_token}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Process results - API may return results in different formats
            #results = data.get('results', data.get('mrt_stops', []))
            
            if not data:
                print(f"No MRT/LRT stations found within {radius_m}m")
                return []
            
            print(f"Found {len(data)} MRT/LRT stations within {radius_m}m")
            # Process and add distance information
            processed_results = []
            for station in data:
                try:
                    # Try different possible field names from API response
                    station_lat = float(
                        station.get('lat') or 0
                    )
                    station_lon = float(
                        station.get('lon') or 0
                    )
                    
                    # Skip due to invalid coordinates
                    if station_lat == 0 or station_lon == 0:
                        continue
                    
                    # Calculate distance using haversine formula
                    distance_m = _haversine_distance_m(lat, lon, station_lat, station_lon)
                    
                    # Only include stations within the specified radius
                    if distance_m <= radius_m:
                        # Get station name from various possible fields
                        name = (
                            station.get('name') or 
                            'Unknown Station'
                        )

                        station_id = (
                            station.get('id') or
                            ''
                        )
                        
                        processed_results.append({
                            'name': f"{name}({station_id})",
                            'distance_m': distance_m,
                            'latitude': station_lat,
                            'longitude': station_lon,
                            'raw_data': station
                        })
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Error processing station data: {e}")
                    continue
            
            # Sort by distance (closest first)
            processed_results.sort(key=lambda x: x['distance_m'])
            
            return processed_results
        
        print(f"OneMap Nearby Transport API failed for MRT/LRT stations: status={response.status_code}, body={response.text[:200]}")
        return []
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling OneMap Nearby Transport API: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in fetch_nearby_mrt_stations: {e}")
        return []


def register_mrt_callbacks(app):
    """
    Register callbacks for displaying nearest MRT/LRT stations.
    """
    
    @app.callback(
        Output('nearest-mrt-content', 'children'),
        Input('input_search', 'value')
    )
    def update_nearest_mrt_content(search_value):
        """
        Update the nearest MRT content based on selected location.
        
        Args:
            search_value: Selected value from search dropdown (format: 'lat,lon,address')
        
        Returns:
            HTML Div containing nearest MRT/LRT stations within 1000m
        """
        if not search_value:
            return html.P(
                "Select a location to view nearest MRT stations",
                style={
                    "textAlign": "center",
                    "color": "#999",
                    "fontSize": "14px",
                    "fontStyle": "italic",
                    "padding": "20px"
                }
            )
        
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
            )
        
        # Fetch nearby MRT stations within 1000m
        future = fetch_nearby_mrt_stations_async(lat, lon, radius_m=1000)
        stations = future.result() if future else []
        
        if not stations:
            return html.P(
                "No MRT/LRT stations found within specified radius",
                style={
                    "textAlign": "center",
                    "color": "#999",
                    "fontSize": "14px",
                    "fontStyle": "italic",
                    "padding": "20px"
                }
            )
        
        # Build display items for each station
        station_items = []
        for station in stations:
            name = station['name']
            distance_m = station['distance_m']
            
            # Format distance display
            if distance_m < 1000:
                distance_str = f"{int(distance_m)}m"
            else:
                distance_str = f"{distance_m/1000:.2f}km"
            
            station_items.append(
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
        
        # Return all station items with H4 title
        return [
            html.H4(
                "Nearest MRT (1KM radius) with crowd level",
                style={
                    "textAlign": "center",
                    "marginBottom": "0.625rem",
                    "color": "#fff",
                    "fontWeight": "700",
                    "fontSize": "0.875rem"
                }
            ),
            *station_items
        ]

    # Callback for nearby transport page
    @app.callback(
        Output('nearby-transport-mrt-column', 'children'),
        Input('nearby-transport-search', 'value')
    )
    def update_nearby_transport_mrt_content(search_value):
        """
        Update the nearest MRT content for nearby transport page based on selected location.
        
        Args:
            search_value: Selected value from search dropdown (format: 'lat,lon,address')
        
        Returns:
            HTML Div containing nearest MRT/LRT stations within 1000m
        """
        if not search_value:
            return [
                html.H4(
                    "Nearest MRT (1KM radius) with crowd level",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "Select a location to view nearest MRT stations",
                    style={
                        "textAlign": "center",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic",
                        "padding": "0.9375rem"
                    }
                )
            ]
        
        try:
            # Parse the search value to get coordinates
            parts = search_value.split(',', 2)
            lat = float(parts[0])
            lon = float(parts[1])
        except (ValueError, IndexError, TypeError):
            return [
                html.H4(
                    "Nearest MRT (1KM radius) with crowd level",
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
            ]
        
        # Fetch nearby MRT stations within 1000m
        future = fetch_nearby_mrt_stations_async(lat, lon, radius_m=1000)
        stations = future.result() if future else []
        
        if not stations:
            return [
                html.H4(
                    "Nearest MRT (1KM radius) with crowd level",
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.625rem",
                        "color": "#fff",
                        "fontWeight": "700",
                        "fontSize": "0.875rem"
                    }
                ),
                html.P(
                    "No MRT/LRT stations found within specified radius",
                    style={
                        "textAlign": "center",
                        "color": "#999",
                        "fontSize": "0.75rem",
                        "fontStyle": "italic",
                        "padding": "0.9375rem"
                    }
                )
            ]
        
        # Fetch crowd data for all stations
        crowd_data = fetch_all_station_crowd_data()
        crowd_lookup = {}
        if crowd_data and 'value' in crowd_data:
            for stn in crowd_data['value']:
                station_code = stn.get('Station', '')
                crowd_level = stn.get('CrowdLevel', 'NA')
                if station_code:
                    crowd_lookup[station_code] = crowd_level
        
        # Build display items for each station
        station_items = []
        for station in stations:
            name = station['name']
            distance_m = station['distance_m']
            station_code = station.get('raw_data', {}).get('id', '')
            
            # Format distance display
            if distance_m < 1000:
                distance_str = f"{int(distance_m)}m"
            else:
                distance_str = f"{distance_m/1000:.2f}km"
            
            # Get crowd level for this station
            # Handle multi-line stations (e.g., "EW8/CC9") - check each code
            crowd_level = 'NA'
            if station_code:
                if '/' in station_code:
                    # For multi-line stations, try to find crowd data for any of the lines
                    codes = station_code.split('/')
                    for code in codes:
                        if code.strip() in crowd_lookup:
                            crowd_level = crowd_lookup[code.strip()]
                            break
                else:
                    crowd_level = crowd_lookup.get(station_code, 'NA')
            
            crowd_color = CROWD_COLORS.get(crowd_level, CROWD_COLORS['NA'])
            crowd_label = CROWD_LABELS.get(crowd_level, 'Not Available')
            
            station_items.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    name,
                                    style={
                                        "fontWeight": "600",
                                        "fontSize": "14px",
                                        "color": "#fff",
                                    }
                                ),
                                html.Span(
                                    crowd_label,
                                    style={
                                        "fontSize": "11px",
                                        "color": crowd_color,
                                        "fontWeight": "700",
                                        "marginLeft": "8px",
                                        "padding": "2px 6px",
                                        "borderRadius": "3px",
                                        "backgroundColor": f"{crowd_color}22",
                                    }
                                )
                            ],
                            style={
                                "display": "flex",
                                "alignItems": "center",
                                "marginBottom": "4px"
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
        
        # Return all station items with H4 title
        return [
            html.H4(
                "Nearest MRT (1KM radius) with crowd level",
                style={
                    "textAlign": "center",
                    "marginBottom": "0.625rem",
                    "color": "#fff",
                    "fontWeight": "700",
                    "fontSize": "0.875rem"
                }
            ),
            *station_items
        ]

