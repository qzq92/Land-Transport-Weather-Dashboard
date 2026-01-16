"""
Callback functions for handling map interactions and OneMap search API integration.
Reference: https://www.onemap.gov.sg/apidocs/search
"""
import re
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv
from dash.dependencies import Input, Output, State
from dash import no_update
import dash_leaflet as dl
from utils.async_fetcher import run_in_thread
load_dotenv(override=True)

@run_in_thread
def search_location_via_onemap_info_async(searchVal: str, returnGeom: str = "Y", getAddrDetails: str = "Y", pageNum: int = 1):
    """
    Search for location using OneMap Search API.
    Reference: https://www.onemap.gov.sg/apidocs/search
    
    Args:
        searchVal: Search value (required)
        returnGeom: Return geometry coordinates (Y/N), default Y
        getAddrDetails: Return address details (Y/N), default Y
        pageNum: Page number for pagination, default 1
    
    Returns:
        List of search results from OneMap API
    """
    # Defensive: handle None/NaN/float and ensure URL-safe encoding
    if not searchVal or str(searchVal).strip() == "":
        return []
    
    searchVal = quote_plus(str(searchVal).strip())
    
    # OneMap Search API endpoint as per documentation
    onemap_search_url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={searchVal}&returnGeom={returnGeom}&getAddrDetails={getAddrDetails}&pageNum={pageNum}"
    print(f"OneMap Search API Request: {onemap_search_url}")

    req_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    }
    
    try:
        res = requests.get(onemap_search_url, headers=req_headers, timeout=10)
        if res.status_code == 200:
            print(f"Request successful with status code {res.status_code}")
            the_json = res.json()
            found = the_json.get("found", 0)
            total_num_pages = the_json.get("totalNumPages", 0)
            page_num = the_json.get("pageNum", 0)
            results = the_json.get("results", [])

            print(f"Found {found} results, Page {page_num} of {total_num_pages}")
            return results

        print(f"Request unsuccessful with status code {res.status_code}")
        return []
    except requests.exceptions.RequestException as error:
        print(f"Error during OneMap API request: {error}")
        return []

