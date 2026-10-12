"""Normalize and locate LTA faulty traffic-light alerts."""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus

import requests

from conf.api_urls import ONEMAP_SEARCH_URL


LTA_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
)

ALARM_TYPE_LABELS = {
    "4": "Blackout",
    "13": "Flashing yellow",
}

_LOCATION_PATTERN = re.compile(
    r"\bat\s+(.+?)(?:\s+junc(?:tion)?\.?|$)",
    flags=re.IGNORECASE,
)
_LOCATION_SUFFIX_PATTERN = re.compile(
    r"\s+(?:from|towards|before|after)\s+.+$",
    flags=re.IGNORECASE,
)


def extract_payload_items(payload: Any) -> List[Dict[str, Any]]:
    """Return dictionary records from a common API envelope or a list."""
    values: Any = payload
    if isinstance(payload, dict):
        for key in ("value", "data", "items"):
            if isinstance(payload.get(key), list):
                values = payload[key]
                break
        else:
            values = []
    if not isinstance(values, list):
        return []
    return [item for item in values if isinstance(item, dict)]


def parse_lta_datetime(value: Any) -> Optional[datetime]:
    """Parse the timestamp formats documented by LTA DataMall."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.rstrip("Z")
    for date_format in LTA_DATETIME_FORMATS:
        try:
            return datetime.strptime(normalized, date_format)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def extract_location(message: Any) -> str:
    """Extract the human-readable junction phrase from an alert message."""
    text = " ".join(str(message or "").split())
    if not text:
        return "Location unavailable"
    match = _LOCATION_PATTERN.search(text)
    if not match:
        return text
    location = match.group(1).strip(" .,-")
    location = _LOCATION_SUFFIX_PATTERN.sub("", location).strip(" .,-")
    return location or text


def _coordinate(record: Dict[str, Any], keys: Iterable[str]) -> Optional[float]:
    for key in keys:
        value = record.get(key)
        if value in (None, ""):
            continue
        try:
            coordinate = float(value)
        except (TypeError, ValueError):
            continue
        if coordinate:
            return coordinate
    return None


def normalize_faulty_light(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one LTA faulty-light record for presenters and markers."""
    alarm_type = str(record.get("Type") or "").strip()
    start = parse_lta_datetime(record.get("StartDate"))
    end = parse_lta_datetime(record.get("EndDate"))
    message = str(record.get("Message") or "").strip()
    node_id = str(record.get("NodeID") or "").strip()
    alarm_id = str(record.get("AlarmID") or "").strip()
    is_maintenance = bool(str(record.get("EndDate") or "").strip())

    return {
        "alarm_id": alarm_id,
        "node_id": node_id,
        "alarm_type": alarm_type,
        "type_label": ALARM_TYPE_LABELS.get(
            alarm_type,
            f"Alarm type {alarm_type}" if alarm_type else "Signal fault",
        ),
        "status": "maintenance" if is_maintenance else "fault",
        "start": start,
        "end": end,
        "message": message,
        "location": extract_location(message),
        "latitude": _coordinate(record, ("Latitude", "latitude", "Lat", "lat")),
        "longitude": _coordinate(
            record,
            ("Longitude", "longitude", "Lon", "lon"),
        ),
        "location_is_approximate": False,
    }


def normalize_faulty_lights(payload: Any) -> List[Dict[str, Any]]:
    """Normalize and deduplicate faulty-light records by alarm or node."""
    normalized: List[Dict[str, Any]] = []
    seen = set()
    for item in extract_payload_items(payload):
        alert = normalize_faulty_light(item)
        identity = alert["alarm_id"] or (
            alert["node_id"],
            alert["status"],
            alert["start"],
        )
        if identity in seen:
            continue
        seen.add(identity)
        normalized.append(alert)

    priority = {
        ("fault", "4"): 0,
        ("fault", "13"): 1,
        ("fault", ""): 2,
        ("maintenance", "4"): 3,
        ("maintenance", "13"): 4,
        ("maintenance", ""): 5,
    }
    normalized.sort(
        key=lambda alert: (
            priority.get((alert["status"], alert["alarm_type"]), 2),
            alert["start"] or datetime.max,
            alert["node_id"],
        )
    )
    return normalized


def summarize_faulty_lights(alerts: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    """Count unique affected nodes by operational status."""
    node_sets = {"fault": set(), "maintenance": set()}
    anonymous = {"fault": 0, "maintenance": 0}
    for alert in alerts:
        status = alert.get("status", "fault")
        if status not in node_sets:
            status = "fault"
        node_id = alert.get("node_id")
        if node_id:
            node_sets[status].add(str(node_id))
        else:
            anonymous[status] += 1
    faults = len(node_sets["fault"]) + anonymous["fault"]
    maintenance = len(node_sets["maintenance"]) + anonymous["maintenance"]
    return {
        "faults": faults,
        "maintenance": maintenance,
        "total": faults + maintenance,
    }


def _geocode_query(location: str) -> str:
    return re.sub(r"\s*/\s*", " and ", location).strip()


@lru_cache(maxsize=256)
def geocode_location(location: str) -> Optional[Tuple[float, float, str]]:
    """Resolve a junction description through OneMap and cache the outcome."""
    query = _geocode_query(location)
    if not query or query == "Location unavailable":
        return None
    url = (
        f"{ONEMAP_SEARCH_URL}?searchVal={quote_plus(query)}"
        "&returnGeom=Y&getAddrDetails=Y&pageNum=1"
    )
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "lta-transport-dashboard/1.0"},
            timeout=8,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
    except (requests.RequestException, ValueError, AttributeError):
        return None

    for result in results[:5]:
        try:
            latitude = float(result["LATITUDE"])
            longitude = float(result["LONGITUDE"])
        except (KeyError, TypeError, ValueError):
            continue
        if 1.15 <= latitude <= 1.48 and 103.55 <= longitude <= 104.10:
            address = result.get("ADDRESS") or result.get("SEARCHVAL") or query
            return latitude, longitude, str(address)
    return None


def locate_faulty_lights(
    alerts: Iterable[Dict[str, Any]],
    max_lookups: int = 10,
) -> List[Dict[str, Any]]:
    """Add best-effort coordinates without dropping unresolved alerts."""
    located = []
    lookups = 0
    for source in alerts:
        alert = dict(source)
        if alert.get("latitude") and alert.get("longitude"):
            located.append(alert)
            continue
        result = None
        if lookups < max_lookups:
            lookups += 1
            result = geocode_location(str(alert.get("location") or ""))
        if result:
            alert["latitude"], alert["longitude"], alert["geocoded_address"] = result
            alert["location_is_approximate"] = True
        located.append(alert)
    return located
