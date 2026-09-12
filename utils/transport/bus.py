"""Bus stop, route, and service data helpers."""

import math
import os
from concurrent.futures import Future, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from conf.api_urls import BUS_ROUTES_URL, BUS_SERVICES_URL, BUS_STOPS_URL
from utils.async_fetcher import _executor, fetch_url, fetch_url_10min_cached, run_in_thread
from utils.transport.cache import _road_infra_cache


def _lta_headers() -> Optional[Dict[str, str]]:
    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    return {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json",
    }


def _fetch_paginated_lta(endpoint_url: str, max_skip: int) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch a paginated LTA endpoint in parallel batches."""
    headers = _lta_headers()
    if headers is None:
        return {"value": []}

    page_size = 500
    batch_size = 5000
    all_items: List[Dict[str, Any]] = []
    current_skip = 0

    while current_skip < max_skip:
        skip_values = list(range(current_skip, min(current_skip + batch_size, max_skip), page_size))
        futures = {
            _executor.submit(
                fetch_url,
                f"{endpoint_url}?$skip={skip}" if skip > 0 else endpoint_url,
                headers,
            ): skip
            for skip in skip_values
        }

        batch_results: Dict[int, List[Dict[str, Any]]] = {}
        for future in as_completed(futures):
            skip = futures[future]
            try:
                page_data = future.result()
                batch_results[skip] = page_data.get("value", []) if page_data else []
            except Exception as error:
                print(f"Error fetching LTA page (skip={skip}): {error}")
                batch_results[skip] = []

        reached_end = False
        for skip in sorted(skip_values):
            page_items = batch_results.get(skip, [])
            all_items.extend(page_items)
            if len(page_items) < page_size:
                reached_end = True
                break

        if reached_end:
            break
        current_skip += batch_size

    return {"value": all_items}


def fetch_bus_stops_data() -> Optional[Dict[str, Any]]:
    """Fetch all bus stops with a monthly in-memory cache."""
    current_bucket = datetime.now().year * 100 + datetime.now().month
    if (
        _road_infra_cache.get("bus_stops") is not None
        and _road_infra_cache.get("bus_stops_bucket") == current_bucket
    ):
        return _road_infra_cache["bus_stops"]

    result = _fetch_paginated_lta(BUS_STOPS_URL, max_skip=6500)
    _road_infra_cache["bus_stops"] = result
    _road_infra_cache["bus_stops_bucket"] = current_bucket
    return result


def fetch_bus_stops_data_async() -> Future:
    """Fetch all bus stops asynchronously."""
    return _executor.submit(fetch_bus_stops_data)


def fetch_bus_routes_data() -> Optional[Dict[str, Any]]:
    """Fetch all bus routes with a monthly in-memory cache."""
    current_bucket = datetime.now().year * 100 + datetime.now().month
    if (
        _road_infra_cache.get("bus_routes") is not None
        and _road_infra_cache.get("bus_routes_bucket") == current_bucket
    ):
        return _road_infra_cache["bus_routes"]

    result = _fetch_paginated_lta(BUS_ROUTES_URL, max_skip=40000)
    _road_infra_cache["bus_routes"] = result
    _road_infra_cache["bus_routes_bucket"] = current_bucket
    return result


def fetch_bus_routes_data_async() -> Future:
    """Fetch all bus routes asynchronously."""
    return _executor.submit(fetch_bus_routes_data)


@run_in_thread
def fetch_bus_services_data_async() -> Optional[Dict[str, Any]]:
    """Fetch bus services data from LTA DataMall with shared 10-minute cache."""
    headers = _lta_headers()
    if headers is None:
        return None
    return fetch_url_10min_cached(BUS_SERVICES_URL, headers=headers)


def get_bus_services_count() -> int:
    """Return the number of unique bus services from bus routes."""
    routes_data = fetch_bus_routes_data()
    if not routes_data or "value" not in routes_data:
        return 0
    return len({route.get("ServiceNo", "") for route in routes_data.get("value", []) if route.get("ServiceNo")})


def get_bus_stops_count() -> int:
    """Return the total number of bus stops from cached/monthly bus-stop data."""
    stops_data = fetch_bus_stops_data()
    if not stops_data or "value" not in stops_data:
        return 0
    stops = stops_data.get("value", [])
    return len(stops) if isinstance(stops, list) else 0


def calculate_bus_stop_viewport_bounds(
    center: List[float],
    zoom: int,
    map_width_px: int = 800,
    map_height_px: int = 600,
) -> Tuple[float, float, float, float]:
    """Approximate map viewport bounds for filtering bus stops."""
    lat, lon = center
    meters_per_pixel = 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)
    half_width_m = (map_width_px / 2) * meters_per_pixel
    half_height_m = (map_height_px / 2) * meters_per_pixel
    lat_delta = half_height_m / 111320
    lon_delta = half_width_m / (111320 * math.cos(math.radians(lat)))
    return lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta


def filter_bus_stops_by_viewport(
    bus_stops: List[Dict[str, Any]],
    center: List[float],
    zoom: int,
) -> List[Dict[str, Any]]:
    """Filter bus stops to the current viewport."""
    min_lat, max_lat, min_lon, max_lon = calculate_bus_stop_viewport_bounds(center, zoom)
    filtered = []
    for stop in bus_stops:
        try:
            lat = float(stop.get("Latitude"))
            lon = float(stop.get("Longitude"))
        except (TypeError, ValueError):
            continue
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            filtered.append(stop)
    return filtered
