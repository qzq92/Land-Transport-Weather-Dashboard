"""
Callback functions for handling estimated travel times from LTA DataMall API.
Reference: https://datamall2.mytransport.sg/ltaodataservice/EstTravelTimes
"""
import os
from collections import defaultdict
from datetime import datetime
from dash import Input, Output, html
from utils.async_fetcher import fetch_url_2min_cached, _executor


EST_TRAVEL_TIMES_URL = "https://datamall2.mytransport.sg/ltaodataservice/EstTravelTimes"

# Expressways that use East/West direction mapping
EAST_WEST_EXPRESSWAYS = {"AYE", "PIE", "ECP", "KJE", "SLE", "TPE"}


def map_direction(expressway_name, direction):
    """
    Map direction number to text based on expressway name.

    Args:
        expressway_name: Name of the expressway (e.g., "AYE", "BKE")
        direction: Direction number (1 or 2)

    Returns:
        Direction text ("West"/"East" or "North"/"South")
    """
    direction_str = str(direction).strip()

    if expressway_name in EAST_WEST_EXPRESSWAYS:
        # For AYE, PIE, ECP, KJE, SLE, TPE: 1 = West, 2 = East
        if direction_str == "1":
            return "West"
        if direction_str == "2":
            return "East"
    else:
        # For other expressways: 1 = North, 2 = South
        if direction_str == "1":
            return "North"
        if direction_str == "2":
            return "South"

    # Fallback: return original direction if not 1 or 2
    return str(direction)


# Duration color thresholds
DURATION_COLORS = {
    "good": "#2ecc71",      # Green - less than 5 mins (good flow)
    "moderate": "#f39c12",  # Orange - 5 to 10 mins (moderate congestion)
    "heavy": "#e74c3c",     # Red - more than 10 mins (heavy congestion)
}


def get_duration_color(est_time):
    """
    Get color based on estimated travel time duration.

    Args:
        est_time: Estimated time in minutes (can be string or number)

    Returns:
        Color hex code based on duration thresholds
    """
    try:
        duration = float(est_time)
    except (ValueError, TypeError):
        return DURATION_COLORS["moderate"]  # Default to orange if invalid

    if duration < 5:
        return DURATION_COLORS["good"]
    if duration <= 10:
        return DURATION_COLORS["moderate"]
    return DURATION_COLORS["heavy"]


def build_segment_chains(items):
    """
    Build connected chains of segments by matching EndPoint to StartPoint.

    Args:
        items: List of segment dictionaries with StartPoint, EndPoint, EstTime

    Returns:
        List of chains, where each chain is a list of connected segments
    """
    if not items:
        return []

    # Create a lookup from StartPoint to segment
    start_point_map = {}
    for item in items:
        start = item.get("StartPoint", "")
        if start:
            start_point_map[start] = item

    # Find all start points and end points
    all_start_points = {item.get("StartPoint", "") for item in items}
    all_end_points = {item.get("EndPoint", "") for item in items}

    # Find chain starting points (start points that are not end points of any segment)
    chain_starts = all_start_points - all_end_points

    # If no clear starting points, use all start points
    if not chain_starts:
        chain_starts = all_start_points

    # Track which segments have been used
    used_segments = set()
    chains = []

    # Build chains starting from each chain start point
    for start in sorted(chain_starts):
        if start not in start_point_map:
            continue

        segment = start_point_map[start]
        segment_key = (segment.get("StartPoint"), segment.get("EndPoint"))

        if segment_key in used_segments:
            continue

        # Start a new chain
        chain = [segment]
        used_segments.add(segment_key)

        # Follow the chain
        current_end = segment.get("EndPoint", "")
        while current_end in start_point_map:
            next_segment = start_point_map[current_end]
            next_key = (next_segment.get("StartPoint"), next_segment.get("EndPoint"))

            if next_key in used_segments:
                break

            chain.append(next_segment)
            used_segments.add(next_key)
            current_end = next_segment.get("EndPoint", "")

        chains.append(chain)

    # Handle any remaining unused segments (disconnected segments)
    for item in items:
        segment_key = (item.get("StartPoint"), item.get("EndPoint"))
        if segment_key not in used_segments:
            chains.append([item])
            used_segments.add(segment_key)

    return chains


def fetch_est_travel_times():
    """
    Fetch estimated travel times from LTA DataMall API.

    Returns:
        Dictionary containing travel times data or None if error
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

    return fetch_url_2min_cached(EST_TRAVEL_TIMES_URL, headers)


def fetch_est_travel_times_async():
    """
    Fetch estimated travel times asynchronously (returns Future).
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

    return _executor.submit(fetch_url_2min_cached, EST_TRAVEL_TIMES_URL, headers)


