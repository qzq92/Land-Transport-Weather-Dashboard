"""Versioned API route definitions."""

import asyncio
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import StringConstraints
from redis.exceptions import RedisError

from backend.bus_views import bus_service_view, bus_stop_locations, buses_view
from backend.models import (
    ApiResponse,
    CacheMetadata,
    DashboardResponse,
    HealthComponent,
    HealthResponse,
)
from backend.presenters import (
    cameras_view,
    crowding_view,
    environment_view,
    health_clusters_view,
    nearby_places,
    rail_status_view,
    search_places,
    transport_view,
    travel_times_view,
    weather_alerts_view,
    weather_view,
)
from backend.services import (
    EnvironmentService,
    LocationService,
    TransitService,
    TransportService,
    WeatherService,
    gather_named,
)
from backend.upstream import UpstreamError

Latitude = Annotated[float, Query(ge=-90, le=90)]
Longitude = Annotated[float, Query(ge=-180, le=180)]
SearchQuery = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=200),
    Query(),
]
PostalCode = Annotated[str, Query(pattern=r"^\d{6}$")]
BusStopCode = Annotated[str, Query(pattern=r"^\d{5}$")]
ServiceNumber = Annotated[
    str | None,
    Query(pattern=r"^[A-Za-z0-9]{1,4}$"),
]
TrainLine = Literal[
    "BPL",
    "CCL",
    "CEL",
    "CGL",
    "DTL",
    "EWL",
    "NEL",
    "NSL",
    "PLRT",
    "SLRT",
    "TEL",
]

router = APIRouter()


def _service(request: Request, name: str):
    try:
        return getattr(request.app.state.services, name)
    except AttributeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application services are not initialized",
        ) from error


async def _collect(
    calls,
) -> tuple[dict[str, object], CacheMetadata]:
    """Collect partial provider responses and retain cache metadata."""
    names = list(calls)
    results = await asyncio.gather(
        *(calls[name]() for name in names),
        return_exceptions=True,
    )
    responses = {
        name: result
        for name, result in zip(names, results, strict=True)
        if isinstance(result, ApiResponse)
    }
    if not responses:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No upstream provider data is currently available",
        )
    payloads = {name: response.data for name, response in responses.items()}
    metadata = next(iter(responses.values())).meta
    return payloads, metadata


@router.get("/health/live", response_model=HealthResponse, tags=["health"])
async def liveness() -> HealthResponse:
    """Prove that the process can serve requests."""
    return HealthResponse(
        status="ok",
        components={"api": HealthComponent(status="up")},
    )


@router.get("/health/ready", response_model=HealthResponse, tags=["health"])
async def readiness(request: Request, response: Response) -> HealthResponse:
    """Report whether required lifespan-owned dependencies are usable."""
    settings = request.app.state.settings
    http_client = getattr(request.app.state, "http_client", None)
    http_ready = http_client is not None and not http_client.is_closed
    components: dict[str, HealthComponent] = {
        "http": HealthComponent(
            status="up" if http_ready else "down",
            detail=None if http_ready else "HTTP client is unavailable",
        )
    }

    redis_client = getattr(request.app.state, "redis", None)
    redis_error = getattr(request.app.state, "redis_error", None)
    if not settings.redis_url:
        components["redis"] = HealthComponent(status="disabled")
    elif redis_client is None:
        components["redis"] = HealthComponent(
            status="down" if settings.redis_required else "degraded",
            detail=redis_error or "Redis is unavailable",
        )
    else:
        try:
            await redis_client.ping()
            components["redis"] = HealthComponent(status="up")
        except (RedisError, OSError) as error:
            redis_client = None
            components["redis"] = HealthComponent(
                status="down" if settings.redis_required else "degraded",
                detail=str(error),
            )

    ready = http_ready and not (
        settings.redis_required and redis_client is None
    )
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if ready else "not_ready",
        components=components,
    )


@router.get(
    "/locations/search",
    response_model=ApiResponse,
    tags=["locations"],
)
async def search_locations(
    request: Request,
    q: SearchQuery,
    page: Annotated[int, Query(ge=1, le=100)] = 1,
    include_geometry: bool = True,
) -> ApiResponse:
    """Search Singapore addresses with OneMap."""
    service: LocationService = _service(request, "locations")
    return await service.search(q, page, include_geometry)


