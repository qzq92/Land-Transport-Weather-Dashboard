"""Helpers for GTFS realtime train alerts and trip updates."""
# pylint: disable=no-member

from __future__ import annotations

import os
import re
import threading
import time
from typing import Dict, Iterable, Optional, Set

import requests
from google.protobuf.message import DecodeError
from google.transit import gtfs_realtime_pb2

from conf.api_urls import GTFS_TRAIN_SERVICE_ALERTS_URL, GTFS_TRAIN_TRIP_UPDATES_URL
from utils.async_fetcher import get_current_2min_bucket

_GTFS_STATUS_CACHE: Dict[str, Dict[str, object]] = {}
_CACHE_LOCK = threading.Lock()

_LINE_ALIASES = {
    "NS": "NSL",
    "NSL": "NSL",
    "NORTHSOUTHLINE": "NSL",
    "EW": "EWL",
    "EWL": "EWL",
    "EASTWESTLINE": "EWL",
    "CC": "CCL",
    "CCL": "CCL",
    "CIRCLELINE": "CCL",
    "CEL": "CCL",
    "DT": "DTL",
    "DTL": "DTL",
    "DOWNTOWNLINE": "DTL",
    "NE": "NEL",
    "NEL": "NEL",
    "NORTHEASTLINE": "NEL",
    "TE": "TEL",
    "TEL": "TEL",
    "THOMSONEASTCOASTLINE": "TEL",
    "CGL": "EWL",
    "BPL": "BPL",
    "PGL": "PGL",
    "PEL": "PGL",
    "PWL": "PGL",
    "SKL": "SKL",
    "SEL": "SKL",
    "SWL": "SKL",
}

_KNOWN_LINE_TOKENS = sorted(_LINE_ALIASES.keys(), key=len, reverse=True)
_LINE_TOKEN_PATTERN = re.compile(
    rf"\b({'|'.join(re.escape(token) for token in _KNOWN_LINE_TOKENS)})\b",
    flags=re.IGNORECASE,
)

_DISRUPTION_ALERT_EFFECTS = {
    gtfs_realtime_pb2.Alert.Effect.NO_SERVICE,
    gtfs_realtime_pb2.Alert.Effect.REDUCED_SERVICE,
    gtfs_realtime_pb2.Alert.Effect.SIGNIFICANT_DELAYS,
    gtfs_realtime_pb2.Alert.Effect.DETOUR,
    gtfs_realtime_pb2.Alert.Effect.MODIFIED_SERVICE,
    gtfs_realtime_pb2.Alert.Effect.STOP_MOVED,
}

_TRIP_DISRUPTION_RELATIONSHIPS = {
    gtfs_realtime_pb2.TripDescriptor.ScheduleRelationship.CANCELED,
    gtfs_realtime_pb2.TripDescriptor.ScheduleRelationship.DELETED,
}

_STOP_TIME_DISRUPTION_RELATIONSHIPS = {
    gtfs_realtime_pb2.TripUpdate.StopTimeUpdate.ScheduleRelationship.SKIPPED,
}

_STATUS_PRIORITY = {"Normal": 0, "Service disruption": 2, "Delay": 3}


def _lta_headers() -> Optional[Dict[str, str]]:
    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    return {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json",
        "Accept": "application/x-protobuf, application/octet-stream, application/json",
    }


