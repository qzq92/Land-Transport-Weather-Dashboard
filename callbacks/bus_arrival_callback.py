"""
Callback functions for handling bus arrival information.
"""
import re
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
from dash import Input, Output, State, html, callback_context, no_update, ALL
import dash_leaflet as dl
# Import fetch_bus_stops_data from transport_callback to avoid circular import
# This is done inside the function to prevent circular import issues

# API URLs
BUS_ARRIVAL_URL = "https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival"


def fetch_bus_arrival_data(bus_stop_code: str) -> Optional[Dict[str, Any]]:
    """
    Fetch bus arrival data for a specific bus stop from LTA DataMall API.
    
    Args:
        bus_stop_code: Bus stop code (e.g., "83139")
    
    Returns:
        Dictionary containing bus arrival data, or None if error
    """
    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    params = {
        "BusStopCode": bus_stop_code
    }
    
    try:
        import requests
        response = requests.get(BUS_ARRIVAL_URL, headers=headers, params=params, timeout=10)
        if 200 <= response.status_code < 300:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching bus arrival data for stop {bus_stop_code}: {e}")
        return None


def format_arrival_time_minutes(estimated_arrival: str) -> str:
    """
    Calculate and format arrival time in minutes from current time.
    
    Args:
        estimated_arrival: ISO format datetime string (e.g., "2024-08-14T16:41:48+08:00")
    
    Returns:
        String like "5 min" or "Arriving" or "N/A"
    """
    if not estimated_arrival:
        return "N/A"
    
    try:
        # Parse the estimated arrival time
        if isinstance(estimated_arrival, str):
            # Remove timezone info for parsing
            arrival_str = estimated_arrival.replace('+08:00', '').replace('Z', '')
            arrival_dt = datetime.strptime(arrival_str, "%Y-%m-%dT%H:%M:%S")
        else:
            arrival_dt = estimated_arrival
        
        # Get current time
        current_dt = datetime.now()
        
        # Calculate difference
        time_diff = arrival_dt - current_dt
        total_seconds = time_diff.total_seconds()
        
        if total_seconds < 0:
            return "Departed"
        elif total_seconds < 60:
            return "Arriving"
        else:
            minutes = int(total_seconds / 60)
            return f"{minutes} min"
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Error formatting arrival time '{estimated_arrival}': {e}")
        return "N/A"


