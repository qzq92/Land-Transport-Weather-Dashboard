"""Traffic incidents and faulty traffic light fetch helpers."""

import os
from typing import Any, Dict, Optional

from conf.api_urls import FAULTY_TRAFFIC_LIGHTS_URL, TRAFFIC_INCIDENTS_URL
from utils.async_fetcher import fetch_url_2min_cached, run_in_thread


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


@run_in_thread
def fetch_traffic_incidents_data_async() -> Optional[Dict[str, Any]]:
    """Fetch traffic incidents from LTA DataMall."""
    headers = _lta_headers()
    if headers is None:
        return None
    return fetch_url_2min_cached(TRAFFIC_INCIDENTS_URL, headers)


@run_in_thread
def fetch_faulty_traffic_lights_data_async() -> Optional[Dict[str, Any]]:
    """Fetch faulty traffic lights from LTA DataMall."""
    headers = _lta_headers()
    if headers is None:
        return None
    return fetch_url_2min_cached(FAULTY_TRAFFIC_LIGHTS_URL, headers)
