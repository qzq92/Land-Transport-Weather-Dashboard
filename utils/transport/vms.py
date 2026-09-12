"""Variable message sign data helpers."""

import os
from typing import Any, Dict, Optional

from conf.api_urls import VMS_URL
from utils.async_fetcher import fetch_url, run_in_thread
from utils.transport.cache import _road_infra_cache


@run_in_thread
def fetch_vms_data_async() -> Optional[Dict[str, Any]]:
    """Fetch VMS data from LTA DataMall."""
    if _road_infra_cache.get("vms") is not None:
        return _road_infra_cache["vms"]

    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None

    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json",
    }
    data = fetch_url(VMS_URL, headers)
    if data:
        _road_infra_cache["vms"] = data
    return data
