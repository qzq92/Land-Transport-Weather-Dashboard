"""Pure transformations from provider payloads to frontend view models."""

from datetime import UTC, datetime
from math import asin, cos, radians, sin, sqrt
from typing import Any

from backend.camera_locations import camera_locations


def _records(payload: Any) -> list[dict[str, Any]]:
    """Find the first common list-of-records shape in a provider payload."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("value", "results", "items", "features"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return _records(data)
    return []


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coordinate(
    record: dict[str, Any],
) -> tuple[float | None, float | None]:
    location = record.get("location")
    source = location if isinstance(location, dict) else record
    latitude = _number(
        source.get("latitude", source.get("Latitude", source.get("LATITUDE")))
    )
    longitude = _number(
        source.get("longitude", source.get("Longitude", source.get("LONGITUDE")))
    )
    return latitude, longitude


def _identifier(record: dict[str, Any], fallback: str) -> str:
    for key in (
        "id",
        "stationId",
        "BusStopCode",
        "CameraID",
        "IncidentID",
        "Name",
    ):
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return fallback


def search_places(payload: Any) -> list[dict[str, Any]]:
    """Normalize OneMap search records."""
    places: list[dict[str, Any]] = []
    for index, record in enumerate(_records(payload)):
        latitude, longitude = _coordinate(record)
        if latitude is None or longitude is None:
            continue
        address = str(record.get("ADDRESS") or record.get("address") or "").strip()
        building = str(record.get("BUILDING") or record.get("building") or "").strip()
        label = ", ".join(part for part in (building, address) if part)
        places.append(
            {
                "id": _identifier(record, f"place-{index}"),
                "label": label or "Selected location",
                "latitude": latitude,
                "longitude": longitude,
            }
        )
    return places


def _distance_m(
    latitude: float,
    longitude: float,
    other_latitude: float,
    other_longitude: float,
) -> float:
    radius = 6_371_000.0
    delta_latitude = radians(other_latitude - latitude)
    delta_longitude = radians(other_longitude - longitude)
    value = (
        sin(delta_latitude / 2) ** 2
        + cos(radians(latitude))
        * cos(radians(other_latitude))
        * sin(delta_longitude / 2) ** 2
    )
    return 2 * radius * asin(sqrt(value))


def nearby_places(
    latitude: float,
    longitude: float,
    payloads: dict[str, Any],
) -> dict[str, Any]:
    """Combine OneMap nearby records into a distance-sorted view."""
    places: list[dict[str, Any]] = []
    for category, payload in payloads.items():
        for index, record in enumerate(_records(payload)):
            item_latitude, item_longitude = _coordinate(record)
            if item_latitude is None or item_longitude is None:
                geometry = record.get("geometry", {})
                coordinates = (
                    geometry.get("coordinates")
                    if isinstance(geometry, dict)
                    else None
                )
                if (
                    isinstance(coordinates, list)
                    and len(coordinates) >= 2
                    and not isinstance(coordinates[0], list)
                ):
                    item_longitude = _number(coordinates[0])
                    item_latitude = _number(coordinates[1])
            if item_latitude is None or item_longitude is None:
                continue
            properties = record.get("properties", {})
            properties = properties if isinstance(properties, dict) else {}
            name = (
                record.get("name")
                or record.get("Name")
                or properties.get("name")
                or properties.get("NAME")
                or properties.get("DESCRIPTION")
                or record.get("BUS_STOP_NM")
                or record.get("STN_NAME")
                or record.get("DESCRIPTION")
                or category.replace("-", " ").title()
            )
            distance = _number(
                record.get("distance", record.get("Distance"))
            )
            places.append(
                {
                    "id": f"{category}-{_identifier(record, str(index))}",
                    "name": str(name),
                    "latitude": item_latitude,
                    "longitude": item_longitude,
                    "category": category,
                    "distance_m": round(
                        distance
                        if distance is not None
                        else _distance_m(
                            latitude,
                            longitude,
                            item_latitude,
                            item_longitude,
                        )
                    ),
                    "address": record.get("ADDRESS")
                    or record.get("RoadName")
                    or record.get("ROAD_NAME"),
                }
            )
    places.sort(key=lambda item: item["distance_m"])
    return {
        "centre": {"latitude": latitude, "longitude": longitude},
        "places": places,
    }


def weather_view(payloads: dict[str, Any]) -> dict[str, Any]:
    """Build weather metrics and sensor points from Data.gov.sg V2 feeds."""
    metrics: list[dict[str, Any]] = []
    readings: list[dict[str, Any]] = []
    units = {
        "air-temperature": "°C",
        "rainfall": "mm",
        "relative-humidity": "%",
        "wind-speed": "km/h",
    }
    labels = {
        "air-temperature": "Temperature",
        "rainfall": "Rainfall",
        "relative-humidity": "Humidity",
        "wind-speed": "Wind speed",
    }
    for metric, payload in payloads.items():
        root = payload.get("data", payload) if isinstance(payload, dict) else {}
        stations = root.get("stations", []) if isinstance(root, dict) else []
        station_map = {
            str(station.get("id")): station
            for station in stations
            if isinstance(station, dict)
        }
        groups = root.get("readings", []) if isinstance(root, dict) else []
        group = groups[0] if groups and isinstance(groups[0], dict) else {}
        values: list[float] = []
        for index, item in enumerate(group.get("data", [])):
            if not isinstance(item, dict):
                continue
            value = _number(item.get("value"))
            station_id = str(item.get("stationId", index))
            station = station_map.get(station_id, {})
            latitude, longitude = _coordinate(station)
            if value is None:
                continue
            values.append(value)
            if latitude is not None and longitude is not None:
                readings.append(
                    {
                        "id": f"{metric}-{station_id}",
                        "name": station.get("name", station_id),
                        "latitude": latitude,
                        "longitude": longitude,
                        "metric": metric,
                        "unit": units[metric],
                        "value": value,
                        "observed_at": group.get("timestamp"),
                    }
                )
        average = round(sum(values) / len(values), 1) if values else "—"
        metrics.append(
            {
                "id": metric,
                "label": labels[metric],
                "value": average,
                "unit": units[metric],
                "status": "neutral",
            }
        )
    return {"metrics": metrics, "readings": readings}


def weather_alerts_view(payloads: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize lightning observations and active flood notices."""
    alerts: list[dict[str, Any]] = []
    for alert_type, payload in payloads.items():
        root = payload.get("data", payload) if isinstance(payload, dict) else {}
        records = root.get("records", []) if isinstance(root, dict) else []
        for record_index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            item = record.get("item", {})
            readings = item.get("readings", []) if isinstance(item, dict) else []
            if not isinstance(readings, list):
                continue
            observed_at = record.get("datetime") or record.get("updatedTimestamp")
            for reading_index, reading in enumerate(readings):
                if not isinstance(reading, dict):
                    continue
                if alert_type == "lightning":
                    title = str(reading.get("text") or "Lightning detected")
                    detail = str(reading.get("type") or "Lightning observation")
                    severity = "warning"
                else:
                    title = str(
                        reading.get("description")
                        or reading.get("name")
                        or "Flood alert"
                    )
                    detail = str(reading.get("instruction") or "")
                    severity = "critical"
                latitude, longitude = _coordinate(reading)
                if latitude is None or longitude is None:
                    station = reading.get("station")
                    if isinstance(station, dict):
                        latitude, longitude = _coordinate(station)
                alert = {
                    "id": f"{alert_type}-{record_index}-{reading_index}",
                    "title": title,
                    "detail": detail or None,
                    "severity": severity,
                    "updated_at": observed_at,
                }
                if latitude is not None and longitude is not None:
                    alert["latitude"] = latitude
                    alert["longitude"] = longitude
                alerts.append(alert)
    return alerts


