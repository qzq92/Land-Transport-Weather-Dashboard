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
    "point": {
        "padding": "0.25rem 0.5rem",
        "color": "#e0e0e0",
        "fontSize": "0.75rem",
        "fontWeight": "500",
        "whiteSpace": "nowrap",
    },
    "time_badge": {
        "padding": "0.125rem 0.375rem",
        "color": "#4ecdc4",
        "fontSize": "0.6875rem",
        "fontWeight": "600",
        "whiteSpace": "nowrap",
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
    }
}


def build_chain_elements(chain):
    """
    Build HTML elements for a single chain of connected segments.

    Args:
        chain: List of connected segment dictionaries

    Returns:
        List of HTML Span elements representing the chain flow
    """
    elements = []
    for idx, segment in enumerate(chain):
        # Add start point (only for first segment)
        if idx == 0:
            elements.append(
                html.Span(segment.get("StartPoint", "N/A"), style=CHAIN_STYLES["point"])
            )

        # Add time badge with arrows
        est_time = segment.get("EstTime", "N/A")
        elements.append(
            html.Span(f" → ({est_time} mins) → ", style=CHAIN_STYLES["time_badge"])
        )

        # Add end point
        elements.append(
            html.Span(segment.get("EndPoint", "N/A"), style=CHAIN_STYLES["point"])
        )

    return elements


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

            # Build chain flow rows
            chain_rows = [
                html.Div(style=CHAIN_STYLES["chain_row"], children=build_chain_elements(chain))
                for chain in chains
            ]

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

    return html.Div(style=CHAIN_STYLES["grid"], children=cards)


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

