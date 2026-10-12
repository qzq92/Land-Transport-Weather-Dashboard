"""Shared in-memory caches for transport data."""

from pathlib import Path
from typing import Dict

import pandas as pd

_road_infra_cache = {
    "taxi_stands": None,
    "bus_stops": None,
    "bus_stops_bucket": None,
    "bus_routes": None,
    "bus_routes_bucket": None,
}

_LTA_CAMERA_ID_MAPPING: Dict[str, str] = {}
_LTA_CAMERA_ID_MAPPING_LOADED = False


def clear_road_infra_cache() -> None:
    """Clear cached road infrastructure data."""
    for key in list(_road_infra_cache.keys()):
        _road_infra_cache[key] = None


def load_lta_camera_id_mapping() -> Dict[str, str]:
    """Load LTA camera ID to road/location description mapping from CSV."""
    global _LTA_CAMERA_ID_MAPPING_LOADED

    if _LTA_CAMERA_ID_MAPPING_LOADED:
        return _LTA_CAMERA_ID_MAPPING

    project_root = Path(__file__).resolve().parents[2]
    csv_path = project_root / "data" / "lta_camera_id_mapping.csv"

    if not csv_path.exists():
        _LTA_CAMERA_ID_MAPPING_LOADED = True
        return _LTA_CAMERA_ID_MAPPING

    try:
        df = pd.read_csv(csv_path, dtype={"Camera ID": str})
        for _, row in df.iterrows():
            camera_id = str(row.get("Camera ID", "")).strip()
            description = str(row.get("Location", "")).strip()
            if camera_id and description and camera_id.lower() != "nan":
                _LTA_CAMERA_ID_MAPPING[camera_id] = description
    except Exception as error:
        print(f"Error loading LTA camera ID mapping: {error}")

    _LTA_CAMERA_ID_MAPPING_LOADED = True
    return _LTA_CAMERA_ID_MAPPING
