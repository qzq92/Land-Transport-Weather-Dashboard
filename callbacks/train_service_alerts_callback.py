"""
Callback functions for handling train service alerts from LTA DataMall API.
Reference: https://datamall2.mytransport.sg/ltaodataservice/TrainServiceAlerts
"""
import os
import re
from collections import defaultdict
from dash import Input, Output, html
from utils.async_fetcher import fetch_url_2min_cached, _executor
from conf.mrt_line_config import MRT_LINES, LRT_LINES, ALL_TRAIN_LINES, LINE_INFO_MAP


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
    if not data or not isinstance(data, dict):
        return html.P("Unable to fetch train service alerts", style={
            "color": "#999",
            "fontSize": "0.75rem"
        })
    
    # Get the value object if it exists (new format)
    inner_data = data.get("value", data) if isinstance(data.get("value"), dict) else data
    
    # Get status from inner data
    status = inner_data.get("Status", inner_data.get("status", 1))
    
    # Get messages from inner data
    messages = inner_data.get("Message", inner_data.get("message", []))
    
    # If status is 1, check for messages
    if status == 1:
        if messages and len(messages) > 0:
            return html.P("Refer a Road & Transport Metrics and Advisories tab for further advisory/information", style={
                "color": "#4CAF50",
                "fontSize": "0.75rem",
                "fontWeight": "600"
            })
            
        return html.P("All train services are operational", style={
            "color": "#4CAF50",
            "fontSize": "0.75rem",
            "fontWeight": "600"
        })
    
    # If status is not 1, show referral message in red
    return html.P("Refer a Road & Transport Metrics and Advisories tab for further advisory/information", style={
        "color": "#ff4444",
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
    # Use MRT and LRT lines from config
    mrt_lines = MRT_LINES
    lrt_lines = LRT_LINES
    
    # Create a mapping of all lines with their status and details
    line_status_map = {}
    
    # Get the value object if it exists (new format)
    inner_data = data.get("value", data) if isinstance(data, dict) and isinstance(data.get("value"), dict) else (data if isinstance(data, dict) else {})
    
    # 1. Get status from inner data
    status = inner_data.get("Status", inner_data.get("status", 1))
    
    # 2. Check AffectedSegments for status != 1 (disruptions)
    segments = inner_data.get("AffectedSegments", inner_data.get("affected_segments", []))
    for segment in segments:
        if isinstance(segment, dict):
            line = segment.get("Line", segment.get("line", ""))
            if line:
                line_upper = line.upper()
                line_status_map[line_upper] = {
                    "status": status,
                    "direction": segment.get("Direction", segment.get("direction", "")),
                    "stations": segment.get("Stations", segment.get("stations", "")),
                    "has_message": False
                }

    # 3. Check Message list for advisories
    messages = inner_data.get("Message", inner_data.get("message", []))
    for msg_obj in messages:
        if isinstance(msg_obj, dict):
            content = msg_obj.get("Content", msg_obj.get("content", ""))
            if content:
                # Search for line codes in the message content
                for line_info in ALL_TRAIN_LINES:
                    code = line_info["code"]
                    # Match if -CODE- or CODE surrounded by space/start/end
                    upper_content = content.upper()
                    if (f"-{code}-" in upper_content or 
                        f" {code} " in upper_content or 
                        upper_content.endswith(f" {code}") or
                        upper_content.startswith(f"{code} ")):
                        line_upper = code.upper()
                        if line_upper not in line_status_map:
                            line_status_map[line_upper] = {
                                "status": status,
                                "has_message": True
                            }
                        else:
                            line_status_map[line_upper]["has_message"] = True
    
    # Helper function to create line status display
    def create_line_status_display(line_info, line_status_dict):
        line_code = line_info["code"]
        line_name = line_info["name"]
        line_color = line_info["color"]
        
        # Get status for this line
        line_status_info = line_status_dict.get(line_code)
        
        # Determine status display
        if line_status_info:
            status_value = line_status_info.get("status", 1)
            has_message = line_status_info.get("has_message", False)
            
            if status_value == 1:
                if has_message:
                    # Normal service with message (Normal*)
                    detail_text = "Normal*"
                    detail_text_color = "#4CAF50"
                else:
                    # Normal service
                    detail_text = "Normal"
                    detail_text_color = "#4CAF50"
            else:
                # Disrupted/Delays (status != 1) - show referral message
                detail_text = "Refer a Road & Transport Metrics and Advisories tab for further advisory/information"
                detail_text_color = "#ff4444"
        else:
            # No alert data for this line - assume normal
            detail_text = "Normal"
            detail_text_color = "#4CAF50"
        
        return html.Div(
            style={
                "padding": "0.25rem 0.5rem",
                "backgroundColor": "#2c3e50",
                "borderRadius": "0.5rem",
                "display": "flex",
                "alignItems": "center",
                "gap": "0.75rem",
                "minWidth": "fit-content",
                "boxShadow": "0 0.125rem 0.25rem rgba(0, 0, 0, 0.3)",
                "transition": "all 0.2s ease",
            },
            children=[
                # Pill badge with line name and code
                html.Span(
                    f"{line_name} ({line_code})",
                    style={
                        "backgroundColor": line_color,
                        "color": "#ffffff",
                        "fontWeight": "bold",
                        "fontSize": "0.625rem",
                        "padding": "0.25rem 0.625rem",
                        "borderRadius": "1rem",
                        "whiteSpace": "nowrap",
                        "boxShadow": "0 0.0625rem 0.125rem rgba(0, 0, 0, 0.2)",
                    }
                ),
                # Status indicator (colored text)
                html.Span(
                    detail_text,
                    style={
                        "color": detail_text_color,
                        "fontSize": "0.625rem",
                        "fontWeight": "bold",
                        "marginLeft": "auto",
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
    Format train service alerts for display on Road & Transport Metrics and Advisories tab.
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
    
    # Use line info from config
    line_info_map = LINE_INFO_MAP
    
    #print("DATA:", data)
    # Group disrupted alerts or alerts with messages by line code
    # Focus on the Message list as requested
    line_messages_map = defaultdict(list)
    general_messages = []
    
    # Get the value object if it exists (new format)
    inner_data = data.get("value", data) if isinstance(data, dict) and isinstance(data.get("value"), dict) else (data if isinstance(data, dict) else {})
    
    # Get status and messages from inner data
    status = inner_data.get("Status", inner_data.get("status", 1))
    messages = inner_data.get("Message", inner_data.get("message", []))
    
    for msg_obj in messages:
        if isinstance(msg_obj, dict):
            content = msg_obj.get("Content", msg_obj.get("content", ""))
            created_date = msg_obj.get("CreatedDate", msg_obj.get("createdDate", msg_obj.get("created_date", "")))
            
            if content:
                # Extract text after line abbreviation pattern (e.g., "-CCL-")
                processed_content = content
                found_line = False
                upper_content = content.upper()
                
                for line_code in line_info_map.keys():
                    # Line code will be prefix/suffixed with -
                    pattern = f"-{line_code}-"
                    if pattern in upper_content:
                        # Find the position after the pattern
                        pattern_idx = upper_content.find(pattern)
                        if pattern_idx != -1:
                            # Extract text after the pattern (including the pattern itself)
                            # Pattern is like "-CCL-", we want everything after it
                            after_pattern = content[pattern_idx + len(pattern):].strip()
                            processed_content = after_pattern
                        
                        # Prepend CreatedDate if available
                        if created_date:
                            formatted_message = f"{created_date} {processed_content}"
                        else:
                            formatted_message = processed_content
                        
                        line_messages_map[line_code].append(formatted_message)
                        found_line = True
                        break
                
                if not found_line:
                    # For general messages, also prepend CreatedDate if available
                    if created_date:
                        formatted_message = f"{created_date} {content}"
                    else:
                        formatted_message = content
                    general_messages.append(formatted_message)
    
    # Also check AffectedSegments for disruptions if Status != 1
    if status != 1:
        segments = inner_data.get("AffectedSegments", inner_data.get("affected_segments", []))
        for segment in segments:
            if isinstance(segment, dict):
                line = segment.get("Line", segment.get("line", ""))
                if line:
                    line_upper = line.upper()
                    # Add disruption info to messages if not already there
                    disruption_info = f"Status: {status} | Direction: {segment.get('Direction', '')} | Stations: {segment.get('Stations', '')}"
                    if disruption_info not in line_messages_map[line_upper]:
                        line_messages_map[line_upper].insert(0, disruption_info)

    # If no messages and status is 1, show all operational message
    if not line_messages_map and not general_messages and status == 1:
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
    
    # Collect all messages with line information for table display
    table_rows = []
    
    # Helper function to parse datetime and message from formatted content
    def parse_datetime_and_message(content):
        """
        Parse datetime and message from content.
        Expected format: "2026-01-07 05:30:12 Planned train service adjustments..."
        Returns: (datetime_str, message_str)
        """
        # Pattern to match datetime: YYYY-MM-DD HH:MM:SS
        datetime_pattern = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+)$'
        match = re.match(datetime_pattern, content)
        if match:
            datetime_str = match.group(1)
            message_str = match.group(2)
            return datetime_str, message_str
        # If no datetime found, return empty datetime and full content as message
        return "", content
    
    # 1. Process line-specific messages
    for line_code, content_list in line_messages_map.items():
        line_info = line_info_map.get(line_code)
        if not line_info:
            continue
        
        line_name = line_info["name"]
        line_color = line_info["color"]
        
        # Add each message as a table row
        for content in content_list:
            published_time, advisory_message = parse_datetime_and_message(content)
            table_rows.append({
                "line": f"{line_name} ({line_code})",
                "line_color": line_color,
                "published_time": published_time,
                "message": advisory_message
            })
    
    # 2. Process general messages
    for content in general_messages:
        published_time, advisory_message = parse_datetime_and_message(content)
        table_rows.append({
            "line": "General",
            "line_color": "#808080",
            "published_time": published_time,
            "message": advisory_message
        })
    
    # If no messages, show message
    if not table_rows:
        return html.P(
            "No advisories at the moment",
            style={"color": "#999", "fontSize": "0.75rem", "textAlign": "center"}
        )
    
    # Limit to top 5 entries
    table_rows = table_rows[:5]
    
    # Create table structure with 2 columns
    table_header = html.Thead(
        html.Tr([
            html.Th("Line", style={
                "padding": "0.5rem",
                "backgroundColor": "#2c3e50",
                "color": "#fff",
                "fontSize": "0.625rem",
                "fontWeight": "600",
                "textAlign": "left",
                "borderBottom": "0.125rem solid #4a5a6a",
                "width": "20%"
            }),
            html.Th("Alerts/Advisory", style={
                "padding": "0.5rem",
                "backgroundColor": "#2c3e50",
                "color": "#fff",
                "fontSize": "0.625rem",
                "fontWeight": "600",
                "textAlign": "left",
                "borderBottom": "0.125rem solid #4a5a6a",
                "width": "80%"
            })
        ])
    )
    
    # Create table body rows
    table_body_rows = []
    for row_data in table_rows:
        # Combine published time with message in brackets
        message_with_time = row_data["message"]
        if row_data["published_time"]:
            message_with_time = f"[{row_data['published_time']}] {row_data['message']}"
        
        table_body_rows.append(
            html.Tr([
                html.Td(
                    row_data["line"],
                    style={
                        "padding": "0.5rem",
                        "color": row_data["line_color"],
                        "fontSize": "0.75rem",
                        "fontWeight": "600",
                        "verticalAlign": "top",
                        "borderBottom": "0.0625rem solid #4a5a6a",
                    }
                ),
                html.Td(
                    message_with_time,
                    style={
                        "padding": "0.5rem",
                        "color": "#fff",
                        "fontSize": "0.75rem",
                        "verticalAlign": "top",
                        "borderBottom": "0.0625rem solid #4a5a6a",
                        "lineHeight": "1.4",
                    }
                )
            ])
        )
    
    table_body = html.Tbody(table_body_rows)
    
    # Create table
    return html.Table(
        [table_header, table_body],
        style={
            "width": "100%",
            "borderCollapse": "collapse",
            "backgroundColor": "#3a4a5a",
            "borderRadius": "0.25rem",
            "overflow": "hidden"
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
        Update train service alerts display on Road & Transport Metrics and Advisories tab.
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
                # Get the value object if it exists (new format)
                inner_data = data.get("value", data) if isinstance(data.get("value"), dict) else data
                
                # Check status
                status = inner_data.get("Status", inner_data.get("status", 1))
                if status != 1:
                    has_alerts = True
                else:
                    # If status is 1, check if there are any messages
                    messages = inner_data.get("Message", inner_data.get("message", []))
                    if messages and len(messages) > 0:
                        has_alerts = True
            
            # Set background color based on whether there are alerts
            if has_alerts:
                content_style = {
                    "padding": "0.25rem",
                    "color": "#999",
                    "fontSize": "0.5rem",
                    "textAlign": "center",
                    "backgroundColor": "#3a4a5a",
                    "borderRadius": "0.25rem",
                }
            else:
                content_style = {
                    "padding": "0.25rem",
                    "color": "#999",
                    "fontSize": "0.5rem",
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

