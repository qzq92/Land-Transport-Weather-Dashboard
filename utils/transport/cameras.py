"""Traffic camera data helpers."""

from typing import Any, Dict, Optional

from conf.api_urls import TRAFFIC_IMAGES_API_URL
from utils.async_fetcher import fetch_url_2min_cached
from utils.transport.cache import load_lta_camera_id_mapping


def fetch_traffic_cameras() -> Optional[Dict[str, Any]]:
    """Fetch traffic camera metadata from Data.gov.sg."""
    return fetch_url_2min_cached(TRAFFIC_IMAGES_API_URL)


def parse_traffic_camera_data(data: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Parse traffic camera API response to extract camera metadata by camera ID."""
    camera_dict: Dict[str, Dict[str, Any]] = {}

    if not data:
        return camera_dict

    items = data.get("items", [])
    if not items:
        return camera_dict

    cameras = items[0].get("cameras", [])
    for camera in cameras:
        camera_id = str(camera.get("camera_id", ""))
        location = camera.get("location", {})
        if not camera_id:
            continue

        camera_dict[camera_id] = {
            "timestamp": camera.get("timestamp", ""),
            "image_url": camera.get("image", ""),
            "lat": location.get("latitude"),
            "lon": location.get("longitude"),
            "md5": camera.get("image_metadata", {}).get("md5", ""),
        }

    return camera_dict


__all__ = [
    "fetch_traffic_cameras",
    "parse_traffic_camera_data",
    "load_lta_camera_id_mapping",
]
