"""
Callback functions for handling MRT/LRT Station Crowd information.
Uses LTA DataMall PCDRealTime API for real-time crowd density data.
"""
import os
import csv
import re
import threading
from typing import Optional, Dict, Any
from concurrent.futures import as_completed
from dash import Input, Output, State, html
import dash_leaflet as dl
from utils.async_fetcher import fetch_url_10min_cached, _executor, get_current_10min_bucket
from utils.map_utils import SG_MAP_CENTER

# API URL
PCD_REALTIME_URL = "https://datamall2.mytransport.sg/ltaodataservice/PCDRealTime"

# Global cache for the combined crowd data to ensure 10-minute alignment
_COMBINED_CROWD_CACHE = {'data': None, 'bucket': None}
_COMBINED_CROWD_LOCK = threading.Lock()


# List of all train lines to fetch
ALL_TRAIN_LINES = ['CCL', 'CEL', 'CGL', 'DTL', 'EWL', 'NEL', 'NSL', 'BPL', 'SLRT', 'PLRT', 'TEL']

# Crowd level colors
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

# Crowd level icons (using people/crowd icons)
CROWD_ICONS = {
    'l': '👤',  # Single person (Low crowd)
    'm': '👥',  # Two people (Moderate crowd)
    'h': '👥👥',  # Many people (High crowd)
    'NA': '❓',  # Question mark (Not Available)
}


def _station_sort_key(station_obj):
    """
    Helper to sort station codes numerically (e.g., EW1, EW2, ..., EW10).
    """
    station_code = station_obj.get('Station', '')
    if not station_code:
        return ("", 0)

    # Extract prefix (e.g., EW) and number (e.g., 10)
    match = re.match(r"([a-zA-Z]+)(\d+)", station_code)
    if match:
        prefix, number = match.groups()
        return (prefix.upper(), int(number))

    # Fallback for codes that don't match the pattern
    return (station_code.upper(), 0)

# Station name mapping cache
_STATION_NAME_MAP = None
_STATION_LOCATION_MAP = None


def _load_station_names() -> Dict[str, str]:
    """
    Load station codes to station names mapping from CSV file.
    Returns a dictionary mapping station codes to station names.
    """
    global _STATION_NAME_MAP
    if _STATION_NAME_MAP is not None:
        return _STATION_NAME_MAP

    _STATION_NAME_MAP = {}
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'MRTLRTStations.csv')

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stn_no = row.get('STN_NO', '').strip()
                stn_name = row.get('STN_NAME', '').strip()
                if stn_no and stn_name:
                    # Handle multi-line stations (e.g., "EW8/CC9")
                    if '/' in stn_no:
                        for code in stn_no.split('/'):
                            _STATION_NAME_MAP[code.strip()] = stn_name
                    else:
                        _STATION_NAME_MAP[stn_no] = stn_name
    except Exception as e:
        print(f"Warning: Could not load station names from CSV: {e}")

    return _STATION_NAME_MAP


def _load_station_locations() -> Dict[str, Dict[str, Any]]:
    """
    Load station codes to locations (lat, lon, name) mapping from CSV file.
    Returns a dictionary mapping station codes to location details.
    """
    global _STATION_LOCATION_MAP
    if _STATION_LOCATION_MAP is not None:
        return _STATION_LOCATION_MAP

    _STATION_LOCATION_MAP = {}
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'MRTLRTStations.csv')

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stn_no = row.get('STN_NO', '').strip()
                stn_name = row.get('STN_NAME', '').strip()
                lat = row.get('Latitude')
                lon = row.get('Longitude')
                if stn_no and lat and lon:
                    loc = {
                        'lat': float(lat),
                        'lon': float(lon),
                        'name': stn_name
                    }
                    # Handle multi-line stations (e.g., "EW8/CC9")
                    if '/' in stn_no:
                        for code in stn_no.split('/'):
                            _STATION_LOCATION_MAP[code.strip()] = loc
                    else:
                        _STATION_LOCATION_MAP[stn_no] = loc
    except Exception as e:
        print(f"Error loading station locations: {e}")

    return _STATION_LOCATION_MAP


