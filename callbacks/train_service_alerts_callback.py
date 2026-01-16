"""
Callback functions for handling train service alerts from LTA DataMall API.
Reference: https://datamall2.mytransport.sg/ltaodataservice/TrainServiceAlerts
"""
import os
from collections import defaultdict
from dash import Input, Output, html
from utils.async_fetcher import fetch_url_2min_cached, _executor


TRAIN_SERVICE_ALERTS_URL = "https://datamall2.mytransport.sg/ltaodataservice/TrainServiceAlerts"


def fetch_train_service_alerts():
    """
    Fetch train service alerts from LTA DataMall API.
    
    Returns:
        Dictionary containing train service alerts data or None if error
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
    
    return fetch_url_2min_cached(TRAIN_SERVICE_ALERTS_URL, headers)


def fetch_train_service_alerts_async():
    """
    Fetch train service alerts asynchronously (returns Future).
    Call .result() to get the data when needed.
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
    
    return _executor.submit(fetch_url_2min_cached, TRAIN_SERVICE_ALERTS_URL, headers)


def format_train_service_alerts(data):
    """
    Format train service alerts data for display.
    
    Args:
        data: Dictionary containing train service alerts response from LTA API
        
    Returns:
        HTML elements for displaying the alerts
    """
    if not data:
        return html.P("Unable to fetch train service alerts", style={
            "color": "#999",
            "fontSize": "0.75rem"
        })
    
    # Check status attribute - could be at top level or in value array
    status = None
    
    # First check if status is at top level
    if "Status" in data:
        status = data.get("Status")
    elif "status" in data:
        status = data.get("status")
    # Otherwise check in value array
    elif "value" in data:
        alerts = data.get("value", [])
        if alerts and isinstance(alerts, list) and len(alerts) > 0:
            # Check first alert for status
            first_alert = alerts[0]
            if isinstance(first_alert, dict):
                status = first_alert.get("Status", first_alert.get("status"))
    
    # If status is 1, all services are operational
    if status == 1:
        return html.P("All train services are operational", style={
            "color": "#4CAF50",
            "fontSize": "0.75rem",
            "fontWeight": "600"
        })
    
    # If status is 2, extract line, direction, and stations
    if status == 2:
        # Extract from top level or from value array
        line = data.get("Line", data.get("line", ""))
        direction = data.get("Direction", data.get("direction", ""))
        stations = data.get("Stations", data.get("stations", ""))
        
        # If not at top level, check value array
        if not line and "value" in data:
            alerts = data.get("value", [])
            if alerts and isinstance(alerts, list) and len(alerts) > 0:
                first_alert = alerts[0]
                if isinstance(first_alert, dict):
                    line = first_alert.get("Line", first_alert.get("line", ""))
                    direction = first_alert.get("Direction", first_alert.get("direction", ""))
                    stations = first_alert.get("Stations", first_alert.get("stations", ""))
        
        # Format the alert
        alert_text_parts = []
        if line:
            alert_text_parts.append(f"Line: {line}")
        if direction:
            alert_text_parts.append(f"Direction: {direction}")
        if stations:
            alert_text_parts.append(f"Stations: {stations}")
        
        if alert_text_parts:
            alert_text = " | ".join(alert_text_parts)
            return html.Div(
                style={
                    "padding": "0.5rem",
                    "backgroundColor": "#3a4a5a",
                    "borderRadius": "4px",
                    "borderLeft": "3px solid #ff4444"
                },
                children=[
                    html.P(
                        alert_text,
                        style={
                            "color": "#ff6666",
                            "fontSize": "0.75rem",
                            "margin": "0",
                            "fontWeight": "500"
                        }
                    )
                ]
            )
    
    # Default: show operational if status not found or unexpected
    return html.P("All train services are operational", style={
        "color": "#4CAF50",
        "fontSize": "0.75rem",
        "fontWeight": "600"
    })