@router.get(
    "/locations/nearby/{kind}",
    response_model=ApiResponse,
    tags=["locations"],
)
async def nearby_locations(
    request: Request,
    kind: Literal["bus-stops", "mrt-stations"],
    latitude: Latitude,
    longitude: Longitude,
    radius_m: Annotated[int, Query(ge=50, le=5000)] = 500,
) -> ApiResponse:
    """Find nearby public-transport facilities with OneMap."""
    service: LocationService = _service(request, "locations")
    return await service.nearby(kind, latitude, longitude, radius_m)


@router.get(
    "/nearby/search",
    response_model=ApiResponse,
    tags=["locations"],
)
async def nearby_search(
    request: Request,
    q: SearchQuery,
) -> ApiResponse:
    """Return the frontend location-search view."""
    service: LocationService = _service(request, "locations")
    response = await service.search(q, 1, True)
    return response.model_copy(update={"data": search_places(response.data)})


@router.get(
    "/nearby",
    response_model=ApiResponse,
    tags=["locations"],
)
async def nearby_view(
    request: Request,
    latitude: Latitude,
    longitude: Longitude,
    radius: Annotated[int, Query(ge=50, le=5000)] = 2000,
) -> ApiResponse:
    """Combine nearby bus and MRT facilities for the React map."""
    service: LocationService = _service(request, "locations")
    payloads, metadata = await _collect(
        {
            "bus-stops": lambda: service.nearby(
                "bus-stops", latitude, longitude, radius
            ),
            "mrt-stations": lambda: service.nearby(
                "mrt-stations", latitude, longitude, radius
            ),
            "parks": lambda: service.amenity("parks"),
            "sports-fields": lambda: service.amenity("sports-fields"),
            "recycling-bins": lambda: service.amenity("recycling-bins"),
            "hawker-centres": lambda: service.amenity("hawker-centres"),
        }
    )
    return ApiResponse(
        data=nearby_places(latitude, longitude, payloads),
        meta=metadata,
    )


@router.get(
    "/weather/realtime/{metric}",
    response_model=ApiResponse,
    tags=["weather"],
)
async def realtime_weather(
    request: Request,
    metric: Literal[
        "air-temperature",
        "rainfall",
        "relative-humidity",
        "wind-speed",
    ],
) -> ApiResponse:
    """Return one realtime weather measurement feed."""
    service: WeatherService = _service(request, "weather")
    return await service.realtime(metric)


@router.get(
    "/weather/forecasts/{period}",
    response_model=ApiResponse,
    tags=["weather"],
)
async def weather_forecast(
    request: Request,
    period: Literal["2-hour", "24-hour"],
) -> ApiResponse:
    """Return a short-term weather forecast."""
    service: WeatherService = _service(request, "weather")
    return await service.forecast(period)


@router.get(
    "/weather/realtime",
    response_model=ApiResponse,
    tags=["weather"],
)
async def realtime_weather_view(request: Request) -> ApiResponse:
    """Combine sensor readings, WBGT, and weather alerts for the React page."""
    service: WeatherService = _service(request, "weather")
    environment: EnvironmentService = _service(request, "environment")
    metrics = (
        "air-temperature",
        "rainfall",
        "relative-humidity",
        "wind-speed",
    )
    payloads, metadata = await _collect(
        {
            **{
                metric: lambda value=metric: service.realtime(value)
                for metric in metrics
            },
            "lightning": lambda: service.alert("lightning"),
            "flood": lambda: service.alert("flood"),
            "wbgt": lambda: environment.index("wbgt"),
        }
    )
    weather_data = weather_view(
        {metric: payloads.get(metric, {}) for metric in metrics}
    )
    alerts = weather_alerts_view(
        {
            alert_type: payloads.get(alert_type, {})
            for alert_type in ("lightning", "flood")
        }
    )
    weather_data["alerts"] = alerts
    weather_data["readings"].extend(
        {
            "id": alert["id"],
            "name": alert["title"],
            "latitude": alert["latitude"],
            "longitude": alert["longitude"],
            "metric": (
                "lightning" if str(alert["id"]).startswith("lightning-") else "flood"
            ),
            "unit": "",
            "value": alert["title"],
            "detail": alert.get("detail"),
            "observed_at": alert.get("updated_at"),
        }
        for alert in alerts
        if alert.get("latitude") is not None and alert.get("longitude") is not None
    )
    lightning_count = sum(
        str(alert["id"]).startswith("lightning-") for alert in alerts
    )
    flood_count = sum(str(alert["id"]).startswith("flood-") for alert in alerts)
    weather_data["metrics"].extend(
        [
            {
                "id": "lightning",
                "label": "Lightning observations",
                "value": lightning_count,
                "status": "neutral",
            },
            {
                "id": "flood",
                "label": "Flood alerts",
                "value": "No alerts" if flood_count == 0 else flood_count,
                "status": "neutral",
            },
        ]
    )
    wbgt_view = environment_view({"wbgt": payloads.get("wbgt", {})})
    weather_data["metrics"].extend(wbgt_view["metrics"])
    weather_data["readings"].extend(wbgt_view["readings"])
    return ApiResponse(data=weather_data, meta=metadata)