# Styles for chain flow visualization (defined at module level to reduce local variables)
CHAIN_STYLES = {
    "header": {
        "padding": "0.4375rem 1rem",
        "backgroundColor": "#1a2a3a",
        "color": "#fff",
        "fontWeight": "700",
        "fontSize": "0.9375rem",
        "borderBottom": "0.125rem solid #4a5a6a",
        "borderRadius": "0.375rem 0.375rem 0 0",
    },
    "point_base": {
        "padding": "0.25rem 0.625rem",
        "fontSize": "0.75rem",
        "fontWeight": "500",
        "whiteSpace": "nowrap",
        "borderRadius": "0.375rem",
        "backgroundColor": "#3a4a5a",
        "color": "#e0e0e0",
    },
    "point_first": {
        "padding": "0.25rem 0.625rem",
        "fontSize": "0.8125rem",
        "fontWeight": "600",
        "whiteSpace": "nowrap",
        "borderRadius": "0.375rem",
        "backgroundColor": "#3a4a5a",
        "color": "#fff",
        "borderLeft": "0.1875rem solid #4ecdc4",
    },
    "point_last": {
        "padding": "0.25rem 0.625rem",
        "fontSize": "0.8125rem",
        "fontWeight": "600",
        "whiteSpace": "nowrap",
        "borderRadius": "0.375rem",
        "backgroundColor": "#3a4a5a",
        "color": "#fff",
        "borderRight": "0.1875rem solid #4ecdc4",
    },
    "point_intermediate": {
        "padding": "0.25rem 0.5rem",
        "fontSize": "0.75rem",
        "fontWeight": "500",
        "whiteSpace": "nowrap",
        "borderRadius": "0.375rem",
        "backgroundColor": "#3a4a5a",
        "color": "#ccc",
    },
    "location_marker": {
        "fontSize": "0.625rem",
        "marginRight": "0.25rem",
    },
    "time_badge_base": {
        "padding": "0.125rem 0.5rem",
        "fontSize": "0.6875rem",
        "fontWeight": "600",
        "whiteSpace": "nowrap",
        "borderRadius": "0.75rem",
        "margin": "0 0.25rem",
        "color": "#fff",
    },
    "arrow": {
        "color": "#888",
        "fontSize": "0.75rem",
        "margin": "0 0.125rem",
    },
    "chain_row": {
        "display": "flex",
        "flexWrap": "wrap",
        "alignItems": "center",
        "padding": "0.375rem 0.75rem",
        "borderBottom": "0.0625rem solid #3a4a5a",
    },
    "card": {
        "backgroundColor": "#2a3a4a",
        "borderRadius": "0.5rem",
        "overflow": "hidden",
        "display": "flex",
        "flexDirection": "column"
    },
    "card_content": {
        "display": "flex",
        "flexDirection": "column",
        "width": "100%"
    },
    "grid": {
        "display": "grid",
        "gridTemplateColumns": "1fr",
        "gap": "1rem",
    },
    "total_time": {
        "marginLeft": "auto",
        "padding": "0.125rem 0.5rem",
        "backgroundColor": "#1a2a3a",
        "borderRadius": "0.5rem",
        "color": "#aaa",
        "fontSize": "0.6875rem",
        "fontWeight": "500",
    }
}


def build_color_legend():
    """Build the color legend component for travel time durations."""
    legend_item_style = {"display": "flex", "alignItems": "center", "gap": "0.375rem"}
    badge_style = {"width": "0.75rem", "height": "0.75rem", "borderRadius": "50%"}
    text_style = {"fontSize": "0.75rem", "color": "#ccc"}

    return html.Div(
        style={
            "display": "flex",
            "alignItems": "center",
            "padding": "0.5rem 1rem",
            "backgroundColor": "#1a2a3a",
            "borderRadius": "0.5rem",
            "marginBottom": "1rem",
            "flexWrap": "wrap",
            "gap": "0.5rem",
        },
        children=[
            html.Span("Travel Time:", style={
                "fontSize": "0.75rem", "color": "#fff", "fontWeight": "600", "marginRight": "0.5rem"
            }),
            html.Div(style={**legend_item_style, "marginRight": "1rem"}, children=[
                html.Div(style={**badge_style, "backgroundColor": DURATION_COLORS["good"]}),
                html.Span("< 5 mins (Good)", style=text_style),
            ]),
            html.Div(style={**legend_item_style, "marginRight": "1rem"}, children=[
                html.Div(style={**badge_style, "backgroundColor": DURATION_COLORS["moderate"]}),
                html.Span("5-10 mins (Moderate)", style=text_style),
            ]),
            html.Div(style={**legend_item_style, "marginRight": "1rem"}, children=[
                html.Div(style={**badge_style, "backgroundColor": DURATION_COLORS["heavy"]}),
                html.Span("> 10 mins (Heavy)", style=text_style),
            ]),
        ]
    )