def format_mrt_line_operational_details(data):
    """
    Format MRT line operational details for display on transport page.
    Shows status for each MRT line.
    
    Args:
        data: Dictionary containing train service alerts response from LTA API
        
    Returns:
        HTML elements displaying operational status for each MRT line
    """
    # Singapore MRT lines with official colors
    mrt_lines = [
        {"code": "NSL", "name": "North South Line", "color": "#E31937"},
        {"code": "EWL", "name": "East West Line", "color": "#009645"},
        {"code": "CCL", "name": "Circle Line", "color": "#FF8C00"},
        {"code": "DTL", "name": "Downtown Line", "color": "#005EC4"},
        {"code": "NEL", "name": "North East Line", "color": "#9900AA"},
        {"code": "TEL", "name": "Thomson-East Coast Line", "color": "#9D5B25"},
    ]
    
    # LRT lines (all share grey color)
    lrt_lines = [
        {"code": "PGL", "name": "Punggol LRT", "color": "#808080"},
        {"code": "SKL", "name": "Sengkang LRT", "color": "#808080"},
        {"code": "BPL", "name": "Bukit Panjang LRT", "color": "#808080"},
    ]
    
    # Extract alerts from API response
    alerts = []
    if data and isinstance(data, dict):
        if "value" in data:
            alerts = data.get("value", [])
        elif isinstance(data, list):
            alerts = data
    
    # Create a mapping of all lines with their status and details
    line_status_map = {}
    for alert in alerts:
        if isinstance(alert, dict):
            line = alert.get("Line", alert.get("line", ""))
            status = alert.get("Status", alert.get("status", 1))
            if line:
                line_upper = line.upper()
                # Store status and details for each line
                # If multiple alerts for same line, keep the one with status != 1 (prioritize disruptions)
                if line_upper not in line_status_map or status != 1:
                    line_status_map[line_upper] = {
                        "status": status,
                        "direction": alert.get("Direction", alert.get("direction", "")),
                        "stations": alert.get("Stations", alert.get("stations", ""))
                    }
    
    # Helper function to create line status display
    def create_line_status_display(line_info, line_status_dict):
        line_code = line_info["code"]
        line_name = line_info["name"]
        line_color = line_info["color"]
        
        # Get status for this line (check exact match first, then partial match)
        line_status_info = None
        if line_code in line_status_dict:
            line_status_info = line_status_dict[line_code]
        else:
            # Check for partial match (e.g., "NSL" in "NSL1", "NSL2")
            for line_key, status_info in line_status_dict.items():
                if line_code in line_key or line_key in line_code:
                    line_status_info = status_info
                    break
        
        # Determine status: Normal only if status == 1, otherwise show referral message
        if line_status_info:
            status_value = line_status_info.get("status", 1)
            if status_value == 1:
                # Normal service
                border_color = line_color
                detail_text = "Normal"
                detail_text_color = "#4CAF50"
            else:
                # Disrupted/Delays (status != 1) - show referral message
                border_color = "#ff4444"
                detail_text = "Refer to Road & Transport tab for more information"
                detail_text_color = "#ff4444"
        else:
            # No alert data for this line - assume normal (status 1)
            border_color = line_color
            detail_text = "Normal"
            detail_text_color = "#4CAF50"
        
        return html.Div(
            style={
                "padding": "0.25rem 0.5rem",
                "backgroundColor": "#2c3e50",
                "borderRadius": "0.25rem",
                "borderLeft": f"3px solid {border_color}",
                "display": "flex",
                "alignItems": "center",
                "gap": "0.5rem",
                "minWidth": "fit-content",
            },
            children=[
                html.Span(
                    f"{line_name} ({line_code})",
                    style={
                        "color": line_color,
                        "fontWeight": "bold",
                        "fontSize": "0.75rem",
                    }
                ),
                html.Span(
                    detail_text,
                    style={
                        "color": detail_text_color,
                        "fontSize": "0.65rem",
                        "fontWeight": "bold",
                    }
                ),
            ]
        )
    
    # Create display for each MRT line
    mrt_elements = []
    for line_info in mrt_lines:
        mrt_elements.append(create_line_status_display(line_info, line_status_map))
    
    # Create display for each LRT line
    lrt_elements = []
    for line_info in lrt_lines:
        lrt_elements.append(create_line_status_display(line_info, line_status_map))
    
    # Return MRT and LRT displays separately
    mrt_display = html.Div(
        children=mrt_elements if mrt_elements else [
            html.P(
                "Unable to load MRT line status",
                style={
                    "color": "#999",
                    "fontSize": "0.75rem",
                    "margin": "0",
                }
            )
        ],
        style={
            "display": "flex",
            "flexDirection": "row",
            "flexWrap": "wrap",
            "gap": "0.5rem",
            "justifyContent": "flex-start",
            "width": "100%",
        }
    )
    
    lrt_display = html.Div(
        children=lrt_elements if lrt_elements else [
            html.P(
                "Unable to load LRT line status",
                style={
                    "color": "#999",
                    "fontSize": "0.75rem",
                    "margin": "0",
                }
            )
        ],
        style={
            "display": "flex",
            "flexDirection": "row",
            "flexWrap": "wrap",
            "gap": "0.5rem",
            "justifyContent": "flex-start",
            "width": "100%",
        }
    )
    
    return mrt_display, lrt_display