def rail_status_view(payload: Any) -> dict[str, Any]:
    """Normalize the aggregate LTA rail-service status for the dashboard."""
    root = payload.get("value", payload) if isinstance(payload, dict) else {}
    if not isinstance(root, dict):
        return {
            "state": "unknown",
            "summary": "Rail service status is unavailable",
        }
    status = root.get("Status", root.get("status"))
    if status == 1:
        return {
            "state": "normal",
            "summary": "All train services are operational",
        }
    return {
        "state": "disrupted",
        "summary": "Rail service disruption reported",
    }


def environment_view(payloads: dict[str, Any]) -> dict[str, Any]:
    """Create a conservative environment view from heterogeneous feeds."""
    metrics: list[dict[str, Any]] = []
    regions: list[dict[str, Any]] = []
    readings: list[dict[str, Any]] = []
    uv_series: list[dict[str, Any]] = []
    for metric, payload in payloads.items():
        root = payload.get("data", payload) if isinstance(payload, dict) else {}
        if metric == "psi":
            metadata = (
                root.get("regionMetadata", [])
                if isinstance(root, dict)
                else []
            )
            locations = {
                str(region.get("name")): region.get("labelLocation", {})
                for region in metadata
                if isinstance(region, dict)
            }
            items = root.get("items", []) if isinstance(root, dict) else []
            psi_readings = (
                items[0].get("readings", {})
                if items and isinstance(items[0], dict)
                else {}
            )
            values_by_region = (
                psi_readings.get("psi_twenty_four_hourly", {})
                if isinstance(psi_readings, dict)
                else {}
            )
            values = [
                numeric_value
                for raw_value in values_by_region.values()
                if (numeric_value := _number(raw_value)) is not None
            ] if isinstance(values_by_region, dict) else []
            for region, value in values_by_region.items():
                location = locations.get(str(region), {})
                latitude, longitude = _coordinate(
                    location if isinstance(location, dict) else {}
                )
                numeric_value = _number(value)
                if latitude is None or longitude is None or numeric_value is None:
                    continue
                regions.append(
                    {
                        "id": f"psi-{region}",
                        "name": str(region).title(),
                        "latitude": latitude,
                        "longitude": longitude,
                        "psi": round(numeric_value),
                        "pollutant": "24-hour PSI",
                    }
                )
            metrics.append(
                {
                    "id": metric,
                    "label": "PSI",
                    "value": round(sum(values) / len(values), 1) if values else "—",
                    "status": "neutral",
                }
            )
            continue

        if metric == "uv":
            records = root.get("records", []) if isinstance(root, dict) else []
            index_values = [
                index
                for record in records
                if isinstance(record, dict)
                for index in record.get("index", [])
                if isinstance(index, dict)
            ]
            values = [
                value
                for index in index_values
                if (value := _number(index.get("value"))) is not None
            ]
            uv_series.extend(
                {
                    "timestamp": str(index.get("hour") or ""),
                    "value": value,
                }
                for index in index_values
                if (value := _number(index.get("value"))) is not None
            )
            metrics.append(
                {
                    "id": metric,
                    "label": "UV",
                    "value": values[0] if values else "—",
                    "unit": "index",
                    "status": "neutral",
                }
            )
            continue

        if metric == "wbgt":
            records = root.get("records", []) if isinstance(root, dict) else []
            wbgt_values: list[float] = []
            for record in records:
                if not isinstance(record, dict):
                    continue
                item = record.get("item", {})
                station_readings = (
                    item.get("readings", []) if isinstance(item, dict) else []
                )
                observed_at = record.get("datetime") or record.get("updatedTimestamp")
                for index, reading in enumerate(station_readings):
                    if not isinstance(reading, dict):
                        continue
                    value = _number(reading.get("wbgt"))
                    if value is None:
                        continue
                    wbgt_values.append(value)
                    station = reading.get("station", {})
                    station = station if isinstance(station, dict) else {}
                    latitude, longitude = _coordinate(reading)
                    if latitude is None or longitude is None:
                        latitude, longitude = _coordinate(station)
                    if latitude is None or longitude is None:
                        continue
                    readings.append(
                        {
                            "id": f"wbgt-{station.get('id', index)}",
                            "name": station.get("name", "WBGT station"),
                            "latitude": latitude,
                            "longitude": longitude,
                            "metric": "wbgt",
                            "unit": "°C",
                            "value": value,
                            "detail": str(reading.get("heatStress") or "") or None,
                            "observed_at": observed_at,
                        }
                    )
            metrics.append(
                {
                    "id": metric,
                    "label": "WBGT",
                    "value": round(sum(wbgt_values) / len(wbgt_values), 1)
                    if wbgt_values
                    else "—",
                    "unit": "°C",
                    "status": "neutral",
                }
            )
            continue

        records = _records(payload)
        numeric_values: list[float] = []
        for record in records:
            record_readings = record.get("readings", record)
            if isinstance(record_readings, dict):
                for reading_value in record_readings.values():
                    if isinstance(reading_value, dict):
                        numeric_values.extend(
                            number
                            for number in (
                                _number(item) for item in reading_value.values()
                            )
                            if number is not None
                        )
                    else:
                        number = _number(reading_value)
                        if number is not None:
                            numeric_values.append(number)
        summary_value: float | str = (
            round(sum(numeric_values) / len(numeric_values), 1)
            if numeric_values
            else "—"
        )
        metrics.append(
            {
                "id": metric,
                "label": metric.upper(),
                "value": summary_value,
                "status": "neutral",
            }
        )
    return {
        "metrics": metrics,
        "regions": regions,
        "readings": readings,
        "uv_index": uv_series,
    }


