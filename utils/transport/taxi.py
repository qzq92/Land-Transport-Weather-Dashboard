"""Taxi availability and taxi stand data helpers."""

import os
from typing import Any, Dict, List, Optional

from conf.api_urls import TAXI_API_URL, TAXI_STANDS_URL
from utils.async_fetcher import fetch_url, fetch_url_2min_cached, run_in_thread
from utils.transport.cache import _road_infra_cache


def fetch_taxi_availability() -> Optional[Dict[str, Any]]:
    """Fetch taxi availability from Data.gov.sg."""
    return fetch_url_2min_cached(TAXI_API_URL)


@run_in_thread
def fetch_taxi_stands_data_async() -> Optional[Dict[str, Any]]:
    """Fetch taxi stands data from LTA DataMall."""
    if _road_infra_cache.get("taxi_stands") is not None:
        return _road_infra_cache["taxi_stands"]

    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None

    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json",
    }
    data = fetch_url(TAXI_STANDS_URL, headers)
    if data:
        _road_infra_cache["taxi_stands"] = data
    return data


def fetch_nearby_taxi_stands(
    lat: float,
    lon: float,
    radius_m: float,
    distance_fn,
) -> List[Dict[str, Any]]:
    """Return taxi stands within a radius of the given coordinate."""
    future = fetch_taxi_stands_data_async()
    data = future.result() if future else None
    if not data or "value" not in data:
        return []

    nearby = []
    for stand in data.get("value", []):
        try:
            stand_lat = float(stand.get("Latitude"))
            stand_lon = float(stand.get("Longitude"))
        except (TypeError, ValueError):
            continue
        distance = distance_fn(lat, lon, stand_lat, stand_lon)
        if distance <= radius_m:
            nearby.append({**stand, "distance_m": distance})

    nearby.sort(key=lambda item: item.get("distance_m", float("inf")))
    return nearby