def format_transport_page_train_service_alerts(data):
    """
    Format train service alerts for display on Road & Transport tab.
    Shows only lines with status != 1, displaying line name with abbreviation,
    direction, and message.
    
    Args:
        data: Dictionary containing train service alerts response from LTA API
        
    Returns:
        HTML elements displaying disrupted lines with details
    """
    if not data:
        return html.P(
            "Unable to fetch train service alerts",
            style={
                "color": "#999",
                "fontSize": "0.75rem",
                "textAlign": "center",
            }
        )
    
    # Singapore MRT lines with official colors and names
    mrt_lines = [
        {"code": "NSL", "name": "North South Line", "color": "#E31937"},
        {"code": "EWL", "name": "East West Line", "color": "#009645"},
        {"code": "CCL", "name": "Circle Line", "color": "#FF8C00"},
        {"code": "DTL", "name": "Downtown Line", "color": "#005EC4"},
        {"code": "NEL", "name": "North East Line", "color": "#9900AA"},
        {"code": "TEL", "name": "Thomson-East Coast Line", "color": "#9D5B25"},
    ]
    
    # LRT lines
    lrt_lines = [
        {"code": "PGL", "name": "Punggol LRT", "color": "#808080"},
        {"code": "SKL", "name": "Sengkang LRT", "color": "#808080"},
        {"code": "BPL", "name": "Bukit Panjang LRT", "color": "#808080"},
    ]
    
    all_lines = mrt_lines + lrt_lines
    
    # Extract alerts from API response
    alerts = []
    if data and isinstance(data, dict):
        if "value" in data:
            alerts = data.get("value", [])
        elif isinstance(data, list):
            alerts = data
    
    # Create a mapping of line codes to line info
    line_info_map = {line["code"]: line for line in all_lines}
    
    # Group disrupted alerts by line code (status != 1)
    disrupted_lines_by_code = defaultdict(list)
    for alert in alerts:
        if isinstance(alert, dict):
            line = alert.get("Line", alert.get("line", ""))
            status = alert.get("Status", alert.get("status", 1))
            if line and status != 1:
                line_upper = line.upper()
                # Find matching line info
                line_info = None
                for line_code, info in line_info_map.items():
                    if line_code in line_upper or line_upper in line_code:
                        line_info = info
                        break
                
                if line_info:
                    direction = alert.get("Direction", alert.get("direction", ""))
                    message = alert.get("Message", alert.get("message", ""))
                    
                    disrupted_lines_by_code[line_info["code"]].append({
                        "line_name": line_info["name"],
                        "line_color": line_info["color"],
                        "direction": direction,
                        "message": message,
                    })
    
    # If no disrupted lines, show all operational message
    if not disrupted_lines_by_code:
        return html.P(
            "All train services are operational",
            style={
                "color": "#4CAF50",
                "fontSize": "0.75rem",
                "fontWeight": "600",
                "textAlign": "center",
                "margin": "0",
            }
        )
    
    # Create parent containers for each line with child rows for each alert
    line_containers = []
    for line_code, alerts_list in disrupted_lines_by_code.items():
        # Get line info from first alert (all alerts for same line have same info)
        line_name = alerts_list[0]["line_name"]
        line_color = alerts_list[0]["line_color"]
        
        # Create child rows for each alert in this line
        alert_rows = []
        for alert_data in alerts_list:
            direction = alert_data["direction"]
            message = alert_data["message"]
            
            # Create direction header text
            direction_text = ""
            if direction:
                direction_text = f"towards {direction}"
            
            # Create nested message container
            message_content = message if message else "Service disruption - please check for updates"
            
            # Create alert row children
            alert_row_children = []
            
            # Add direction header if available
            if direction_text:
                alert_row_children.append(
                    html.Div(
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "gap": "0.5rem",
                        },
                        children=[
                            html.Span(
                                direction_text,
                                style={
                                    "color": "#fff",
                                    "fontWeight": "600",
                                    "fontSize": "0.75rem",
                                }
                            ),
                        ]
                    )
                )
            
            # Always add message container
            alert_row_children.append(
                html.Div(
                    style={
                        "padding": "0.5rem",
                        "backgroundColor": "#2c3e50",
                        "borderRadius": "0.25rem",
                        "borderLeft": "2px solid #ff4444",
                    },
                    children=[
                        html.P(
                            message_content,
                            style={
                                "color": "#ff6666",
                                "fontSize": "0.75rem",
                                "margin": "0",
                                "lineHeight": "1.4",
                            }
                        )
                    ]
                )
            )
            
            # Create alert row
            alert_row = html.Div(
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "0.5rem",
                },
                children=alert_row_children
            )
            alert_rows.append(alert_row)
        
        # Create parent container for this line
        line_container = html.Div(
            style={
                "padding": "0.75rem",
                "backgroundColor": "#3a4a5a",
                "borderRadius": "0.5rem",
                "borderLeft": f"4px solid {line_color}",
                "marginBottom": "0.75rem",
                "display": "flex",
                "flexDirection": "column",
                "gap": "0.75rem",
            },
            children=[
                # Line header
                html.Div(
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "0.5rem",
                    },
                    children=[
                        html.Span(
                            f"{line_name} ({line_code})",
                            style={
                                "color": line_color,
                                "fontWeight": "bold",
                                "fontSize": "0.8125rem",
                            }
                        ),
                    ]
                ),
                # Alerts container with all alert rows
                html.Div(
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "0.5rem",
                    },
                    children=alert_rows
                ),
            ]
        )
        line_containers.append(line_container)
    
    return html.Div(
        children=line_containers,
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "0.5rem",
        }
    )


