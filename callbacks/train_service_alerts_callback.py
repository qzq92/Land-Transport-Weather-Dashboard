"""
Callback functions for handling train service alerts from LTA DataMall API.
See TRAIN_SERVICE_ALERTS_URL in conf.api_urls.
"""
import os
import re
import threading
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional
from dash import ALL, Input, Output, State, html, no_update
from utils.async_fetcher import fetch_url_2min_cached, _executor
from conf.mrt_line_config import MRT_LINES, LRT_LINES, ALL_TRAIN_LINES, LINE_INFO_MAP
from utils.transport.gtfs_train_alerts import (
    fetch_gtfs_train_service_alerts,
    fetch_gtfs_train_trip_updates,
    merge_gtfs_with_legacy_status,
)
from conf.api_urls import TRAIN_SERVICE_ALERTS_URL
_RAIL_STATUS_LOCK = threading.Lock()
_LAST_RAIL_STATUS_MAP: Dict[str, Dict[str, object]] = {}
_LAST_RAIL_STATUS_UPDATED: Optional[datetime] = None


def _normalise_status(status_info: Optional[Dict[str, object]], unavailable=False):
    """Return an accessible display label, icon, and affected-state flag."""
    if status_info is None:
        if unavailable:
            return "Status unavailable", "?", False
        return "Normal", "✓", False

    raw_text = str(status_info.get("status_text", "")).rstrip("*").lower()
    status_value = int(status_info.get("status", 1))
    if raw_text.startswith("delay"):
        return "Delay", "!", True
    if raw_text.startswith("alert") or status_value != 1:
        return "Service disruption", "!", True
    return "Normal", "✓", False


def _affected_lines(line_status_map):
    """Return configured lines whose merged status indicates an impact."""
    affected = []
    for line_info in ALL_TRAIN_LINES:
        status_info = line_status_map.get(line_info["code"])
        label, icon, is_affected = _normalise_status(status_info)
        if is_affected:
            affected.append((line_info, status_info, label, icon))
    return affected


