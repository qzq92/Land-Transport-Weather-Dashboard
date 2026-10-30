"""Lookup names for LTA traffic camera IDs."""

import csv
from functools import lru_cache
from pathlib import Path

CAMERA_LOCATIONS_FILE = (
    Path(__file__).resolve().parents[1] / "data" / "lta_camera_id_mapping.csv"
)


@lru_cache(maxsize=1)
def camera_locations() -> dict[str, str]:
    """Load the versioned camera-ID mapping without adding a runtime dependency."""
    try:
        with CAMERA_LOCATIONS_FILE.open(encoding="utf-8", newline="") as file:
            return {
                row["Camera ID"].strip(): row["Location"].strip()
                for row in csv.DictReader(file)
                if row.get("Camera ID") and row.get("Location")
            }
    except OSError:
        return {}