@router.get(
    "/environment/indices/{metric}",
    response_model=ApiResponse,
    tags=["environment"],
)
async def environment_index(
    request: Request,
    metric: Literal["psi", "uv", "wbgt"],
) -> ApiResponse:
    """Return a PSI, UV, or WBGT feed."""
    service: EnvironmentService = _service(request, "environment")
    return await service.index(metric)


@router.get(
    "/environment/clusters/{disease}",
    response_model=ApiResponse,
    tags=["environment"],
)
async def disease_clusters(
    request: Request,
    disease: Literal["dengue", "zika"],
) -> ApiResponse:
    """Return a disease-cluster GeoJSON dataset."""
    service: EnvironmentService = _service(request, "environment")
    return await service.clusters(disease)


@router.get(
    "/environment",
    response_model=ApiResponse,
    tags=["environment"],
)
async def environment_summary(request: Request) -> ApiResponse:
    """Combine environmental indices and public-health clusters."""
    service: EnvironmentService = _service(request, "environment")
    metrics = ("psi", "uv", "wbgt")
    payloads, metadata = await _collect(
        {
            **{
                metric: lambda value=metric: service.index(value)
                for metric in metrics
            },
            "dengue": lambda: service.clusters("dengue"),
            "zika": lambda: service.clusters("zika"),
        }
    )
    environment_data = environment_view(
        {metric: payloads.get(metric, {}) for metric in metrics}
    )
    environment_data["clusters"] = health_clusters_view(
        {
            disease: payloads.get(disease, {})
            for disease in ("dengue", "zika")
        }
    )
    return ApiResponse(data=environment_data, meta=metadata)


@router.get(
    "/healthcare/wait-times",
    response_model=ApiResponse,
    tags=["healthcare"],
)
async def healthcare_wait_times(request: Request) -> ApiResponse:
    """Return official emergency-department queue estimates."""
    service = _service(request, "healthcare")
    return await service.wait_times()


@router.get(
    "/transport/ev/chargers",
    response_model=ApiResponse,
    tags=["transport"],
)
async def ev_chargers(
    request: Request,
    postal_code: PostalCode,
) -> ApiResponse:
    """Return EV chargers for a six-digit Singapore postal code."""
    service: TransportService = _service(request, "transport")
    return await service.ev_chargers(postal_code)


@router.get(
    "/transport/{resource}",
    response_model=ApiResponse,
    tags=["transport"],
)
async def transport_resource(
    request: Request,
    resource: Literal[
        "cameras",
        "incidents",
        "travel-times",
        "taxis",
        "carparks",
        "vms",
        "faulty-lights",
    ],
) -> ApiResponse:
    """Return a road-transport resource."""
    service: TransportService = _service(request, "transport")
    response = await service.resource(resource)
    if resource == "cameras":
        return response.model_copy(update={"data": cameras_view(response.data)})
    if resource == "travel-times":
        return response.model_copy(update={"data": travel_times_view(response.data)})
    return response


@router.get(
    "/transport",
    response_model=ApiResponse,
    tags=["transport"],
)
async def transport_summary(request: Request) -> ApiResponse:
    """Combine live road feeds into the React transport view."""
    service: TransportService = _service(request, "transport")
    resources = ("taxis", "incidents", "carparks", "cameras", "vms")
    payloads, metadata = await _collect(
        {
            resource: lambda value=resource: service.resource(value)
            for resource in resources
        }
    )
    return ApiResponse(data=transport_view(payloads), meta=metadata)


@router.get(
    "/transit/bus/locations",
    response_model=ApiResponse,
    tags=["transit"],
)
async def bus_locations(request: Request) -> ApiResponse:
    """Return coordinates for plotting bus stops on the arrivals map."""
    service: TransitService = _service(request, "transit")
    response = await service.bus_stops(0)
    stops = await service.bus_stop_index()
    return response.model_copy(
        update={"data": bus_stop_locations(stops)}
    )