def format_bus_arrival_display(arrival_data: Optional[Dict[str, Any]], bus_stop_code: str) -> html.Div:
    """
    Format bus arrival data for display in the panel.
    
    Args:
        arrival_data: Dictionary containing bus arrival API response
        bus_stop_code: Bus stop code for display
    
    Returns:
        HTML Div containing formatted bus arrival information
    """
    if not arrival_data:
        return html.Div(
            html.P(
                "Unable to fetch bus arrival data. Please try again.",
                style={
                    "color": "#999",
                    "textAlign": "center",
                    "fontSize": "0.75rem",
                    "margin": "0.5rem 0",
                }
            )
        )
    
    services = arrival_data.get('Services', [])
    
    if not services:
        return html.Div(
            html.P(
                "No bus services available at this stop.",
                style={
                    "color": "#999",
                    "textAlign": "center",
                    "fontSize": "0.75rem",
                    "margin": "0.5rem 0",
                }
            )
        )
    
    # Sort services by service number in increasing numerical order
    def get_service_number(service):
        """Extract numeric part of service number for sorting."""
        service_no = service.get('ServiceNo', 'N/A')
        if service_no == 'N/A':
            return float('inf')  # Put N/A at the end
        try:
            # Extract numeric part (handles cases like "21", "21A", "CT8", etc.)
            match = re.search(r'\d+', str(service_no))
            if match:
                return int(match.group())
            return float('inf')  # If no number found, put at end
        except (ValueError, TypeError):
            return float('inf')
    
    services = sorted(services, key=get_service_number)
    
    # Create table rows
    table_rows = []
    
    # Header row
    table_rows.append(
        html.Tr(
            [
                html.Td(
                    "Service (Operator)",
                    style={
                        "padding": "0.375rem",
                        "fontWeight": "600",
                        "fontSize": "0.6875rem",
                        "color": "#fff",
                        "border": "0.0625rem solid #555",
                        "textAlign": "left",
                    }
                ),
                html.Td(
                    "Next Bus Arrival",
                    style={
                        "padding": "0.375rem",
                        "fontWeight": "600",
                        "fontSize": "0.6875rem",
                        "color": "#fff",
                        "border": "0.0625rem solid #555",
                        "textAlign": "center",
                    }
                ),
            ]
        )
    )
    
    for service in services:
        service_no = service.get('ServiceNo', 'N/A')
        operator = service.get('Operator', 'N/A')
        
        # Get arrival times for NextBus, NextBus2, NextBus3
        next_bus = service.get('NextBus', {})
        next_bus2 = service.get('NextBus2', {})
        next_bus3 = service.get('NextBus3', {})
        
        estimated_arrival_1 = next_bus.get('EstimatedArrival', '') if next_bus else ''
        estimated_arrival_2 = next_bus2.get('EstimatedArrival', '') if next_bus2 else ''
        estimated_arrival_3 = next_bus3.get('EstimatedArrival', '') if next_bus3 else ''
        
        arrival_1_min = format_arrival_time_minutes(estimated_arrival_1)
        arrival_2_min = format_arrival_time_minutes(estimated_arrival_2)
        arrival_3_min = format_arrival_time_minutes(estimated_arrival_3)
        
        # Build timing blocks as inline spans
        timing_spans = []
        
        # First arrival time
        first_arrival_text = arrival_1_min
        is_minute_based = arrival_1_min not in ("N/A", "Departed", "Arriving") and "min" in arrival_1_min
        if is_minute_based:
            first_arrival_text = f"{arrival_1_min}"
        
        standard_bg_color = "#2E7D32"
        # Determine background color
        if arrival_1_min == "Departed":
            bg_color = "#666"
        elif arrival_1_min == "Arriving":
            bg_color = "#4CAF50"
        else:
            bg_color = standard_bg_color
        
        timing_spans.append(
            html.Span(
                first_arrival_text,
                style={
                    "backgroundColor": bg_color,
                    "color": "#fff",
                    "padding": "0.125rem 0.375rem",
                    "borderRadius": "0.1875rem",
                    "fontSize": "0.7rem",
                    "fontWeight": "600",
                    "marginRight": "0.25rem",
                }
            )
        )
        
        # Second arrival time if available
        if arrival_2_min != "N/A":
            timing_spans.append(
                html.Span(
                    arrival_2_min,
                    style={
                        "backgroundColor": standard_bg_color if arrival_2_min != "Departed" else "#666",
                        "color": "#fff",
                        "padding": "0.125rem 0.375rem",
                        "borderRadius": "0.1875rem",
                        "fontSize": "0.7rem",
                        "fontWeight": "600",
                        "marginRight": "0.25rem",
                    }
                )
            )
        
        # Third arrival time if available
        if arrival_3_min != "N/A":
            timing_spans.append(
                html.Span(
                    arrival_3_min,
                    style={
                        "backgroundColor": standard_bg_color if arrival_3_min != "Departed" else "#666",
                        "color": "#fff",
                        "padding": "0.125rem 0.375rem",
                        "borderRadius": "0.1875rem",
                        "fontSize": "0.7rem",
                        "fontWeight": "600",
                    }
                )
            )
        
        # Create table row
        table_rows.append(
            html.Tr(
                [
                    html.Td(
                        f"{service_no} ({operator})",
                        style={
                            "padding": "0.375rem",
                            "fontSize": "0.6875rem",
                            "color": "#fff",
                            "border": "0.0625rem solid #555",
                            "textAlign": "left",
                        }
                    ),
                    html.Td(
                        timing_spans if timing_spans else [html.Span("N/A", style={"color": "#999"})],
                        style={
                            "padding": "0.375rem",
                            "fontSize": "0.6875rem",
                            "color": "#fff",
                            "border": "0.0625rem solid #555",
                            "textAlign": "center",
                        }
                    ),
                ]
            )
        )
    
    return html.Div(
        children=[
            html.Div(
                f"Bus Stop: {bus_stop_code}",
                style={
                    "color": "#fff",
                    "fontWeight": "600",
                    "fontSize": "0.875rem",
                    "marginBottom": "0.375rem",
                }
            ),
            html.Table(
                style={
                    "width": "100%",
                    "borderCollapse": "collapse",
                    "fontSize": "0.6875rem",
                },
                children=table_rows
            ),
        ]
    )


