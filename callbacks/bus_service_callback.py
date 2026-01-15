"""
Callback functions for handling bus service information.
"""
from typing import Optional, Dict, List, Any
from dash import Input, Output, State, html
from callbacks.transport_callback import fetch_bus_routes_data, fetch_bus_routes_data_async, fetch_bus_stops_data
from components.metric_card import create_metric_value_display


def _format_route_distance(direction_routes: List[Dict[str, Any]]) -> str:
    """
    Extract and format the total distance for a route direction.
    Distance is typically cumulative, so the last segment contains the total distance.
    
    Args:
        direction_routes: List of route segments for a direction
    
    Returns:
        Formatted distance string (e.g., "Distance: 12.5 km")
    """
    if not direction_routes:
        return "Distance: N/A"
    
    # Get distance from the last route segment (cumulative distance)
    last_route = direction_routes[-1]
    distance = last_route.get('Distance')
    
    if distance is None:
        return "Distance: N/A"
    
    try:
        distance_float = float(distance)
        # Format distance - if less than 1 km, show in meters, otherwise show in km
        if distance_float < 1.0:
            return f"Distance: {int(distance_float * 1000)}m"
        else:
            return f"Distance: {distance_float:.2f} km"
    except (ValueError, TypeError):
        return f"Distance: {distance}"