@router.get(
    "/transit/bus/routes",
    response_model=ApiResponse,
    tags=["transit"],
)
async def bus_route(
    request: Request,
    service_no: Annotated[str, Query(pattern=r"^[A-Za-z0-9]{1,4}")],
) -> ApiResponse:
    """Return ordered stops for one bus service."""
    service: TransitService = _service(request, "transit")
    response = await service.bus_routes(0)
    stops_result, records = await asyncio.gather(
        service.bus_stop_index(),
        service.bus_route_records(service_no),
        return_exceptions=True,
    )
    if isinstance(records, BaseException):
        raise records
    stops = {} if isinstance(stops_result, BaseException) else stops_result
    return response.model_copy(
        update={"data": bus_service_view(records, service_no, stops)}
    )


@router.get(
    "/transit/bus/stops",
    response_model=ApiResponse,
    tags=["transit"],
)
async def bus_stops(
    request: Request,
    skip: Annotated[int, Query(ge=0, le=100000, multiple_of=500)] = 0,
) -> ApiResponse:
    """Return one LTA bus-stop page."""
    service: TransitService = _service(request, "transit")
    return await service.bus_stops(skip)


@router.get(
    "/transit/bus/arrivals",
    response_model=ApiResponse,
    tags=["transit"],
)
async def bus_arrivals(
    request: Request,
    bus_stop_code: BusStopCode,
    service_no: ServiceNumber = None,
) -> ApiResponse:
    """Return arrivals at one bus stop, optionally for one service."""
    service: TransitService = _service(request, "transit")
    return await service.bus_arrivals(bus_stop_code, service_no)


@router.get(
    "/transit/bus/services",
    response_model=ApiResponse,
    tags=["transit"],
)
async def bus_services(
    request: Request,
    skip: Annotated[int, Query(ge=0, le=100000, multiple_of=500)] = 0,
) -> ApiResponse:
    """Return one LTA bus-service page."""
    service: TransitService = _service(request, "transit")
    return await service.bus_services(skip)


@router.get(
    "/transit/rail/banner",
    response_model=ApiResponse,
    tags=["transit"],
)
async def rail_banner(request: Request) -> ApiResponse:
    """Return the operational rail status shown on every dashboard tab."""
    service: TransitService = _service(request, "transit")
    response = await service.rail("status", None)
    rail_status = rail_status_view(response.data)
    rail_status["updated_at"] = datetime.now(tz=UTC).isoformat()
    return response.model_copy(update={"data": rail_status})


@router.get(
    "/transit/rail/{resource}",
    response_model=ApiResponse,
    tags=["transit"],
)
async def rail_resource(
    request: Request,
    resource: Literal["status", "crowding", "forecast"],
    train_line: TrainLine | None = None,
) -> ApiResponse:
    """Return rail status, current crowding, or crowd forecast data."""
    service: TransitService = _service(request, "transit")
    return await service.rail(resource, train_line)


@router.get(
    "/transit/crowding",
    response_model=ApiResponse,
    tags=["transit"],
)
async def crowding_summary(
    request: Request,
    train_line: TrainLine | None = None,
) -> ApiResponse:
    """Return normalized rail crowding records."""
    service: TransitService = _service(request, "transit")
    response = await service.rail("crowding", train_line)
    crowding = crowding_view(response.data)
    if train_line:
        crowding["readings"] = [
            {**reading, "line": reading["line"] or train_line}
            for reading in crowding["readings"]
        ]
    return response.model_copy(update={"data": crowding})