def register_train_service_alerts_callbacks(app):
    """
    Register callbacks for train service alerts and station crowd alerts.
    
    Args:
        app: Dash app instance
    """
    @app.callback(
        Output('train-service-alerts-status', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_train_service_alerts(_n_intervals):
        """
        Update train service alerts periodically.
        """
        alerts_display = html.P("Error loading train service alerts", style={
            "color": "#ff4444", "fontSize": "0.75rem"
        })
        try:
            data = fetch_train_service_alerts()
            alerts_display = format_train_service_alerts(data)
        except Exception as error:
            print(f"Error updating train service alerts: {error}")

        return alerts_display
    
    @app.callback(
        [Output('mrt-lines-display', 'children'),
         Output('lrt-lines-display', 'children')],
        Input('interval-component', 'n_intervals')
    )
    def update_mrt_line_operational_details(n_intervals):
        """
        Update MRT and LRT line operational details in banner periodically.
        
        Args:
            n_intervals: Number of intervals (from dcc.Interval component)
            
        Returns:
            Tuple of (MRT lines display, LRT lines display)
        """
        try:
            # Fetch train service alerts
            data = fetch_train_service_alerts()
            
            # Format and return the line details (separate MRT and LRT)
            return format_mrt_line_operational_details(data)
        except Exception as error:
            print(f"Error updating MRT/LRT line operational details: {error}")
            error_display = html.P(
                "Error loading line status",
                style={
                    "color": "#ff4444",
                    "fontSize": "0.75rem",
                    "margin": "0",
                }
            )
            return error_display, error_display
    
    @app.callback(
        [Output('train-service-alerts-content', 'children'),
         Output('train-service-alerts-content', 'style')],
        Input('transport-interval', 'n_intervals')
    )
    def update_transport_page_train_service_alerts(_n_intervals):
        """
        Update train service alerts display on Road & Transport tab.
        Shows disrupted lines with details.
        
        Args:
            n_intervals: Number of intervals (from dcc.Interval component)
            
        Returns:
            HTML elements displaying disrupted lines
        """
        try:
            # Fetch train service alerts
            data = fetch_train_service_alerts()
            
            # Format and return the alerts for transport page
            content = format_transport_page_train_service_alerts(data)
            
            # Check if there are disrupted lines to determine background color
            has_alerts = False
            if data and isinstance(data, dict):
                alerts = []
                if "value" in data:
                    alerts = data.get("value", [])
                elif isinstance(data, list):
                    alerts = data
                
                # Check if any alert has status != 1
                for alert in alerts:
                    if isinstance(alert, dict):
                        status = alert.get("Status", alert.get("status", 1))
                        if status != 1:
                            has_alerts = True
                            break
            
            # Set background color based on whether there are alerts
            if has_alerts:
                content_style = {
                    "padding": "0.5rem",
                    "color": "#999",
                    "fontSize": "0.75rem",
                    "textAlign": "center",
                    "backgroundColor": "#3a4a5a",
                    "borderRadius": "0.25rem",
                }
            else:
                content_style = {
                    "padding": "0.5rem",
                    "color": "#999",
                    "fontSize": "0.75rem",
                    "textAlign": "center",
                }
            
            return content, content_style
        except Exception as error:
            print(f"Error updating transport page train service alerts: {error}")
            error_content = html.P(
                "Error loading train service alerts",
                style={
                    "color": "#ff4444",
                    "fontSize": "0.75rem",
                    "textAlign": "center",
                    "margin": "0",
                }
            )
            error_style = {
                "padding": "0.5rem",
                "color": "#999",
                "fontSize": "0.75rem",
                "textAlign": "center",
            }
            return error_content, error_style

