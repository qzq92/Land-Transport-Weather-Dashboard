"""
Callback functions for handling bus service information.
"""
from typing import Optional, Dict, List, Any
from dash import Input, Output, State, html, ALL, MATCH, callback_context
import dash_leaflet as dl
from callbacks.transport_callback import (
    fetch_bus_routes_data,
    fetch_bus_routes_data_async,
    fetch_bus_stops_data,
    fetch_bus_services_data_async
)
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


def _create_bus_timing_table(timing_info: Dict[str, Any], service_no: str = None, bus_services_data: Optional[Dict[str, Any]] = None) -> Optional[html.Div]:
    """
    Create a table showing first and last bus times for weekdays, Saturday, and Sunday,
    with frequency columns (AM Peak, AM Offpeak, PM Peak, PM Offpeak).
    
    Args:
        timing_info: Dictionary containing bus route timing information
        service_no: Bus service number to look up frequency data
        bus_services_data: Dictionary containing bus services data from LTA API
    
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
    
    # Extract frequency data from bus services data
    am_peak_freq = "N/A"
    am_offpeak_freq = "N/A"
    pm_peak_freq = "N/A"
    pm_offpeak_freq = "N/A"
    
    if service_no and bus_services_data:
        services = []
        if isinstance(bus_services_data, dict):
            if "value" in bus_services_data:
                services = bus_services_data.get("value", [])
            elif isinstance(bus_services_data, list):
                services = bus_services_data
        elif isinstance(bus_services_data, list):
            services = bus_services_data
        
        # Find matching service
        for service in services:
            if isinstance(service, dict):
                service_number = service.get("ServiceNo", service.get("serviceNo", ""))
                if str(service_number).upper() == str(service_no).upper():
                    am_peak_freq = service.get("AM_Peak_Freq", service.get("amPeakFreq", "N/A"))
                    am_offpeak_freq = service.get("AM_Offpeak_Freq", service.get("amOffpeakFreq", "N/A"))
                    pm_peak_freq = service.get("PM_Peak_Freq", service.get("pmPeakFreq", "N/A"))
                    pm_offpeak_freq = service.get("PM_Offpeak_Freq", service.get("pmOffpeakFreq", "N/A"))
                    break
    
    # Format frequency values
    def format_frequency(freq):
        if freq == "N/A" or not freq or freq == "":
            return "N/A"
        try:
            freq_str = str(freq)
            # If it's a number, add " min" suffix
            if freq_str.replace(".", "").isdigit():
                return f"{freq_str} min"
            return freq_str
        except (ValueError, TypeError, AttributeError):
            return str(freq) if freq else "N/A"
    
    am_peak_freq_formatted = format_frequency(am_peak_freq)
    am_offpeak_freq_formatted = format_frequency(am_offpeak_freq)
    pm_peak_freq_formatted = format_frequency(pm_peak_freq)
    pm_offpeak_freq_formatted = format_frequency(pm_offpeak_freq)
    
    # Create table with 3 rows (Weekdays, Saturday, Sunday) and 7 columns
    # Columns: Day Type, First Bus, Last Bus, AM Peak Frequency, AM Offpeak Frequency, PM Peak Frequency, PM Offpeak Frequency
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
                html.Td("AM Peak Frequency", style={
                    "padding": "0.375rem",
                    "fontWeight": "600",
                    "fontSize": "0.6875rem",
                    "color": "#4169E1",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td("AM Offpeak Frequency", style={
                    "padding": "0.375rem",
                    "fontWeight": "600",
                    "fontSize": "0.6875rem",
                    "color": "#4169E1",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td("PM Peak Frequency", style={
                    "padding": "0.375rem",
                    "fontWeight": "600",
                    "fontSize": "0.6875rem",
                    "color": "#4169E1",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td("PM Offpeak Frequency", style={
                    "padding": "0.375rem",
                    "fontWeight": "600",
                    "fontSize": "0.6875rem",
                    "color": "#4169E1",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
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
                html.Td(am_peak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(am_offpeak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(pm_peak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(pm_offpeak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
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
                html.Td(am_peak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(am_offpeak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(pm_peak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(pm_offpeak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
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
                html.Td(am_peak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(am_offpeak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(pm_peak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
                }),
                html.Td(pm_offpeak_freq_formatted, style={
                    "padding": "0.375rem",
                    "fontSize": "0.6875rem",
                    "color": "#fff",
                    "border": "0.0625rem solid #555",
                    "textAlign": "center",
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


def _create_bus_stops_list(direction_routes: List[Dict[str, Any]], bus_stop_map: Dict[str, str]) -> html.Div:
    """
    Create a formatted list of bus stops for a direction.
    
    Args:
        direction_routes: List of route segments for a direction (sorted by stop sequence)
        bus_stop_map: Dictionary mapping bus stop codes to names
    
    Returns:
        HTML Div containing formatted list of bus stops
    """
    stop_items = []
    
    for route in direction_routes:
        seq = route.get('StopSequence', 0)
        code = route.get('BusStopCode', 'N/A')
        name = bus_stop_map.get(code, 'N/A')
        
        stop_items.append(
            html.Div(
                f"{seq}. {name} ({code})",
                style={
                    "color": "#ccc",
                    "fontSize": "0.65rem",
                    "padding": "0.125rem 0",
                    "lineHeight": "1.3",
                }
            )
        )
    
    return html.Div(
        children=stop_items,
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "0.125rem",
            "padding": "0.5rem",
            "backgroundColor": "#2a3a4a",
            "borderRadius": "0.25rem",
            "maxHeight": "12.5rem",
            "overflowY": "auto",
        }
    )


def create_bus_route_markers(direction_routes: List[Dict[str, Any]], bus_stop_map: Dict[str, str], direction_num: int) -> List[dl.DivMarker]:
    """
    Create numbered map markers for bus stops along a route.
    
    Args:
        direction_routes: List of route segments for a direction (sorted by stop sequence)
        bus_stop_map: Dictionary mapping bus stop codes to names
        direction_num: Direction number (1 or 2)
    
    Returns:
        List of DivMarker components for the bus stops
    """
    markers = []
    
    for route in direction_routes:
        try:
            # Get bus stop details
            bus_stop_code = route.get('BusStopCode')
            if not bus_stop_code:
                continue
            
            # Fetch bus stop coordinates from bus stops data
            bus_stops_data = fetch_bus_stops_data()
            if not bus_stops_data or 'value' not in bus_stops_data:
                continue
            
            # Find the matching bus stop
            bus_stop_info = None
            for stop in bus_stops_data['value']:
                if stop.get('BusStopCode') == bus_stop_code:
                    bus_stop_info = stop
                    break
            
            if not bus_stop_info:
                continue
            
            latitude = float(bus_stop_info.get('Latitude', 0))
            longitude = float(bus_stop_info.get('Longitude', 0))
            
            if latitude == 0 or longitude == 0:
                continue
            
            seq = route.get('StopSequence', 0)
            name = bus_stop_map.get(bus_stop_code, 'N/A')
            
            # Set color based on direction (Blue for Direction 1, Yellow for Direction 2)
            if direction_num == 1:
                marker_color = "#4169E1"  # Blue
                shadow_color = "rgba(65,105,225,0.6)"  # Blue shadow
            else:
                marker_color = "#FFD700"  # Yellow
                shadow_color = "rgba(255,215,0,0.6)"  # Yellow shadow
            
            # Create marker HTML with sequence number
            marker_html = (
                f'<div style="width:28px;height:28px;background:{marker_color};'
                f'border-radius:50%;border:3px solid #fff;'
                f'box-shadow:0 2px 8px {shadow_color};'
                f'cursor:pointer;display:flex;align-items:center;'
                f'justify-content:center;font-size:12px;color:#fff;'
                f'font-weight:bold;">'
                f'{seq}'
                f'</div>'
            )
            
            tooltip_text = f"Stop {seq}: {name} ({bus_stop_code})"
            marker_id = f"bus-route-marker-{direction_num}-{seq}-{bus_stop_code}"
            
            markers.append(dl.DivMarker(
                id=marker_id,
                position=[latitude, longitude],
                iconOptions={
                    'className': 'bus-route-marker',
                    'html': marker_html,
                    'iconSize': [28, 28],
                    'iconAnchor': [14, 14],
                },
                children=[dl.Tooltip(tooltip_text)]
            ))
        except (ValueError, TypeError, KeyError):
            continue
    
    return markers


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
    
    # Get bus stops data and create a dictionary mapping for efficient lookup
    bus_stops_data = fetch_bus_stops_data()
    bus_stop_map = {}
    if bus_stops_data and 'value' in bus_stops_data:
        for bs in bus_stops_data['value']:
            bus_stop_code = bs.get('BusStopCode')
            if bus_stop_code:
                bus_stop_map[bus_stop_code] = bs.get('Description', 'N/A')
    
    # Sort routes by direction and stop sequence
    result_items = []
    
    # Fetch bus services data for frequency information
    future = fetch_bus_services_data_async()
    bus_services_data = future.result() if future else None
    
    # Add bus timing table if timing info is available
    if timing_info:
        timing_table = _create_bus_timing_table(timing_info, service_no, bus_services_data)
        if timing_table:
            result_items.append(timing_table)
    
    # Collect direction headers first
    direction_headers = []
    for direction in sorted(directions.keys()):
        direction_routes = sorted(directions[direction], key=lambda x: int(x.get('StopSequence', 0)))
        
        # Get origin and destination using BusStopCode from StopSequence: 1 and last StopSequence
        origin_code = None
        destination_code = None
        
        if direction_routes:
            # Find route with StopSequence: 1 for origin
            for route in direction_routes:
                if route.get('StopSequence') == 1:
                    origin_code = route.get('BusStopCode', 'N/A')
                    break
            
            # Get destination from the last route (highest StopSequence)
            if direction_routes:
                last_route = direction_routes[-1]
                destination_code = last_route.get('BusStopCode', 'N/A')
        
        # Get bus stop names from dictionary mapping
        origin_name = bus_stop_map.get(origin_code, 'N/A') if origin_code else 'N/A'
        destination_name = bus_stop_map.get(destination_code, 'N/A') if destination_code else 'N/A'
        
        direction_label = "Direction 1" if direction == 1 else "Direction 2" if direction == 2 else f"Direction {direction}"
        direction_color = "#4169E1" if direction == 1 else "#FFD700"
        
        # Create direction header with toggle button
        direction_header = html.Div(
            style={
                "backgroundColor": "#3a4a5a",
                "padding": "0.5rem",
                "borderRadius": "0.25rem",
                "flex": "1",
                "minWidth": "0",
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
                                "color": direction_color,
                                "fontWeight": "bold",
                                "fontSize": "0.75rem",
                            }
                        ),
                        html.Span(
                            f"From: {origin_name} ({origin_code})" if origin_code else "From: N/A",
                            style={
                                "color": "#ccc",
                                "fontSize": "0.65rem",
                            }
                        ),
                        html.Span(
                            f"To: {destination_name} ({destination_code})" if destination_code else "To: N/A",
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
                        html.Button(
                            "Show route stops on map",
                            id={"type": "bus-route-toggle", "direction": direction, "service": service_no},
                            n_clicks=0,
                            style={
                                "padding": "0.25rem 0.5rem",
                                "borderRadius": "0.125rem",
                                "border": "0.0625rem solid #999",
                                "backgroundColor": "#2a3a4a",
                                "color": "#fff",
                                "cursor": "pointer",
                                "fontSize": "0.65rem",
                                "fontWeight": "600",
                                "whiteSpace": "nowrap",
                                "marginTop": "0.25rem",
                                "alignSelf": "flex-start",
                            }
                        ),
                    ]
                )
            ]
        )
        
        direction_headers.append(direction_header)
    
    # Display directions side-by-side if there are 2 directions
    if len(direction_headers) == 2:
        directions_container = html.Div(
            style={
                "display": "flex",
                "flexDirection": "row",
                "gap": "0.5rem",
                "marginBottom": "0.5rem",
            },
            children=direction_headers
        )
        result_items.append(directions_container)
    else:
        # If not exactly 2 directions, display them vertically
        result_items.extend(direction_headers)
    
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
        [Input('bus-arrival-page-interval', 'n_intervals'),
         Input('transport-interval', 'n_intervals')]
    )
    def update_bus_services_count(_bus_interval, _transport_interval):
        """
        Update bus services count display using async data fetching.
        Updates from both bus-arrival-page-interval and transport-interval.
        
        Returns:
            HTML Div with bus services count
        """
        # Used for periodic refresh from either interval

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

    # Bus service search callback removed - now handled by unified callback in bus_arrival_callback.py
    # to avoid duplicate output to bus-search-results

    @app.callback(
        Output({"type": "bus-route-toggle", "direction": MATCH, "service": MATCH}, "children"),
        Input({"type": "bus-route-toggle", "direction": MATCH, "service": MATCH}, "n_clicks"),
        prevent_initial_call=True
    )
    def toggle_bus_route_button_text(n_clicks):
        """Toggle button text between show and hide."""
        if not n_clicks or n_clicks % 2 == 0:
            return "Show route stops on map"
        return "Hide route stops on map"

    @app.callback(
        Output("bus-route-markers", "children"),
        [Input({"type": "bus-route-toggle", "direction": ALL, "service": ALL}, "n_clicks"),
         Input("bus-service-search-btn", "n_clicks")],
        [State({"type": "bus-route-toggle", "direction": ALL, "service": ALL}, "id"),
         State("bus-service-search-input", "value")],
        prevent_initial_call=True
    )
    def update_bus_route_markers(_toggle_clicks, _search_clicks, toggle_ids, search_value):
        """Update bus route markers on the map based on toggle states."""
        # If triggered by search button, clear all markers
        if callback_context.triggered:
            trigger_id = callback_context.triggered[0]['prop_id']
            if 'bus-service-search-btn' in trigger_id:
                return []

        # No valid input
        if not search_value or not toggle_ids or not _toggle_clicks:
            return []

        # Determine which directions are expanded
        markers = []
        service_no = search_value.strip().upper()

        # Get routes data
        routes_data = fetch_bus_routes_data()
        if not routes_data or 'value' not in routes_data:
            return []

        routes = routes_data.get('value', [])
        service_routes = [route for route in routes if route.get('ServiceNo', '').upper() == service_no]

        if not service_routes:
            return []

        # Get bus stops data
        bus_stops_data = fetch_bus_stops_data()
        bus_stop_map = {}
        if bus_stops_data and 'value' in bus_stops_data:
            for bus_stop in bus_stops_data['value']:
                bus_stop_code = bus_stop.get('BusStopCode')
                if bus_stop_code:
                    bus_stop_map[bus_stop_code] = bus_stop.get('Description', 'N/A')

        # Group routes by direction
        directions = {}
        for route in service_routes:
            direction = route.get('Direction', 'N/A')
            if direction not in directions:
                directions[direction] = []
            directions[direction].append(route)

        # Check each toggle state (odd n_clicks = shown, even = hidden)
        for toggle_id, n_clicks in zip(toggle_ids, _toggle_clicks):
            if n_clicks and n_clicks % 2 == 1:
                direction = toggle_id.get("direction")
                if direction in directions:
                    direction_routes = sorted(directions[direction], key=lambda x: int(x.get('StopSequence', 0)))
                    direction_markers = create_bus_route_markers(direction_routes, bus_stop_map, direction)
                    markers.extend(direction_markers)

        return markers