def _request_with_retries(
    url: str,
    headers: Optional[Dict[str, str]],
    timeout: int,
    max_retries: int,
    source_name: str,
) -> Optional[requests.Response]:
    """GET a URL with retry/backoff for transient 5xx and network errors."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers or {}, timeout=timeout)
            if 200 <= response.status_code < 300:
                return response
            if 400 <= response.status_code < 500:
                print(f"GTFS request failed: {source_name} - status={response.status_code}")
                return None
            if 500 <= response.status_code < 600 and attempt < max_retries - 1:
                wait_time = 3 * (2 ** attempt)
                print(
                    f"GTFS request failed with {response.status_code}: {source_name} - "
                    f"retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
                continue
            print(f"GTFS request failed: {source_name} - status={response.status_code}")
            return None
        except requests.exceptions.RequestException as error:
            if attempt < max_retries - 1:
                wait_time = 3 * (2 ** attempt)
                print(
                    f"Error fetching GTFS feed {source_name}: {error} - retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
                continue
            print(
                f"Error fetching GTFS feed {source_name} after {max_retries} attempts: {error}"
            )
    return None


def _extract_gtfs_download_link(metadata: object) -> Optional[str]:
    """Return the signed protobuf download URL from DataMall metadata JSON."""
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("value")
    if not isinstance(value, list) or not value:
        return None
    first = value[0]
    if not isinstance(first, dict):
        return None
    link = first.get("link")
    if isinstance(link, str) and link.startswith("http"):
        return link
    return None


def _fetch_gtfs_payload(url: str, timeout: int = 10, max_retries: int = 3) -> Optional[bytes]:
    """Fetch GTFS protobuf bytes via DataMall metadata JSON then signed download URL."""
    headers = _lta_headers()
    if headers is None:
        return None

    cache_key = f"{url}:{get_current_2min_bucket()}"
    with _CACHE_LOCK:
        cache_item = _GTFS_STATUS_CACHE.get(cache_key)
        if cache_item and isinstance(cache_item.get("payload"), bytes):
            return cache_item["payload"]  # type: ignore[index]

    metadata_response = _request_with_retries(
        url,
        headers=headers,
        timeout=timeout,
        max_retries=max_retries,
        source_name="metadata",
    )
    if metadata_response is None:
        return None

    try:
        metadata = metadata_response.json()
    except ValueError:
        print("GTFS metadata is not valid JSON")
        return None

    download_link = _extract_gtfs_download_link(metadata)
    if not download_link:
        print("GTFS metadata missing download link")
        return None

    protobuf_response = _request_with_retries(
        download_link,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=timeout,
        max_retries=max_retries,
        source_name="protobuf download",
    )
    if protobuf_response is None:
        return None

    payload = protobuf_response.content
    if payload:
        with _CACHE_LOCK:
            _GTFS_STATUS_CACHE.clear()
            _GTFS_STATUS_CACHE[cache_key] = {"payload": payload}
    return payload


def _decode_gtfs_feed(
    payload: Optional[bytes], source_name: str
) -> Optional[gtfs_realtime_pb2.FeedMessage]:
    if not payload:
        return None
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        feed.ParseFromString(payload)
        return feed
    except DecodeError as error:
        print(f"Unable to decode {source_name} GTFS protobuf payload: {error}")
        return None


def _normalize_line_code(raw_code: str) -> Optional[str]:
    if not raw_code:
        return None
    compact = re.sub(r"[^A-Za-z0-9]", "", raw_code).upper()
    return _LINE_ALIASES.get(compact)


def _extract_line_codes_from_texts(texts: Iterable[str]) -> Set[str]:
    line_codes: Set[str] = set()
    for text in texts:
        if not text:
            continue
        upper_text = text.upper()
        for token in _LINE_TOKEN_PATTERN.findall(upper_text):
            normalized = _normalize_line_code(token)
            if normalized:
                line_codes.add(normalized)
    return line_codes


def _collect_translations(translation_message: object) -> str:
    if not translation_message:
        return ""
    translations = getattr(translation_message, "translation", [])
    values = [getattr(entry, "text", "") for entry in translations if getattr(entry, "text", "")]
    return " ".join(values).strip()


def _upsert_line_status(
    line_status_map: Dict[str, Dict[str, object]],
    line_code: str,
    *,
    status: int,
    status_text: str,
    reason: str,
    has_message: bool = True,
) -> None:
    existing = line_status_map.get(line_code)
    if existing is None:
        line_status_map[line_code] = {
            "status": status,
            "status_text": status_text,
            "has_message": has_message,
            "reason": reason,
        }
        return

    existing_status = int(existing.get("status", 1))
    if status > existing_status:
        existing["status"] = status
    current_status_text = str(existing.get("status_text", "Normal"))
    if _STATUS_PRIORITY.get(status_text, 0) > _STATUS_PRIORITY.get(current_status_text, 0):
        existing["status_text"] = status_text
    if reason:
        existing["reason"] = reason
    if has_message:
        existing["has_message"] = True


def fetch_gtfs_train_service_alerts() -> Dict[str, Dict[str, object]]:
    """Fetch and parse GTFS service alerts into per-line status."""
    payload = _fetch_gtfs_payload(GTFS_TRAIN_SERVICE_ALERTS_URL)
    feed = _decode_gtfs_feed(payload, "service alerts")
    if feed is None:
        return {}

    line_status_map: Dict[str, Dict[str, object]] = {}
    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue
        alert = entity.alert
        header_text = _collect_translations(getattr(alert, "header_text", None))
        description_text = _collect_translations(getattr(alert, "description_text", None))
        url_text = _collect_translations(getattr(alert, "url", None))

        route_tokens = []
        for informed_entity in alert.informed_entity:
            route_tokens.extend(
                [
                    informed_entity.route_id,
                    informed_entity.stop_id,
                    informed_entity.trip.route_id,
                    informed_entity.trip.trip_id,
                    informed_entity.trip.start_date,
                ]
            )
        line_codes = _extract_line_codes_from_texts(
            [header_text, description_text, url_text, " ".join(route_tokens)]
        )
        if not line_codes:
            continue

        is_disruption = alert.effect in _DISRUPTION_ALERT_EFFECTS
        status = 2 if is_disruption else 1
        status_text = "Service disruption" if is_disruption else "Normal"
        reason = description_text or header_text or "Service advisory"
        for line_code in line_codes:
            _upsert_line_status(
                line_status_map,
                line_code,
                status=status,
                status_text=status_text,
                reason=reason,
                has_message=True,
            )
    return line_status_map


def fetch_gtfs_train_trip_updates() -> Dict[str, Dict[str, object]]:
    """Fetch and parse GTFS trip updates into per-line status."""
    payload = _fetch_gtfs_payload(GTFS_TRAIN_TRIP_UPDATES_URL)
    feed = _decode_gtfs_feed(payload, "trip updates")
    if feed is None:
        return {}

    line_status_map: Dict[str, Dict[str, object]] = {}
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        trip_update = entity.trip_update
        trip = trip_update.trip
        line_codes = _extract_line_codes_from_texts(
            [trip.route_id, trip.trip_id, trip.start_date, trip_update.vehicle.id]
        )
        if not line_codes:
            continue

        has_disruption = trip.schedule_relationship in _TRIP_DISRUPTION_RELATIONSHIPS
        has_delay = False
        for stop_update in trip_update.stop_time_update:
            if stop_update.schedule_relationship in _STOP_TIME_DISRUPTION_RELATIONSHIPS:
                has_disruption = True
            arrival_delay = stop_update.arrival.delay if stop_update.HasField("arrival") else 0
            departure_delay = stop_update.departure.delay if stop_update.HasField("departure") else 0
            if abs(arrival_delay) >= 180 or abs(departure_delay) >= 180:
                has_disruption = True
                has_delay = True
            elif arrival_delay or departure_delay:
                has_delay = True

        if not has_disruption and not has_delay:
            continue

        status = 2 if has_disruption else 1
        status_text = "Delay" if has_delay else "Service disruption"
        reason = "Trip update indicates delays or service adjustments"
        for line_code in line_codes:
            _upsert_line_status(
                line_status_map,
                line_code,
                status=status,
                status_text=status_text,
                reason=reason,
                has_message=True,
            )
    return line_status_map


def merge_gtfs_with_legacy_status(
    legacy_line_status_map: Dict[str, Dict[str, object]],
    service_alerts_map: Dict[str, Dict[str, object]],
    trip_updates_map: Dict[str, Dict[str, object]],
) -> Dict[str, Dict[str, object]]:
    """Merge maps with GTFS priority and legacy fallback."""
    merged = dict(legacy_line_status_map)
    for gtfs_map in (service_alerts_map, trip_updates_map):
        for line_code, status_info in gtfs_map.items():
            merged[line_code] = dict(status_info)
    return merged