def register_bus_arrival_callbacks(app):
    """
    Register all bus arrival related callbacks.
    
    Args:
        app: Dash application instance
    """
    @app.callback(
        Output('current-bus-stop-code', 'data'),
        [Input('bus-stop-search-btn', 'n_clicks'),
         Input({'type': 'bus-stop-marker', 'index': ALL}, 'n_clicks')],
        [State('bus-stop-search-input', 'value')],
        prevent_initial_call=True
    )
    def update_current_bus_stop_code(_search_clicks, marker_clicks, search_value):
        """Store the current bus stop code for auto-refresh."""
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        
        trigger_id = ctx.triggered[0]['prop_id']
        trigger_value = ctx.triggered[0]['value']
        bus_stop_code = None
        
        # Check if a bus stop marker was clicked
        if 'bus-stop-marker' in trigger_id:
            if trigger_value is None or trigger_value == 0:
                return no_update
            marker_id_str = trigger_id.split('.')[0]
            marker_id = json.loads(marker_id_str)
            bus_stop_code = marker_id['index']
        # Check if search button was clicked
        elif 'bus-stop-search-btn' in trigger_id:
            if search_value and search_value.strip().isdigit() and len(search_value.strip()) == 5:
                bus_stop_code = search_value.strip()
        
        return bus_stop_code if bus_stop_code else no_update

    @app.callback(
        [Output('bus-arrival-content', 'children'),
         Output('bus-arrival-popup-layer', 'children'),
         Output('bus-stop-search-input', 'value')],
        [Input('bus-stop-search-btn', 'n_clicks'),
         Input({'type': 'bus-stop-marker', 'index': ALL}, 'n_clicks'),
         Input('bus-arrival-interval', 'n_intervals')],
        [State('bus-stop-search-input', 'value'),
         State('bus-stops-toggle-state', 'data'),
         State('current-bus-stop-code', 'data')],
        prevent_initial_call=True
    )
    def update_bus_arrival_display(_search_clicks, marker_clicks, _interval_n, search_value, bus_stops_visible, stored_bus_stop_code):
        """
        Update bus arrival display when search is performed, a bus stop marker is clicked, or interval triggers.
        Fills the textbox and shows the arrival info in the side panel.
        Note: Map viewport is not auto-centered to allow user to freely navigate.
        """
        # Determine which input triggered the callback
        ctx = callback_context
        if not ctx.triggered:
            return no_update, [], no_update
        
        trigger_id = ctx.triggered[0]['prop_id']
        trigger_value = ctx.triggered[0]['value']
        bus_stop_code = None
        
        # Check if interval triggered (auto-refresh)
        if 'bus-arrival-interval' in trigger_id:
            # Use stored bus stop code for auto-refresh
            if stored_bus_stop_code:
                bus_stop_code = stored_bus_stop_code
            else:
                return no_update, [], no_update
        
        # Check if a bus stop marker was clicked
        elif 'bus-stop-marker' in trigger_id:
            # Validate that this was an actual click (n_clicks must be a positive number)
            if trigger_value is None or trigger_value == 0:
                return no_update, [], no_update
            
            # Extract the bus stop code from the triggered marker ID
            marker_id_str = trigger_id.split('.')[0]
            marker_id = json.loads(marker_id_str)
            bus_stop_code = marker_id['index']
        
        # Check if search button was clicked
        elif 'bus-stop-search-btn' in trigger_id:
            if not search_value:
                return html.P(
                    "Please enter a bus stop code",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                        "margin": "0.5rem 0",
                    }
                ), [], no_update
            
            # Validate bus stop code (must be 5 digits)
            search_value = search_value.strip()
            if not search_value.isdigit() or len(search_value) != 5:
                return html.P(
                    "Invalid bus stop code. Please enter a 5-digit number.",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                        "margin": "0.5rem 0",
                    }
                ), [], no_update
            
            bus_stop_code = search_value
        
        if not bus_stop_code:
            return no_update, [], no_update
        
        # Fetch bus arrival data
        arrival_data = fetch_bus_arrival_data(bus_stop_code)
        
        # Coordinate lookup for bus stop
        lat, lon = None, None
        from callbacks.transport_callback import fetch_bus_stops_data
        bus_stops_data = fetch_bus_stops_data()
        if bus_stops_data and 'value' in bus_stops_data:
            for bs in bus_stops_data['value']:
                if bs.get('BusStopCode') == bus_stop_code:
                    lat = float(bs.get('Latitude', 0))
                    lon = float(bs.get('Longitude', 0))
                    break
        
        # Format and return display
        formatted_arrival = format_bus_arrival_display(arrival_data, bus_stop_code)
        
        # If coordinates found, update map and return highlight circle
        if lat and lon:
            # Create a highlight circle around the bus stop
            highlight_circle = dl.Circle(
                center=[lat, lon],
                radius=30,  # 30 meters radius
                color="#FF4136",  # Red color
                fill=True,
                fillColor="#FF4136",
                fillOpacity=0.2,
                weight=2,
                dashArray="5, 5"  # Dashed line
            )
            
            # Return with highlight displayed and textbox updated
            # The arrival content is now shown in the side panel (bus-arrival-content)
            # Map viewport is not auto-centered to allow user to freely navigate
            return formatted_arrival, [highlight_circle], bus_stop_code
        
        # If no coordinates found, just display the arrival info without highlighting
        return formatted_arrival, [], bus_stop_code