def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance in meters between two WGS84 lat/lon points."""
    from math import radians, sin, cos, asin, sqrt
    r = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2.0)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2.0)**2
    c = 2.0 * asin(sqrt(a))
    return r * c

def register_search_callbacks(app):
    """
    Register search-related callbacks for the OneMap search functionality.
    Implements integrated search bar with top 5 most relevant results.
    Reference: https://www.onemap.gov.sg/apidocs/search
    """

    @app.callback(
        Output('input_search', 'options'),
        Input('input_search', 'search_value'),
        Input('input_search', 'value')
    )
    def update_search_options(search_value, selected_value):
        """
        Update dropdown with top 5 search results from OneMap API as user types.

        Args:
            search_value: Text entered in the search input
            selected_value: Currently selected value

        Returns:
            List of top 5 dropdown options with address labels and lat/lon values
        """
        # If user has selected a value, keep it in options
        if selected_value and not search_value:
            try:
                parts = selected_value.split(',', 2)
                address = parts[2] if len(parts) > 2 else "Selected Location"
                return [{'label': address, 'value': selected_value}]
            except (ValueError, IndexError):
                return []

        if not search_value or len(str(search_value).strip()) < 3:
            return []

        future = search_location_via_onemap_info_async(search_value)
        results = future.result() if future else []
        options = []

        # Limit to top 5 most relevant results
        for result in results[:5]:
            # Extract relevant fields from OneMap API response
            address = result.get('ADDRESS', 'Unknown Address')
            building = result.get('BUILDING', '')
            postal = result.get('POSTAL', '')
            lat = result.get('LATITUDE')
            lon = result.get('LONGITUDE')

            if lat and lon:
                # Create a descriptive label
                label_parts = []
                if building:
                    label_parts.append(building)
                if address:
                    label_parts.append(address)
                if postal:
                    label_parts.append(f"(S{postal})")

                label = ', '.join(label_parts) if label_parts else address

                # Store coordinates in EPSG:4326 format (Leaflet expects this)
                # Include postal code in value: lat,lon,address,postal
                options.append({
                    'label': label,
                    'value': f'{lat},{lon},{address},{postal}' if postal else f'{lat},{lon},{address}'
                })

        print(f"Generated {len(options)} dropdown options (top 5)")
        return options

    @app.callback(
        [Output('sg-map', 'viewport'),
         Output('markers-layer', 'children'),
         Output('map-coordinates-store', 'data')],
        Input('input_search', 'value')
    )
    def update_map_from_search_selection(dropdown_value):
        """
        Update map when user selects a location from the dropdown.
        Centers the map on the selected location and adds a marker.
        Also updates the coordinates store.

        Args:
            dropdown_value: Selected value from dropdown (format: 'lat,lon,address')

        Returns:
            Tuple of (viewport dict, marker, coordinates store data)
        """
        print(f"Callback triggered with dropdown_value: {dropdown_value}")
        
        if not dropdown_value:
            print("No dropdown value, returning no_update")
            return no_update, no_update, no_update

        try:
            # Parse the dropdown value
            parts = dropdown_value.split(',', 2)  # Split into max 3 parts
            lat_str, lon_str = parts[0], parts[1]
            address = parts[2] if len(parts) > 2 else "Selected Location"

            lat, lon = float(lat_str), float(lon_str)
            
            print(f"Parsed coordinates - lat: {lat}, lon: {lon}, address: {address}")

            # Create marker with popup showing the address (Leaflet expects EPSG:4326)
            marker = dl.Marker(
                position=[lat, lon],
                children=[
                    dl.Tooltip(address),
                    dl.Popup(address)
                ]
            )

            # Create viewport dict to force map re-centering
            # This is more reliable than updating center and zoom separately
            viewport = {
                'center': [lat, lon],
                'zoom': 18,
                'transition': 'flyTo'  # Smooth animation to new location
            }

            # Update coordinates store
            coordinates_data = {"lat": lat, "lon": lon, "address": address}

            print(f"Map viewport updated to: center=[{lat}, {lon}], zoom=18")
            return viewport, [marker], coordinates_data

        except (ValueError, IndexError) as error:
            print(f"Error parsing dropdown value '{dropdown_value}': {error}")
            import traceback
            traceback.print_exc()
            return no_update, no_update, no_update

    # Callback for nearby transport page search bar
    @app.callback(
        Output('nearby-transport-search', 'options'),
        Input('nearby-transport-search', 'search_value'),
        Input('nearby-transport-search', 'value')
    )
    def update_nearby_transport_search_options(search_value, selected_value):
        """
        Update dropdown with top 5 search results from OneMap API as user types.
        For nearby transport page.

        Args:
            search_value: Text entered in the search input
            selected_value: Currently selected value

        Returns:
            List of top 5 dropdown options with address labels and lat/lon values
        """
        # If user has selected a value, keep it in options
        if selected_value and not search_value:
            try:
                parts = selected_value.split(',', 2)
                address = parts[2] if len(parts) > 2 else "Selected Location"
                return [{'label': address, 'value': selected_value}]
            except (ValueError, IndexError):
                return []

        if not search_value or len(str(search_value).strip()) < 3:
            return []

        future = search_location_via_onemap_info_async(search_value)
        results = future.result() if future else []
        options = []

        # Limit to top 5 most relevant results
        for result in results[:5]:
            # Extract relevant fields from OneMap API response
            address = result.get('ADDRESS', 'Unknown Address')
            building = result.get('BUILDING', '')
            postal = result.get('POSTAL', '')
            lat = result.get('LATITUDE')
            lon = result.get('LONGITUDE')

            if lat and lon:
                # Create a descriptive label
                label_parts = []
                if building:
                    label_parts.append(building)
                if address:
                    label_parts.append(address)
                if postal:
                    label_parts.append(f"(S{postal})")

                label = ', '.join(label_parts) if label_parts else address

                # Store coordinates in EPSG:4326 format (Leaflet expects this)
                options.append({
                    'label': label,
                    'value': f'{lat},{lon},{address}'  # Store lat,lon,address in EPSG:4326
                })

        print(f"Generated {len(options)} dropdown options for nearby transport (top 5)")
        return options

    @app.callback(
        [Output('nearby-transport-map', 'viewport'),
         Output('nearby-transport-location-store', 'data'),
         Output('nearby-transport-search-marker', 'children')],
        Input('nearby-transport-search', 'value')
    )
    def update_nearby_transport_map_from_search(dropdown_value):
        """
        Update nearby transport map when user selects a location from the dropdown.
        Centers the map on the selected location and adds a marker.
        Also updates the location store.

        Args:
            dropdown_value: Selected value from dropdown (format: 'lat,lon,address')

        Returns:
            Tuple of (viewport dict, location store data, marker)
        """
        print(f"Nearby transport callback triggered with dropdown_value: {dropdown_value}")

        if not dropdown_value:
            print("No dropdown value, returning no_update")
            return no_update, no_update, []



        try:
            # Parse the dropdown value
            # Format: lat,lon,address,postal (postal is optional)
            parts = dropdown_value.split(',')
            lat_str, lon_str = parts[0], parts[1]
            address = parts[2] if len(parts) > 2 else "Selected Location"
            
            # Search for 6-digit postal code in the dropdown_value
            postal_code = ""
            postal_match = re.search(r'\b\d{6}\b', dropdown_value)
            if postal_match:
                postal_code = postal_match.group(0)

            lat, lon = float(lat_str), float(lon_str)

            print(f"Parsed coordinates - lat: {lat}, lon: {lon}, address: {address}, postal: {postal_code}")

            # Create marker with popup showing the address (Leaflet expects EPSG:4326)
            marker = dl.Marker(
                position=[lat, lon],
                children=[
                    dl.Tooltip(address),
                    dl.Popup(address)
                ]
            )

            # Create viewport dict to force map re-centering
            # This is more reliable than updating center and zoom separately
            viewport = {
                'center': [lat, lon],
                'zoom': 18,
                'transition': 'flyTo'  # Smooth animation to new location
            }

            # Update location store with postal code if available
            location_data = {
                "lat": lat,
                "lon": lon,
                "address": address,
                # Seed viewport so nearby tab features can use map center immediately
                "viewport": {"center": [lat, lon], "zoom": 18}
            }
            if postal_code:
                location_data["postal_code"] = postal_code

            print(f"Nearby transport map viewport updated to: center=[{lat}, {lon}], zoom=18")
            return viewport, location_data, [marker]

        except (ValueError, IndexError) as error:
            print(f"Error parsing dropdown value '{dropdown_value}': {error}")
            import traceback
            traceback.print_exc()
            return no_update, no_update, []

    # Traffic Incidents toggle state callback
    @app.callback(
        Output('main-traffic-incidents-toggle-state', 'data'),
        Input('toggle-main-traffic-incidents', 'n_clicks'),
        State('main-traffic-incidents-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def update_traffic_incidents_toggle_state(n_clicks, current_state):
        """Update traffic incidents toggle state in store."""
        if n_clicks is None or n_clicks == 0:
            return False
        return not current_state

    # Traffic Incidents toggle button label callback
    @app.callback(
        Output('toggle-main-traffic-incidents', 'children'),
        Input('toggle-main-traffic-incidents', 'n_clicks'),
        State('main-traffic-incidents-toggle-state', 'data')
    )
    def toggle_traffic_incidents_button_label(n_clicks, current_state):
        """
        Toggle Traffic Incidents button label based on current state.

        Args:
            n_clicks: Number of button clicks
            current_state: Current toggle state from store

        Returns:
            Button label
        """
        if n_clicks is None or n_clicks == 0:
            # Default state: hidden
            return "🚧 Show Traffic Incidents"

        # Show text based on current state (before toggle)
        # If currently visible (True), show "Hide", otherwise show "Show"
        if current_state:
            return "🚧 Hide Traffic Incidents"
        return "🚧 Show Traffic Incidents"

    # Traffic Incidents markers callback
    @app.callback(
        [Output('main-traffic-incidents-markers', 'children'),
         Output('main-traffic-incidents-legend', 'style')],
        [Input('main-traffic-incidents-toggle-state', 'data'),
         Input('interval-component', 'n_intervals')]
    )
    def update_main_traffic_incidents_markers(show_incidents, n_intervals):
        """Update traffic incidents markers on main map and show/hide legend."""
        _ = n_intervals  # Used for periodic refresh

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

        if not show_incidents:
            return [], legend_style

        # Import here to avoid circular imports
        from callbacks.transport_callback import (
            fetch_traffic_incidents_data_async,
            fetch_faulty_traffic_lights_data_async,
            create_traffic_incidents_markers
        )

        # Fetch data
        future_incidents = fetch_traffic_incidents_data_async()
        future_faulty = fetch_faulty_traffic_lights_data_async()
        incidents_data = future_incidents.result() if future_incidents else None
        faulty_lights_data = future_faulty.result() if future_faulty else None

        # Create markers using existing function
        markers = create_traffic_incidents_markers(incidents_data, faulty_lights_data)

        return markers, legend_style
