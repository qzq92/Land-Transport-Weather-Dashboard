"""
Callback functions for handling estimated travel times from LTA DataMall API.
See EST_TRAVEL_TIMES_URL in conf.api_urls.
"""
import os
from collections import defaultdict
from datetime import datetime

from dash import Input, Output, State, html, no_update

from components.travel_times_board import (
    EXPRESSWAY_FILTER_OPTIONS,
    build_travel_times_board,
    congestion_level,
)
from conf.api_urls import EST_TRAVEL_TIMES_URL
from utils.async_fetcher import _executor, fetch_url_2min_cached

EAST_WEST_EXPRESSWAYS = {"AYE", "PIE", "ECP", "KJE", "SLE", "TPE"}
CONGESTION_RANK = {"clear": 0, "slower": 1, "slow": 2}


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
        if direction_str == "1":
            return "West Direction"
        if direction_str == "2":
            return "East Direction"
    else:
        if direction_str == "1":
            return "North Direction"
        if direction_str == "2":
            return "South Direction"

    return str(direction)


def route_congestion_level(est_times):
    """Return the worst stretch level on a route."""
    worst = "clear"
    for est_time in est_times:
        level = congestion_level(est_time)
        if CONGESTION_RANK[level] > CONGESTION_RANK[worst]:
            worst = level
    return worst


def summarize_expressway_route(expressway_name, direction, items):
    """Build an origin-to-destination summary for one direction."""
    chains = build_segment_chains(items)
    primary = max(chains, key=len) if chains else []
    origin = primary[0].get("StartPoint", "N/A") if primary else "N/A"
    destination = primary[-1].get("EndPoint", "N/A") if primary else "N/A"
    segments = [segment for chain in chains for segment in chain]
    est_times = [segment.get("EstTime", "N/A") for segment in segments]
    total_time = 0.0
    for est_time in est_times:
        try:
            total_time += float(est_time)
        except (ValueError, TypeError):
            pass
    return {
        "expressway": expressway_name,
        "direction": direction,
        "direction_text": map_direction(expressway_name, direction),
        "origin": origin,
        "destination": destination,
        "total_time": total_time,
        "level": route_congestion_level(est_times),
        "chains": chains,
        "segment_count": len(segments),
    }


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

    start_point_map = {}
    for item in items:
        start = item.get("StartPoint", "")
        if start:
            start_point_map[start] = item

    all_start_points = {item.get("StartPoint", "") for item in items}
    all_end_points = {item.get("EndPoint", "") for item in items}
    chain_starts = all_start_points - all_end_points
    if not chain_starts:
        chain_starts = all_start_points

    used_segments = set()
    chains = []

    for start in sorted(chain_starts):
        if start not in start_point_map:
            continue

        segment = start_point_map[start]
        segment_key = (segment.get("StartPoint"), segment.get("EndPoint"))
        if segment_key in used_segments:
            continue

        chain = [segment]
        used_segments.add(segment_key)
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
        "Content-Type": "application/json",
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
        "Content-Type": "application/json",
    }
    return _executor.submit(fetch_url_2min_cached, EST_TRAVEL_TIMES_URL, headers)


def format_travel_times_table(data, selected_expressway="all"):
    """Format travel times as grouped, always-visible direction timelines."""
    if not data or not isinstance(data, dict):
        return html.P(
            "Unable to fetch travel times data",
            style={"color": "#ff6b6b", "fontSize": "0.875rem", "textAlign": "center"},
        )

    travel_times = data.get("value", [])
    if not travel_times:
        return html.P(
            "No travel times data available",
            style={"color": "#94a3b8", "fontSize": "0.875rem", "textAlign": "center"},
        )

    grouped_data = defaultdict(lambda: defaultdict(list))
    for item in travel_times:
        grouped_data[item.get("Name", "Unknown")][item.get("Direction", "Unknown")].append(
            item
        )

    summaries = []
    for expressway_name in grouped_data:
        for direction, items in grouped_data[expressway_name].items():
            summaries.append(
                summarize_expressway_route(expressway_name, direction, items)
            )

    if selected_expressway and selected_expressway != "all":
        summaries = [
            summary
            for summary in summaries
            if summary["expressway"] == selected_expressway
        ]

    if not summaries:
        return html.P(
            "No travel times for this expressway.",
            style={"color": "#94a3b8", "fontSize": "0.875rem", "textAlign": "center"},
        )

    return build_travel_times_board(summaries)


def register_travel_times_callbacks(app):
    """
    Register callbacks for the travel times page.

    Args:
        app: Dash app instance
    """

    @app.callback(
        [
            Output("travel-times-table-container", "children"),
            Output("travel-times-last-updated", "children"),
        ],
        [
            Input("travel-times-interval", "n_intervals"),
            Input("transport-sub-tabs", "value"),
            Input("travel-times-expressway-filter", "value"),
        ],
        State("navigation-tabs", "value"),
    )
    def update_travel_times(_n_intervals, sub_tab, selected_expressway, active_tab):
        if active_tab != "transport" or sub_tab != "transport-travel-times":
            return no_update, no_update
        future = fetch_est_travel_times_async()
        if future is None:
            return (
                html.P(
                    "LTA API key not configured",
                    style={"color": "#ff6b6b", "textAlign": "center"},
                ),
                "API key missing",
            )
        data = future.result()
        table = format_travel_times_table(
            data, selected_expressway=selected_expressway or "all"
        )
        last_updated = f"Updated {datetime.now().strftime('%H:%M')}"
        return table, last_updated
