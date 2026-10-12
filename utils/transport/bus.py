"""Bus stop, route, and service data helpers."""

import os
from concurrent.futures import Future, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional

from conf.api_urls import BUS_ROUTES_URL, BUS_SERVICES_URL, BUS_STOPS_URL
from utils.async_fetcher import (
    _executor,
    fetch_url,
    fetch_url_10min_cached,
    run_in_thread,
)
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