def health_clusters_view(payloads: dict[str, Any]) -> list[dict[str, Any]]:
    """Return concise dengue and Zika cluster summaries for the dashboard."""
    clusters: list[dict[str, Any]] = []
    for disease, payload in payloads.items():
        features = payload.get("features", []) if isinstance(payload, dict) else []
        for index, feature in enumerate(features):
            properties = feature.get("properties", {}) if isinstance(feature, dict) else {}
            if not isinstance(properties, dict):
                continue
            cases = _number(properties.get("CASE_SIZE"))
            clusters.append(
                {
                    "id": f"{disease}-{properties.get('OBJECTID', index)}",
                    "disease": disease,
                    "location": str(
                        properties.get("LOCALITY") or "Location unavailable"
                    ),
                    "cases": round(cases) if cases is not None else None,
                }
            )
    return sorted(
        clusters,
        key=lambda cluster: cluster["cases"] or 0,
        reverse=True,
    )


def travel_times_view(payload: Any) -> dict[str, Any]:
    """Normalize LTA expressway travel-time records."""
    journeys = []
    for index, record in enumerate(_records(payload)):
        minutes = _number(
            record.get("EstTime", record.get("TravelTime", record.get("Minutes")))
        )
        journeys.append(
            {
                "id": _identifier(record, f"journey-{index}"),
                "expressway": str(
                    record.get("Name")
                    or record.get("Expressway")
                    or record.get("RoadName")
                    or "Expressway"
                ),
                "direction": str(record.get("Direction") or ""),
                "start": str(record.get("StartPoint") or record.get("Start") or ""),
                "end": str(record.get("EndPoint") or record.get("End") or ""),
                "minutes": round(minutes or 0),
            }
        )
    return {"journeys": journeys, "updated_at": datetime.now(UTC).isoformat()}


