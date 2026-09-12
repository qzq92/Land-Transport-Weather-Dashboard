"""Data.gov.sg realtime weather API helpers."""

from utils.async_fetcher import _executor, fetch_url_2min_cached, get_default_headers
from conf.api_urls import DATA_GOV_REALTIME_API_BASE, FLOOD_ALERTS_URL, LIGHTNING_URL

SUPPORTED_ENDPOINTS = ["air-temperature", "rainfall", "relative-humidity", "wind-speed"]


def fetch_flood_alerts_async():
    """Fetch flood alerts asynchronously."""
    return _executor.submit(fetch_url_2min_cached, FLOOD_ALERTS_URL, get_default_headers())


def fetch_realtime_data(endpoint):
    """Fetch realtime weather data from data.gov.sg v2 API."""
    if endpoint not in SUPPORTED_ENDPOINTS:
        print(f"Unsupported endpoint: {endpoint}")
        return None

    url = f"{DATA_GOV_REALTIME_API_BASE}/{endpoint}"
    return fetch_url_2min_cached(url, get_default_headers())


def fetch_realtime_data_async(endpoint):
    """Fetch realtime weather data asynchronously."""
    if endpoint not in SUPPORTED_ENDPOINTS:
        print(f"Unsupported endpoint: {endpoint}")
        return None

    url = f"{DATA_GOV_REALTIME_API_BASE}/{endpoint}"
    return _executor.submit(fetch_url_2min_cached, url, get_default_headers())


def fetch_lightning_data_async():
    """Fetch lightning data asynchronously."""
    return _executor.submit(fetch_url_2min_cached, LIGHTNING_URL, get_default_headers())
