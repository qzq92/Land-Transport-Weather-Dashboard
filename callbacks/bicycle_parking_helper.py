"""
Helper functions for bicycle parking data fetching and processing.
Used specifically for the Nearby Transportation & Parking tab.
"""
import os
from datetime import datetime
from dash import html
import dash_leaflet as dl
import base64
from utils.async_fetcher import run_in_thread


@run_in_thread
def fetch_bicycle_parking_from_api_async(lat: float, lon: float, dist_m: int = 300, haversine_func=None) -> list:
    """
    Fetch bicycle parking data directly from LTA DataMall API for a specific location.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        dist_m: Search radius in meters (default: 300)
        haversine_func: Function to calculate distance between coordinates
    
    Returns:
        List of bicycle parking dictionaries with distance information
    """
    import requests
    
    BICYCLE_PARKING_URL = "https://datamall2.mytransport.sg/ltaodataservice/BicycleParkingv2"
    
    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found")
        return []
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    # Convert meters to km (API expects distance in km, rounded to 1 decimal)
    dist_km = round(dist_m / 1000, 1)
    
    params = {
        "Lat": lat,
        "Long": lon,
        "Dist": dist_km
    }
    
    try:
        response = requests.get(BICYCLE_PARKING_URL, headers=headers, params=params, timeout=30)
        if 200 <= response.status_code < 300:
            data = response.json()
            parking_locations = data.get('value', [])
            
            # Process and calculate distances
            processed_results = []
            for loc in parking_locations:
                try:
                    parking_lat = float(loc.get('Latitude', 0))
                    parking_lon = float(loc.get('Longitude', 0))
                    
                    # Calculate distance if haversine function provided
                    distance_m = haversine_func(lat, lon, parking_lat, parking_lon) if haversine_func else 0
                    
                    processed_results.append({
                        'description': loc.get('Description', 'N/A'),
                        'rack_type': loc.get('RackType', 'N/A'),
                        'rack_count': loc.get('RackCount', 'N/A'),
                        'shelter_indicator': loc.get('ShelterIndicator', 'N'),
                        'latitude': parking_lat,
                        'longitude': parking_lon,
                        'distance_m': distance_m,
                    })
                except (ValueError, TypeError, KeyError):
                    continue
            
            # Sort by distance
            processed_results.sort(key=lambda x: x['distance_m'])
            return processed_results
    except Exception as e:
        print(f"Error fetching bicycle parking from API: {e}")
        return []


def create_nearby_bicycle_parking_markers(bicycle_parking_list):
    """
    Create map markers for nearby bicycle parking locations from processed list.
    
    Args:
        bicycle_parking_list: List of processed bicycle parking dictionaries
    
    Returns:
        List of dl.Marker components with bicycle rack icons
    """
    markers = []
    
    if not bicycle_parking_list:
        return markers
    
    for parking in bicycle_parking_list:
        try:
            latitude = parking.get('latitude', 0)
            longitude = parking.get('longitude', 0)
            description = parking.get('description', 'N/A')
            rack_type = parking.get('rack_type', 'N/A')
            rack_count = parking.get('rack_count', 'N/A')
            shelter_indicator = parking.get('shelter_indicator', 'N')
            
            if latitude == 0 or longitude == 0:
                continue
            
            # Determine sheltered/unsheltered status
            shelter_status = 'sheltered' if shelter_indicator == 'Y' else 'unsheltered'
            
            # Create tooltip with formatted information
            tooltip_html = (
                f"{description} ({shelter_status})\n"
                f"RackType: {rack_type}\n"
                f"RackCount: {rack_count}"
            )
            
            # Create bicycle rack icon SVG - different icons for sheltered vs unsheltered
            if shelter_indicator == 'Y':
                # Sheltered: bicycle rack with roof/shelter
                bicycle_rack_svg = (
                    '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                    '<rect x="2" y="2" width="20" height="20" rx="2" fill="#9C27B0" opacity="0.2" stroke="#9C27B0" stroke-width="1.5"/>'
                    '<path d="M 3 3 L 3 19 M 7 3 L 7 19 M 11 3 L 11 19 M 15 3 L 15 19 M 19 3 L 19 19" '
                    'stroke="#9C27B0" stroke-width="2.5" stroke-linecap="round"/>'
                    '<path d="M 4 19 L 20 19" stroke="#9C27B0" stroke-width="2.5" stroke-linecap="round"/>'
                    '<path d="M 2 3 Q 12 1 22 3" stroke="#9C27B0" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
                    '<path d="M 2 2 L 22 2" stroke="#9C27B0" stroke-width="2.5" stroke-linecap="round"/>'
                    '</svg>'
                )
            else:
                # Unsheltered: simple bicycle rack without roof
                bicycle_rack_svg = (
                    '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                    '<rect x="2" y="2" width="20" height="20" rx="2" fill="#9C27B0" opacity="0.2" stroke="#9C27B0" stroke-width="1.5"/>'
                    '<path d="M 6 4 L 6 20 M 10 4 L 10 20 M 14 4 L 14 20 M 18 4 L 18 20" '
                    'stroke="#9C27B0" stroke-width="2.5" stroke-linecap="round"/>'
                    '<path d="M 4 20 L 20 20" stroke="#9C27B0" stroke-width="2.5" stroke-linecap="round"/>'
                    '</svg>'
                )
            bicycle_rack_svg_base64 = base64.b64encode(bicycle_rack_svg.encode()).decode()
            
            bicycle_rack_icon = {
                "iconUrl": f"data:image/svg+xml;base64,{bicycle_rack_svg_base64}",
                "iconSize": [24, 24],
                "iconAnchor": [12, 24],
                "popupAnchor": [0, -24],
            }
            
            # Create marker with bicycle rack icon
            markers.append(
                dl.Marker(
                    position=[latitude, longitude],
                    icon=bicycle_rack_icon,
                    children=[
                        dl.Tooltip(html.Pre(tooltip_html, style={"margin": "0", "fontFamily": "inherit"})),
                    ]
                )
            )
        except (ValueError, TypeError, KeyError):
            continue
    
    return markers