def cameras_view(payload: Any) -> dict[str, Any]:
    """Normalize Data.gov.sg traffic-camera data."""
    records = _records(payload)
    if records and isinstance(records[0].get("cameras"), list):
        records = [
            camera
            for camera in records[0]["cameras"]
            if isinstance(camera, dict)
        ]
    cameras = []
    locations_by_camera_id = camera_locations()
    for index, record in enumerate(records):
        latitude, longitude = _coordinate(record)
        if latitude is None or longitude is None:
            continue
        camera_id = str(
            record.get("camera_id")
            or record.get("CameraID")
            or _identifier(record, f"camera-{index}")
        )
        cameras.append(
            {
                "id": camera_id,
                "name": str(
                    record.get("name")
                    or locations_by_camera_id.get(camera_id)
                    or record.get("CameraID")
                    or record.get("camera_id")
                    or "Traffic camera"
                ),
                "latitude": latitude,
                "longitude": longitude,
                "image_url": record.get("image")
                or record.get("ImageLink")
                or "",
                "captured_at": record.get("timestamp"),
            }
        )
    return {"cameras": cameras}


def crowding_view(payload: Any) -> dict[str, Any]:
    """Normalize LTA platform crowd records."""
    readings = []
    for index, record in enumerate(_records(payload)):
        raw_level = str(
            record.get("CrowdLevel") or record.get("Level") or "unknown"
        ).lower()
        level = next(
            (
                candidate
                for candidate in ("low", "moderate", "high")
                if candidate in raw_level
            ),
            "unknown",
        )
        readings.append(
            {
                "id": _identifier(record, f"crowd-{index}"),
                "station": str(
                    record.get("Station")
                    or record.get("StationName")
                    or record.get("StationCode")
                    or "Station"
                ),
                "line": str(record.get("TrainLine") or record.get("Line") or ""),
                "level": level,
                "start_time": record.get("StartTime"),
                "end_time": record.get("EndTime"),
            }
        )
    return {"readings": readings, "updated_at": datetime.now(UTC).isoformat()}


