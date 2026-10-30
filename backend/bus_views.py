"""Bus arrival, stop, and route view models."""

from datetime import UTC, datetime
from typing import Any


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _bus_stop_record(stops: dict[str, Any], code: object) -> dict[str, Any]:
    record = stops.get(str(code), {})
    return record if isinstance(record, dict) else {}


def _bus_visit(bus: dict[str, Any], now: datetime) -> dict[str, Any]:
    """Normalize one of the next three buses for a service."""
    estimated = bus.get("EstimatedArrival")
    minutes = None
    if estimated:
        try:
            arrival = datetime.fromisoformat(str(estimated))
            minutes = max(0, round((arrival - now).total_seconds() / 60))
        except ValueError:
            minutes = None
    load_code = str(bus.get("Load", ""))
    return {
        "minutes": minutes,
        "load": {
            "SEA": "seats",
            "SDA": "standing",
            "LSD": "limited",
        }.get(load_code, "unknown"),
        "wheelchair": str(bus.get("Feature", "")) == "WAB",
        "type": bus.get("Type"),
    }


def buses_view(
    payload: Any,
    stop_code: str,
    stops: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize LTA BusArrival responses into one row per service."""
    directory = stops or {}
    services = payload.get("Services", []) if isinstance(payload, dict) else []
    arrivals: list[dict[str, Any]] = []
    now = datetime.now(UTC)
    for service in services:
        if not isinstance(service, dict):
            continue
        visits: list[dict[str, Any]] = []
        destination_code = None
        for bus_key in ("NextBus", "NextBus2", "NextBus3"):
            bus = service.get(bus_key)
            if not isinstance(bus, dict):
                visits.append(
                    {
                        "minutes": None,
                        "load": "unknown",
                        "wheelchair": False,
                        "type": None,
                    }
                )
                continue
            destination_code = destination_code or bus.get("DestinationCode")
            visits.append(_bus_visit(bus, now))
        destination = _bus_stop_record(directory, destination_code)
        arrivals.append(
            {
                "service_no": str(service.get("ServiceNo", "")),
                "destination": _text(destination.get("Description"))
                or _text(destination_code),
                "visits": visits,
            }
        )
    current = _bus_stop_record(directory, stop_code)
    return {
        "stop": {
            "code": stop_code,
            "name": _text(current.get("Description")) or f"Bus stop {stop_code}",
            "road": _text(current.get("RoadName")),
            "latitude": _number(current.get("Latitude")),
            "longitude": _number(current.get("Longitude")),
        },
        "arrivals": arrivals,
    }


def bus_stop_locations(stops: dict[str, Any]) -> dict[str, Any]:
    """Return plottable bus stops for the arrivals map."""
    locations: list[dict[str, Any]] = []
    for code, record in stops.items():
        if not isinstance(record, dict):
            continue
        latitude = _number(record.get("Latitude"))
        longitude = _number(record.get("Longitude"))
        if latitude is None or longitude is None:
            continue
        locations.append(
            {
                "code": str(code),
                "name": _text(record.get("Description")) or str(code),
                "road": _text(record.get("RoadName")),
                "latitude": latitude,
                "longitude": longitude,
            }
        )
    return {"stops": locations}


def bus_service_view(
    records: list[dict[str, Any]],
    service_no: str,
    stops: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Group one service's route stops by direction."""
    directory = stops or {}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        direction = str(record.get("Direction") or "1")
        grouped.setdefault(direction, []).append(record)
    directions: list[dict[str, Any]] = []
    for direction, rows in sorted(grouped.items()):
        ordered = sorted(
            rows,
            key=lambda row: int(_number(row.get("StopSequence")) or 0),
        )
        route_stops: list[dict[str, Any]] = []
        for row in ordered:
            code = str(row.get("BusStopCode") or "")
            info = _bus_stop_record(directory, code)
            route_stops.append(
                {
                    "code": code,
                    "name": _text(info.get("Description")) or code,
                    "sequence": int(_number(row.get("StopSequence")) or 0),
                    "latitude": _number(info.get("Latitude")),
                    "longitude": _number(info.get("Longitude")),
                }
            )
        first = ordered[0] if ordered else {}
        directions.append(
            {
                "direction": direction,
                "origin": route_stops[0]["name"] if route_stops else "",
                "destination": route_stops[-1]["name"] if route_stops else "",
                "first_bus": _text(first.get("WD_FirstBus")),
                "last_bus": _text(first.get("WD_LastBus")),
                "stops": route_stops,
            }
        )
    return {"service_no": service_no, "directions": directions}