@router.get(
    "/transit/buses",
    response_model=ApiResponse,
    tags=["transit"],
)
async def buses_summary(
    request: Request,
    stop_code: BusStopCode | None = None,
    service_no: ServiceNumber = None,
) -> ApiResponse:
    """Return normalized arrivals for the React bus search."""
    if stop_code is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A bus stop code is required for live arrivals",
        )
    service: TransitService = _service(request, "transit")
    response = await service.bus_arrivals(stop_code, service_no)
    try:
        stops = await service.bus_stop_index()
    except UpstreamError:
        stops = {}
    return response.model_copy(
        update={"data": buses_view(response.data, stop_code, stops)}
    )


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    tags=["dashboard"],
)
async def dashboard(request: Request) -> DashboardResponse:
    """Aggregate key dashboard feeds with partial-failure semantics."""
    weather: WeatherService = _service(request, "weather")
    environment: EnvironmentService = _service(request, "environment")
    transport: TransportService = _service(request, "transport")
    transit: TransitService = _service(request, "transit")
    data, errors = await gather_named(
        {
            "temperature": lambda: weather.realtime("air-temperature"),
            "rainfall": lambda: weather.realtime("rainfall"),
            "humidity": lambda: weather.realtime("relative-humidity"),
            "wind_speed": lambda: weather.realtime("wind-speed"),
            "lightning": lambda: weather.alert("lightning"),
            "flood": lambda: weather.alert("flood"),
            "forecast": lambda: weather.forecast("24-hour"),
            "psi": lambda: environment.index("psi"),
            "cameras": lambda: transport.resource("cameras"),
            "incidents": lambda: transport.resource("incidents"),
            "taxis": lambda: transport.resource("taxis"),
            "faulty_lights": lambda: transport.resource("faulty-lights"),
            "dengue": lambda: environment.clusters("dengue"),
            "zika": lambda: environment.clusters("zika"),
            "rail_status": lambda: transit.rail("status", None),
        }
    )
    provider_data = {
        name: value.get("data")
        for name, value in data.items()
        if isinstance(value, dict)
    }
    weather_data = weather_view(
        {
            "air-temperature": provider_data.get("temperature", {}),
            "rainfall": provider_data.get("rainfall", {}),
            "relative-humidity": provider_data.get("humidity", {}),
            "wind-speed": provider_data.get("wind_speed", {}),
        }
    )
    environment_data = environment_view(
        {"psi": provider_data.get("psi", {})}
    )
    transport_data = transport_view(
        {
            "incidents": provider_data.get("incidents", {}),
            "taxis": provider_data.get("taxis", {}),
        }
    )
    camera_data = cameras_view(provider_data.get("cameras", {}))
    weather_alerts = weather_alerts_view(
        {
            "lightning": provider_data.get("lightning", {}),
            "flood": provider_data.get("flood", {}),
        }
    )
    forecast_payload = provider_data.get("forecast") or {}
    forecast_root = forecast_payload.get("data", {})
    forecast_records = (
        forecast_root.get("records", [])
        if isinstance(forecast_root, dict)
        else []
    )
    forecast_general = (
        forecast_records[0].get("general", {})
        if forecast_records and isinstance(forecast_records[0], dict)
        else {}
    )
    incidents_by_type: dict[str, int] = {}
    incidents_payload = provider_data.get("incidents") or {}
    for incident in incidents_payload.get("value", []):
        if isinstance(incident, dict):
            incident_type = str(incident.get("Type") or "Other")
            incidents_by_type[incident_type] = (
                incidents_by_type.get(incident_type, 0) + 1
            )
    faulty_lights_payload = provider_data.get("faulty_lights") or {}
    faulty_lights = faulty_lights_payload.get("value", [])
    generated_at = datetime.now(tz=UTC)
    rail_status = rail_status_view(provider_data.get("rail_status", {}))
    rail_status["updated_at"] = generated_at.isoformat()
    dashboard_data = {
        "metrics": [
            *weather_data["metrics"],
            *environment_data["metrics"],
            *transport_data["metrics"],
        ],
        "alerts": transport_data["incidents"],
        "map_points": [
            *[
                {**camera, "category": "camera"}
                for camera in camera_data["cameras"]
            ],
            *transport_data["points"],
        ],
        "checkpoint_cameras": [
            camera
            for camera in camera_data["cameras"]
            if camera["id"] in {"2701", "4713"}
        ],
        "rail_status": rail_status,
        "operations": {
            "flood_alerts": sum(
                alert["id"].startswith("flood-") for alert in weather_alerts
            ),
            "lightning_observations": sum(
                alert["id"].startswith("lightning-") for alert in weather_alerts
            ),
            "forecast": forecast_general,
            "traffic": {
                **incidents_by_type,
                "Faulty traffic lights": len(faulty_lights)
                if isinstance(faulty_lights, list)
                else 0,
            },
            "clusters": health_clusters_view(
                {
                    "dengue": provider_data.get("dengue", {}),
                    "zika": provider_data.get("zika", {}),
                }
            ),
        },
    }
    return DashboardResponse(
        data=dashboard_data,
        errors=errors,
        generated_at=generated_at,
    )