def transport_view(payloads: dict[str, Any]) -> dict[str, Any]:
    """Build summary cards and alert records from transport feeds."""
    incidents = _records(payloads.get("incidents"))
    carparks = _records(payloads.get("carparks"))
    vms = _records(payloads.get("vms"))
    cameras = cameras_view(payloads.get("cameras"))
    taxi_count = 0
    taxi_points: list[dict[str, Any]] = []
    taxi_payload = payloads.get("taxis")
    if isinstance(taxi_payload, dict):
        for feature in taxi_payload.get("features", []):
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties", {})
            if isinstance(properties, dict):
                taxi_count = max(
                    taxi_count,
                    int(_number(properties.get("taxi_count")) or 0),
                )
            geometry = feature.get("geometry", {})
            coordinates = (
                geometry.get("coordinates", [])
                if isinstance(geometry, dict)
                else []
            )
            for coordinate in coordinates[:500]:
                values = coordinate.split() if isinstance(coordinate, str) else coordinate
                if not isinstance(values, (list, tuple)) or len(values) < 2:
                    continue
                longitude = _number(values[0])
                latitude = _number(values[1])
                if latitude is None or longitude is None:
                    continue
                taxi_points.append(
                    {
                        "id": f"taxi-{len(taxi_points)}",
                        "name": "Available taxi",
                        "latitude": latitude,
                        "longitude": longitude,
                        "category": "taxi",
                    }
                )
                if len(taxi_points) >= 500:
                    break
            if len(taxi_points) >= 500:
                break
    alerts = [
        {
            "id": _identifier(record, f"incident-{index}"),
            "title": str(
                record.get("Message")
                or record.get("Type")
                or record.get("Summary")
                or "Road incident"
            ),
            "detail": record.get("RoadName") or record.get("Location"),
            "severity": "warning",
        }
        for index, record in enumerate(incidents)
    ]
    incident_points = [
        {
            "id": f"incident-{index}",
            "name": str(record.get("Type") or "Road incident"),
            "latitude": latitude,
            "longitude": longitude,
            "category": "incident",
            "detail": record.get("Message"),
        }
        for index, record in enumerate(incidents)
        if (latitude := _coordinate(record)[0]) is not None
        if (longitude := _coordinate(record)[1]) is not None
    ]
    vms_points = [
        {
            "id": f"vms-{index}",
            "name": "Variable message sign",
            "latitude": latitude,
            "longitude": longitude,
            "category": "vms",
            "detail": record.get("Message"),
        }
        for index, record in enumerate(vms)
        if (latitude := _coordinate(record)[0]) is not None
        if (longitude := _coordinate(record)[1]) is not None
    ]
    return {
        "metrics": [
            {
                "id": "taxis",
                "label": "Available taxis",
                "value": taxi_count,
                "status": "neutral",
            },
            {
                "id": "cameras",
                "label": "Cameras",
                "value": len(cameras["cameras"]),
                "status": "neutral",
            },
            {
                "id": "carparks",
                "label": "Carparks reporting",
                "value": len(carparks),
                "status": "neutral",
            },
            {
                "id": "incidents",
                "label": "Road incidents",
                "value": len(incidents),
                "status": "warning" if incidents else "good",
            },
            {
                "id": "vms",
                "label": "VMS boards",
                "value": len(vms),
                "status": "neutral",
            },
        ],
        "points": [
            *taxi_points,
            *[
                {**camera, "category": "camera"}
                for camera in cameras["cameras"]
            ],
            *incident_points,
            *vms_points,
        ],
        "incidents": alerts,
        "train_status": [],
    }
