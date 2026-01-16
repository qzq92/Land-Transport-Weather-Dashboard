"""
Callback functions for handling train service alerts from LTA DataMall API.
Reference: https://datamall2.mytransport.sg/ltaodataservice/TrainServiceAlerts
"""
import os
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
    
    # Create a mapping of affected lines
    affected_lines = {}
    for alert in alerts:
        if isinstance(alert, dict):
            line = alert.get("Line", alert.get("line", ""))
            status = alert.get("Status", alert.get("status", 1))
            if line and status == 2:  # Status 2 means disruption
                affected_lines[line.upper()] = {
                    "direction": alert.get("Direction", alert.get("direction", "")),
                    "stations": alert.get("Stations", alert.get("stations", ""))
                }
    
    # Helper function to create line status display
    def create_line_status_display(line_info, affected_lines_dict):
        line_code = line_info["code"]
        line_name = line_info["name"]
        line_color = line_info["color"]
        
        # Check if this line has disruptions
        is_disrupted = line_code in affected_lines_dict or any(
            line_code in line.upper() for line in affected_lines_dict.keys()
        )
        
        if is_disrupted:
            disruption_info = affected_lines_dict.get(line_code, {})
            direction = disruption_info.get("direction", "")
            stations = disruption_info.get("stations", "")
            
            border_color = "#ff4444"
            
            details = []
            if direction:
                details.append(f"Dir: {direction}")
            if stations:
                details.append(f"Stns: {stations}")
            
            detail_text = " | ".join(details) if details else "Disruption"
            # Red and bold for disruptions
            detail_text_color = "#ff4444"
        else:
            border_color = line_color  # Use line color for border when operational
            detail_text = "Normal"
            # Green and bold for normal service
            detail_text_color = "#4CAF50"
        
        # Check if detail_text indicates Normal Service (case-insensitive)
        is_normal_service = detail_text.lower() == "normal"
        if is_normal_service:
            detail_text_color = "#4CAF50"  # Green and bold
        else:
            detail_text_color = "#ff4444"  # Red and bold
        
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
        mrt_elements.append(create_line_status_display(line_info, affected_lines))
    
    # Create display for each LRT line
    lrt_elements = []
    for line_info in lrt_lines:
        lrt_elements.append(create_line_status_display(line_info, affected_lines))
    
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

