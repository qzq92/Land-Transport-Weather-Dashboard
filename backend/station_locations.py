"""Lookup names for MRT/LRT station codes."""

import csv
from functools import lru_cache
from pathlib import Path

STATIONS_FILE = Path(__file__).resolve().parents[1] / "data" / "MRTLRTStations.csv"

# Circle Line Extension codes share stations with Circle Line.
STATION_CODE_ALIASES = {
    "CE1": "CC34",
    "CE2": "CC33",
}


@lru_cache(maxsize=1)
def station_names() -> dict[str, str]:
    """Load STN_NO -> STN_NAME, including interchange and CE aliases."""
    names: dict[str, str] = {}
    try:
        with STATIONS_FILE.open(encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                name = (row.get("STN_NAME") or "").strip()
                codes = (row.get("STN_NO") or "").strip()
                if not name or not codes:
                    continue
                for code in codes.split("/"):
                    normalized = code.strip().upper()
                    if normalized:
                        names[normalized] = name
    except OSError:
        return {}

    for alias, canonical in STATION_CODE_ALIASES.items():
        if canonical in names:
            names[alias] = names[canonical]
    return names


def station_name_for(code: str) -> str:
    """Return the official station name for a code, if known."""
    return station_names().get(code.strip().upper(), "")