def _badge_text_color(background_color):
    """Choose dark or light text using WCAG relative contrast."""
    color = background_color.lstrip("#")
    if len(color) != 6:
        return "#ffffff"
    channels = [int(color[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    white_contrast = 1.05 / (luminance + 0.05)
    return "#ffffff" if white_contrast >= 4.5 else "#111827"


def format_rail_status_summary(line_status_map, availability="current"):
    """Build the compact global summary, including expandable affected chips."""
    affected = _affected_lines(line_status_map)
    if availability == "unavailable":
        return html.Span(
            "? Data unavailable",
            className="rail-status-unavailable",
        )

    if not affected:
        text = (
            "Last known: all lines were operating normally"
            if availability == "stale"
            else "✓ All lines operating normally"
        )
        return html.Span(text, className="rail-status-ok")

    qualifier = "known " if availability == "partial" else ""
    stale_prefix = "Last known: " if availability == "stale" else ""
    summary = html.Span(
        f"! {stale_prefix}{len(affected)} {qualifier}"
        f"{'line' if len(affected) == 1 else 'lines'} affected",
        className="rail-status-warning",
    )
    chips = []
    for line_info, status_info, label, _icon in affected:
        reason = str(status_info.get("reason", "")).strip()
        chips.append(
            html.Details(
                className="rail-affected-chip",
                children=[
                    html.Summary(
                        f"{line_info['code']} — {label}",
                        **{"aria-label": f"{line_info['name']}: {label}"},
                    ),
                    html.Div(
                        className="rail-affected-detail",
                        children=[
                            html.Strong(f"{line_info['name']} — {label}"),
                            html.Span(reason or "See Road & Transport advisories for details."),
                            html.Button(
                                "View advisory",
                                id={
                                    "type": "rail-advisory-link",
                                    "index": line_info["code"],
                                },
                                className="rail-advisory-link",
                                n_clicks=0,
                            ),
                        ],
                    ),
                ],
            )
        )
    return html.Div(
        [summary, *chips],
        className="rail-status-summary",
        role="status",
        **{"aria-live": "polite"},
    )


def format_rail_status_freshness(updated_at, availability="current"):
    """Format source freshness without implying failed data is current."""
    if availability == "unavailable" or updated_at is None:
        return "Data unavailable"
    time_text = updated_at.astimezone().strftime("%H:%M")
    if availability == "stale":
        return f"Last known status · Updated {time_text}"
    if availability == "partial":
        return f"Partial data · Updated {time_text}"
    return f"Updated {time_text}"


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


def _build_legacy_line_status_map(data: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, object]]:
    """Build a line status map using TrainServiceAlerts payload semantics."""
    line_status_map: Dict[str, Dict[str, object]] = {}
    inner_data = (
        data.get("value", data)
        if isinstance(data, dict) and isinstance(data.get("value"), dict)
        else (data if isinstance(data, dict) else {})
    )
    status = inner_data.get("Status", inner_data.get("status", 1))

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
                    "has_message": False,
                }

    messages = inner_data.get("Message", inner_data.get("message", []))
    for msg_obj in messages:
        if isinstance(msg_obj, dict):
            content = msg_obj.get("Content", msg_obj.get("content", ""))
            if content:
                upper_content = content.upper()
                for line_info in ALL_TRAIN_LINES:
                    code = line_info["code"]
                    if (
                        f"-{code}-" in upper_content
                        or f" {code} " in upper_content
                        or upper_content.endswith(f" {code}")
                        or upper_content.startswith(f"{code} ")
                    ):
                        line_upper = code.upper()
                        if line_upper not in line_status_map:
                            line_status_map[line_upper] = {
                                "status": status,
                                "has_message": True,
                                "status_text": (
                                    "Normal" if status == 1 else "Service disruption"
                                ),
                            }
                        else:
                            line_status_map[line_upper]["has_message"] = True
                            if status == 1:
                                line_status_map[line_upper]["status_text"] = "Normal"
                        break
    return line_status_map


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


def format_mrt_line_operational_details(
    data, line_status_map_override=None, availability="current"
):
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
    
    line_status_map = (
        line_status_map_override
        if isinstance(line_status_map_override, dict)
        else _build_legacy_line_status_map(data)
    )
    
    def create_line_status_display(line_info, line_status_dict):
        line_code = line_info["code"]
        line_name = line_info["name"]
        line_color = line_info["color"]
        line_status_info = line_status_dict.get(line_code)
        line_unavailable = availability in ("partial", "unavailable") and line_status_info is None
        detail_text, status_icon, is_affected = _normalise_status(
            line_status_info, unavailable=line_unavailable
        )
        accessible_status = f"{status_icon} {detail_text}"

        return html.Div(
            className="rail-line-card",
            style={
                "borderLeft": (
                    "0.1875rem solid #d99b45"
                    if is_affected
                    else "0.1875rem solid transparent"
                ),
            },
            children=[
                html.Span(
                    f"{line_name} ({line_code})",
                    className="rail-line-badge",
                    style={
                        "backgroundColor": line_color,
                        "color": _badge_text_color(line_color),
                    },
                ),
                html.Span(
                    accessible_status,
                    className="rail-line-state",
                ),
            ],
        )
    
    # Create display for each MRT line
    mrt_elements = []
    for line_info in mrt_lines:
        mrt_elements.append(create_line_status_display(line_info, line_status_map))
    
    # Create display for each LRT line
    lrt_elements = []
    for line_info in lrt_lines:
        lrt_elements.append(create_line_status_display(line_info, line_status_map))
    
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
        className="rail-line-grid",
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
        className="rail-line-grid",
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
        Output('navigation-tabs', 'value'),
        Input({'type': 'rail-advisory-link', 'index': ALL}, 'n_clicks'),
        prevent_initial_call=True,
    )
    def open_rail_advisory(click_counts):
        """Open the Road & Transport view from an affected-line detail."""
        if not click_counts or not any(click_counts):
            return no_update
        return 'transport'

    @app.callback(
        Output('train-service-alerts-status', 'children'),
        Input('interval-component', 'n_intervals'),
        State('navigation-tabs', 'value')
    )
    def update_train_service_alerts(_n_intervals, active_tab):
        """
        Update train service alerts periodically.
        """
        if active_tab != 'main':
            return no_update
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
        [Output('rail-status-summary', 'children'),
         Output('mrt-lines-display', 'children'),
         Output('lrt-lines-display', 'children'),
         Output('rail-status-updated', 'children')],
        Input('interval-component', 'n_intervals')
    )
    def update_mrt_line_operational_details(n_intervals):
        """Update the compact summary and expandable all-lines details."""
        global _LAST_RAIL_STATUS_MAP, _LAST_RAIL_STATUS_UPDATED
        try:
            _ = n_intervals
            legacy_data_future = _executor.submit(fetch_train_service_alerts)
            gtfs_service_alerts_future = _executor.submit(fetch_gtfs_train_service_alerts)
            gtfs_trip_updates_future = _executor.submit(fetch_gtfs_train_trip_updates)

            legacy_data = legacy_data_future.result()
            gtfs_service_alerts_map = gtfs_service_alerts_future.result()
            gtfs_trip_updates_map = gtfs_trip_updates_future.result()

            legacy_line_status_map = _build_legacy_line_status_map(legacy_data)
            merged_line_status_map = merge_gtfs_with_legacy_status(
                legacy_line_status_map=legacy_line_status_map,
                service_alerts_map=gtfs_service_alerts_map,
                trip_updates_map=gtfs_trip_updates_map,
            )

            now = datetime.now().astimezone()
            if isinstance(legacy_data, dict):
                availability = "current"
                with _RAIL_STATUS_LOCK:
                    _LAST_RAIL_STATUS_MAP = {
                        code: dict(status)
                        for code, status in merged_line_status_map.items()
                    }
                    _LAST_RAIL_STATUS_UPDATED = now
                display_map = merged_line_status_map
                updated_at = now
            elif merged_line_status_map:
                availability = "partial"
                display_map = merged_line_status_map
                updated_at = now
            else:
                with _RAIL_STATUS_LOCK:
                    display_map = {
                        code: dict(status)
                        for code, status in _LAST_RAIL_STATUS_MAP.items()
                    }
                    updated_at = _LAST_RAIL_STATUS_UPDATED
                availability = "stale" if updated_at is not None else "unavailable"

            mrt_display, lrt_display = format_mrt_line_operational_details(
                legacy_data,
                line_status_map_override=display_map,
                availability=availability,
            )
            return (
                format_rail_status_summary(display_map, availability),
                mrt_display,
                lrt_display,
                format_rail_status_freshness(updated_at, availability),
            )
        except Exception as error:
            print(f"Error updating MRT/LRT line operational details: {error}")
            with _RAIL_STATUS_LOCK:
                display_map = {
                    code: dict(status)
                    for code, status in _LAST_RAIL_STATUS_MAP.items()
                }
                updated_at = _LAST_RAIL_STATUS_UPDATED
            availability = "stale" if updated_at is not None else "unavailable"
            mrt_display, lrt_display = format_mrt_line_operational_details(
                None,
                line_status_map_override=display_map,
                availability=availability,
            )
            return (
                format_rail_status_summary(display_map, availability),
                mrt_display,
                lrt_display,
                format_rail_status_freshness(updated_at, availability),
            )
    
    @app.callback(
        [Output('train-service-alerts-content', 'children'),
         Output('train-service-alerts-content', 'style')],
        Input('transport-interval', 'n_intervals'),
        State('navigation-tabs', 'value')
    )
    def update_transport_page_train_service_alerts(_n_intervals, active_tab):
        if active_tab != 'transport':
            return no_update, no_update
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
                    "fontSize": "0.8125rem",
                    "textAlign": "left",
                    "backgroundColor": "#3a4a5a",
                    "borderRadius": "0.25rem",
                    "overflowY": "auto",
                    "flex": "1",
                    "minHeight": "0",
                }
            else:
                content_style = {
                    "padding": "0.25rem",
                    "color": "#cbd5e1",
                    "fontSize": "0.8125rem",
                    "textAlign": "left",
                    "overflowY": "auto",
                    "flex": "1",
                    "minHeight": "0",
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