def build_chain_elements(chain):
    """
    Build HTML elements for a single chain of connected segments.

    Args:
        chain: List of connected segment dictionaries

    Returns:
        Tuple of (list of HTML elements, total time in minutes)
    """
    elements = []
    total_time = 0
    chain_length = len(chain)

    for idx, segment in enumerate(chain):
        is_first_segment = (idx == 0)
        is_last_segment = (idx == chain_length - 1)

        # Add start point (only for first segment)
        if is_first_segment:
            start_point = segment.get("StartPoint", "N/A")
            # Add start marker and styled first point
            elements.append(
                html.Span([
                    html.Span("● ", style={**CHAIN_STYLES["location_marker"], "color": "#4ecdc4"}),
                    start_point
                ], style=CHAIN_STYLES["point_first"])
            )

        # Get estimated time and color
        est_time = segment.get("EstTime", "N/A")
        duration_color = get_duration_color(est_time)

        # Track total time
        try:
            total_time += float(est_time)
        except (ValueError, TypeError):
            pass

        # Add arrow
        elements.append(html.Span(" → ", style=CHAIN_STYLES["arrow"]))

        # Add time badge with dynamic background color
        badge_style = {**CHAIN_STYLES["time_badge_base"], "backgroundColor": duration_color}
        elements.append(html.Span(f"{est_time} mins", style=badge_style))

        # Add arrow
        elements.append(html.Span(" → ", style=CHAIN_STYLES["arrow"]))

        # Add end point with appropriate styling
        end_point = segment.get("EndPoint", "N/A")
        if is_last_segment:
            # Last point with destination marker
            elements.append(
                html.Span([
                    end_point,
                    html.Span(" ◉", style={**CHAIN_STYLES["location_marker"], "color": "#4ecdc4"})
                ], style=CHAIN_STYLES["point_last"])
            )
        else:
            # Intermediate point
            elements.append(
                html.Span(end_point, style=CHAIN_STYLES["point_intermediate"])
            )

    return elements, total_time


def format_travel_times_table(data):
    """
    Format travel times data into chain flow visualization grouped by expressway and direction.

    Args:
        data: Dictionary containing travel times response from LTA API

    Returns:
        HTML elements for displaying travel times as connected chain flows
    """
    if not data or not isinstance(data, dict):
        return html.P(
            "Unable to fetch travel times data",
            style={"color": "#ff6b6b", "fontSize": "0.875rem", "textAlign": "center"}
        )

    travel_times = data.get("value", [])
    if not travel_times:
        return html.P(
            "No travel times data available",
            style={"color": "#999", "fontSize": "0.875rem", "textAlign": "center"}
        )

    # Group by expressway name and direction
    grouped_data = defaultdict(lambda: defaultdict(list))
    for item in travel_times:
        grouped_data[item.get("Name", "Unknown")][item.get("Direction", "Unknown")].append(item)

    # Build cards for each expressway-direction combination
    cards = []
    for expressway_name in sorted(grouped_data.keys()):
        for direction in sorted(grouped_data[expressway_name].keys()):
            chains = build_segment_chains(grouped_data[expressway_name][direction])

            # Build chain flow rows with total time
            chain_rows = []
            for chain in chains:
                elements, total_time = build_chain_elements(chain)
                elements.append(
                    html.Span(f"Total: {total_time:.0f} mins", style=CHAIN_STYLES["total_time"])
                )
                chain_rows.append(
                    html.Div(style=CHAIN_STYLES["chain_row"], children=elements)
                )

            # Create card header
            direction_text = map_direction(expressway_name, direction)
            header = f"{expressway_name} (Towards {direction_text})"

            cards.append(
                html.Div(
                    style=CHAIN_STYLES["card"],
                    children=[
                        html.Div(header, style=CHAIN_STYLES["header"]),
                        html.Div(style=CHAIN_STYLES["card_content"], children=chain_rows)
                    ]
                )
            )

    return html.Div(
        style={"display": "flex", "flexDirection": "column"},
        children=[build_color_legend(), html.Div(style=CHAIN_STYLES["grid"], children=cards)]
    )


def register_travel_times_callbacks(app):
    """
    Register callbacks for the travel times page.

    Args:
        app: Dash app instance
    """
    @app.callback(
        [Output("travel-times-table-container", "children"),
         Output("travel-times-last-updated", "children")],
        Input("travel-times-interval", "n_intervals")
    )
    def update_travel_times(_n_intervals):
        """
        Update the travel times table.

        Args:
            _n_intervals: Number of interval triggers (used as callback trigger)

        Returns:
            Tuple of (table content, last updated timestamp)
        """
        # Fetch data asynchronously
        future = fetch_est_travel_times_async()

        if future is None:
            return (
                html.P(
                    "LTA API key not configured",
                    style={"color": "#ff6b6b", "textAlign": "center"}
                ),
                "API key missing"
            )

        data = future.result()
        table = format_travel_times_table(data)

        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        last_updated = f"Last updated: {timestamp}"

        return table, last_updated