def _create_bus_timing_table(timing_info: Dict[str, Any]) -> Optional[html.Div]:
    """
    Create a 3x4 table grid showing first and last bus times for weekdays, Saturday, and Sunday.
    
    Args:
        timing_info: Dictionary containing bus route timing information
    
    Returns:
        HTML Div containing the timing table, or None if no timing data available
    """
    # Extract timing fields
    wd_first = timing_info.get('WD_FirstBus', 'N/A')
    wd_last = timing_info.get('WD_LastBus', 'N/A')
    sat_first = timing_info.get('SAT_FirstBus', 'N/A')
    sat_last = timing_info.get('SAT_LastBus', 'N/A')
    sun_first = timing_info.get('SUN_FirstBus', 'N/A')
    sun_last = timing_info.get('SUN_LastBus', 'N/A')
    
    # Check if any timing data exists
    if all(x == 'N/A' for x in [wd_first, wd_last, sat_first, sat_last, sun_first, sun_last]):
        return None
    
    # Format time values (handle HHMM format)
    def format_time(time_str):
        if time_str == 'N/A' or not time_str:
            return 'N/A'
        try:
            # Handle HHMM format (e.g., "0530" -> "05:30")
            if isinstance(time_str, str) and len(time_str) == 4 and time_str.isdigit():
                return f"{time_str[:2]}:{time_str[2:]}"
            return str(time_str)
        except (ValueError, TypeError, AttributeError):
            return str(time_str)
    
    wd_first_formatted = format_time(wd_first)
    wd_last_formatted = format_time(wd_last)
    sat_first_formatted = format_time(sat_first)
    sat_last_formatted = format_time(sat_last)
    sun_first_formatted = format_time(sun_first)
    sun_last_formatted = format_time(sun_last)
    
    # Create table with 3 rows (Weekdays, Saturday, Sunday) and 4 columns
    # Columns: Day Type, First Bus, Last Bus, (empty for spacing)
    table_rows = [
        # Header row
        html.Tr(
            [
                html.Td("Day", style={
                    "padding": "0.375rem",
                    "fontWeight": "600",
                    "fontSize": "0.6875rem",
                    "color": "#4169E1",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td("First Bus", style={
                    "padding": "0.375rem",
                    "fontWeight": "600",
                    "fontSize": "0.6875rem",
                    "color": "#4169E1",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td("Last Bus", style={
                    "padding": "0.375rem",
                    "fontWeight": "600",
                    "fontSize": "0.6875rem",
                    "color": "#4169E1",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td("", style={
                    "padding": "0.375rem",
                    "border": "0.0625rem solid #555",
                    "width": "1rem",
                }),
            ]
        ),
        # Weekdays row
        html.Tr(
            [
                html.Td("Weekdays", style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#ccc",
                    "border": "0.0625rem solid #555",
                    "textAlign": "left",
                }),
                html.Td(wd_first_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(wd_last_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td("", style={
                    "padding": "0.375rem",
                    "border": "0.0625rem solid #555",
                }),
            ]
        ),
        # Saturday row
        html.Tr(
            [
                html.Td("Saturday", style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#ccc",
                    "border": "0.0625rem solid #555",
                    "textAlign": "left",
                }),
                html.Td(sat_first_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(sat_last_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td("", style={
                    "padding": "0.375rem",
                    "border": "0.0625rem solid #555",
                }),
            ]
        ),
        # Sunday row
        html.Tr(
            [
                html.Td("Sunday", style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#ccc",
                    "border": "0.0625rem solid #555",
                    "textAlign": "left",
                }),
                html.Td(sun_first_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(sun_last_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td("", style={
                    "padding": "0.375rem",
                    "border": "0.0625rem solid #555",
                }),
            ]
        ),
    ]
    
    return html.Div(
        style={
            "backgroundColor": "#3a4a5a",
            "padding": "0.5rem",
            "borderRadius": "0.25rem",
            "marginBottom": "0.5rem",
        },
        children=[
            html.Span(
                "Bus Operating Hours",
                style={
                    "color": "#4169E1",
                    "fontWeight": "bold",
                    "fontSize": "0.75rem",
                    "display": "block",
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
            )
        ]
    )


def format_bus_service_search_display(service_no: str, routes_data: Optional[Dict[str, Any]]) -> html.Div:
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


def register_bus_service_callbacks(app):
    """
    Register all bus service related callbacks.
    
    Args:
        app: Dash application instance
    """
    @app.callback(
        Output('bus-services-count-value', 'children'),
        Input('transport-interval', 'n_intervals')
    )
    def update_bus_services_count(n_intervals: int) -> html.Div:
        """
        Update bus services count display using async data fetching.
        
        Args:
            n_intervals: Number of intervals (from dcc.Interval component)
        
        Returns:
            HTML Div with bus services count
        """
        _ = n_intervals  # Used for periodic refresh

        # Fetch data asynchronously
        future = fetch_bus_routes_data_async()
        data: Optional[Dict[str, Any]] = future.result() if future else None
        
        # Calculate unique bus services count
        bus_services_count = 0
        if isinstance(data, dict):
            routes_list = data.get('value', [])
            if isinstance(routes_list, list):
                # Extract unique service numbers
                service_numbers = set()
                for route in routes_list:
                    service_no = route.get('ServiceNo', '')
                    if service_no:
                        service_numbers.add(service_no)
                bus_services_count = len(service_numbers)
        
        return create_metric_value_display(str(bus_services_count), color="#4169E1")

    @app.callback(
        Output('bus-service-search-content', 'children'),
        Input('bus-service-search-btn', 'n_clicks'),
        State('bus-service-search-input', 'value'),
        prevent_initial_call=True
    )
    def update_bus_service_search_display(_n_clicks, search_value):
        """
        Update bus service search display based on user input.
        
        Args:
            _n_clicks: Number of times search button was clicked
            search_value: Bus service number entered by user
        
        Returns:
            HTML Div containing formatted bus service route information
        """
        if not search_value:
            return html.P(
                "Please enter a bus service number",
                style={
                    "color": "#ff6b6b",
                    "textAlign": "center",
                    "fontSize": "0.75rem",
                    "margin": "0.5rem 0",
                }
            )
        
        # Clean and validate input
        service_no = search_value.strip().upper()
        
        if not service_no:
            return html.P(
                "Invalid bus service number. Please enter a valid service number.",
                style={
                    "color": "#ff6b6b",
                    "textAlign": "center",
                    "fontSize": "0.75rem",
                    "margin": "0.5rem 0",
                }
            )
        
        # Fetch bus routes data
        routes_data = fetch_bus_routes_data()
        
        # Format and return display
        return format_bus_service_search_display(service_no, routes_data)