def fetch_station_crowd_data(train_line: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch station crowd density data from LTA DataMall PCDRealTime API.

    Args:
        train_line: Optional train line code
                   (CCL, CEL, CGL, DTL, EWL, NEL, NSL, BPL, SLRT, PLRT, TEL)
                   If None, fetches all lines

    Returns:
        Dictionary containing crowd data or None if error
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

    # Build URL with TrainLine parameter if specified
    url = PCD_REALTIME_URL
    if train_line:
        url = f"{PCD_REALTIME_URL}?TrainLine={train_line}"

    # Use cached fetch (10-minute cache based on system clock)
    return fetch_url_10min_cached(url, headers)


def fetch_all_station_crowd_data() -> Optional[Dict[str, Any]]:
    """
    Fetch crowd data for all train lines in parallel and combine results.
    Uses a 10-minute in-memory cache aligned to system clock.

    Returns:
        Dictionary containing combined crowd data from all lines or None if error
    """
    global _COMBINED_CROWD_CACHE
    
    current_bucket = get_current_10min_bucket()
    
    # Check high-level cache first
    with _COMBINED_CROWD_LOCK:
        if _COMBINED_CROWD_CACHE['bucket'] == current_bucket and _COMBINED_CROWD_CACHE['data'] is not None:
            # print(f"DEBUG: Serving combined crowd data from 10-minute cache (bucket: {current_bucket})")
            return _COMBINED_CROWD_CACHE['data']

    # If not in cache or bucket expired, fetch fresh data
    # Fetch all lines in parallel
    futures = {
        _executor.submit(fetch_station_crowd_data, line): line
        for line in ALL_TRAIN_LINES
    }

    all_stations = []
    for future in as_completed(futures):
        line = futures[future]
        try:
            data = future.result()
            if data and 'value' in data:
                stations = data['value']
                # Add TrainLine to each station if not present
                for station in stations:
                    if 'TrainLine' not in station or not station.get('TrainLine'):
                        station['TrainLine'] = line
                all_stations.extend(stations)
                # print(f"DEBUG: Fetched {len(stations)} stations for line {line}")
        except Exception as e:
            print(f"Error fetching crowd data for {line}: {e}")

    if not all_stations:
        return None

    combined_data = {'value': all_stations}
    
    # Update cache
    with _COMBINED_CROWD_LOCK:
        _COMBINED_CROWD_CACHE = {
            'data': combined_data,
            'bucket': current_bucket
        }

    print(f"DEBUG: Combined crowd data fetched and cached for bucket {current_bucket} ({len(all_stations)} stations)")
    return combined_data


def register_mrt_crowd_callbacks(app):
    """
    Register callbacks for MRT/LRT crowd density information.
    """
    # Toggle callback for MRT Crowd Level button label
    @app.callback(
        Output('toggle-mrt-crowd', 'children'),
        Input('toggle-mrt-crowd', 'n_clicks'),
        State('mrt-crowd-toggle-state', 'data')
    )
    def toggle_mrt_crowd_button_label(n_clicks, current_state):
        # Default state is False (disabled), so show "Show" by default
        if n_clicks is None or n_clicks == 0:
            return "🚆 Show MRT/LRT Station Crowd Level"
        is_visible = not current_state if current_state is not None else True
        return "🚆 Hide MRT/LRT Station Crowd Level" if is_visible else "🚆 Show MRT/LRT Station Crowd Level"

    # Toggle state update callback
    @app.callback(
        Output('mrt-crowd-toggle-state', 'data'),
        Input('toggle-mrt-crowd', 'n_clicks'),
        State('mrt-crowd-toggle-state', 'data')
    )
    def update_mrt_crowd_toggle_state(n_clicks, current_state):
        # Default state is False (disabled)
        if n_clicks is None or n_clicks == 0:
            return False
        return not current_state if current_state is not None else True

    # Main map markers callback
    @app.callback(
        Output('mrt-crowd-markers', 'children'),
        [Input('interval-component', 'n_intervals'),
         Input('mrt-crowd-toggle-state', 'data')]
    )
    def update_mrt_crowd_map_markers(_n_intervals, is_visible):
        if not is_visible:
            return []

        # Fetch crowd data
        crowd_data = fetch_all_station_crowd_data()
        
        # Show loading marker if data is not yet available
        if not crowd_data or 'value' not in crowd_data:
            loading_style = (
                "font-size: 14px; "
                "display: flex; "
                "align-items: center; "
                "justify-content: center; "
                "padding: 8px 12px; "
                "background-color: rgba(0, 188, 212, 0.9); "
                "color: white; "
                "border-radius: 0.5rem; "
                "border: 2px solid white; "
                "box-shadow: 0 0 10px rgba(0,0,0,0.5); "
                "font-weight: bold; "
                "white-space: nowrap;"
            )
            loading_html = f'<div style="{loading_style}">⏳ Loading crowd data...</div>'
            loading_marker = dl.DivMarker(
                position=SG_MAP_CENTER,
                iconOptions={
                    'className': 'mrt-crowd-loading-marker',
                    'html': loading_html,
                    'iconSize': [200, 40],
                    'iconAnchor': [100, 20],
                },
                children=[
                    dl.Tooltip("Loading MRT/LRT station crowd data...")
                ]
            )
            return [loading_marker]

        # Load station locations
        station_locs = _load_station_locations()
        if not station_locs:
            # Show loading if locations not loaded
            loading_style = (
                "font-size: 14px; "
                "display: flex; "
                "align-items: center; "
                "justify-content: center; "
                "padding: 8px 12px; "
                "background-color: rgba(0, 188, 212, 0.9); "
                "color: white; "
                "border-radius: 20px; "
                "border: 2px solid white; "
                "box-shadow: 0 0 10px rgba(0,0,0,0.5); "
                "font-weight: bold; "
                "white-space: nowrap;"
            )
            loading_html = f'<div style="{loading_style}">⏳ Loading station locations...</div>'
            loading_marker = dl.DivMarker(
                position=SG_MAP_CENTER,
                iconOptions={
                    'className': 'mrt-crowd-loading-marker',
                    'html': loading_html,
                    'iconSize': [200, 40],
                    'iconAnchor': [100, 20],
                },
                children=[
                    dl.Tooltip("Loading station location data...")
                ]
            )
            return [loading_marker]

        markers = []
        # Group stations by location to handle multi-code stations (e.g., Jurong East EW24/NS1)
        loc_grouped_data = {}
        
        for station in crowd_data['value']:
            code = station.get('Station', '')
            crowd = station.get('CrowdLevel', 'NA')
            
            if code in station_locs:
                loc = station_locs[code]
                key = (loc['lat'], loc['lon'])
                if key not in loc_grouped_data:
                    loc_grouped_data[key] = {
                        'name': loc['name'],
                        'codes': [],
                        'crowd_levels': {}
                    }
                loc_grouped_data[key]['codes'].append(code)
                loc_grouped_data[key]['crowd_levels'][code] = crowd

        for (lat, lon), info in loc_grouped_data.items():
            # Determine overall crowd level for the station (take max if multiple codes)
            levels = info['crowd_levels'].values()
            if 'h' in levels:
                worst_level = 'h'
            elif 'm' in levels:
                worst_level = 'm'
            else:
                worst_level = 'l' if 'l' in levels else 'NA'

            color = CROWD_COLORS.get(worst_level, '#888888')
            label = CROWD_LABELS.get(worst_level, 'Not Available')
            icon = CROWD_ICONS.get(worst_level, '⚪')
            
            # Create tooltip text
            codes_str = "/".join(info['codes'])
            tooltip_content = [
                html.B(info['name']),
                html.Br(),
                html.Span(f"Codes: {codes_str}"),
                html.Br(),
                html.Span(f"Crowd: {label}", style={'color': color, 'fontWeight': 'bold'})
            ]

            # Create icon HTML with color-coded crowd icon
            # Use people/crowd icons with colored background circle
            container_style = (
                f"display: flex; "
                f"align-items: center; "
                f"justify-content: center; "
                f"width: 32px; "
                f"height: 32px; "
                f"background-color: {color}; "
                f"border-radius: 50%; "
                f"border: 2px solid white; "
                f"box-shadow: 0 0 5px rgba(0,0,0,0.5), 0 0 3px {color};"
            )
            icon_style = (
                f"font-size: 18px; "
                f"line-height: 1; "
                f"text-shadow: 0 0 2px #000;"
            )
            icon_html = f'<div style="{container_style}"><span style="{icon_style}">{icon}</span></div>'
            
            # Use DivMarker with color-coded crowd icon
            marker = dl.DivMarker(
                position=[lat, lon],
                iconOptions={
                    'className': 'mrt-crowd-icon-marker',
                    'html': icon_html,
                    'iconSize': [32, 32],
                    'iconAnchor': [16, 16],
                },
                children=[
                    dl.Tooltip(html.Div(tooltip_content)),
                    dl.Popup(html.Div(tooltip_content))
                ]
            )
            markers.append(marker)

        return markers
