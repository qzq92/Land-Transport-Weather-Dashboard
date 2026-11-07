"""Domain services for external Singapore transport and environment APIs."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from math import asin, cos, radians, sin, sqrt
from typing import Any, ClassVar, Literal

from conf.api_urls import (
    BICYCLE_PARKING_URL,
    BUS_ARRIVAL_URL,
    BUS_ROUTES_URL,
    BUS_SERVICES_URL,
    BUS_STOPS_URL,
    CARPARK_AVAILABILITY_URL,
    DATA_GOV_REALTIME_API_BASE,
    DENGUE_POLL_DOWNLOAD_URL,
    EST_TRAVEL_TIMES_URL,
    EV_CHARGING_BATCH_URL,
    EV_CHARGING_URL,
    FAULTY_TRAFFIC_LIGHTS_URL,
    FLOOD_ALERTS_URL,
    HAWKER_CENTRES_POLL_DOWNLOAD_URL,
    KTPH_EMERGENCY_WAIT_URL,
    LIGHTNING_URL,
    NUHS_EMERGENCY_WAIT_URL,
    ONEMAP_NEAREST_BUS_STOPS_URL,
    ONEMAP_NEAREST_MRT_STOPS_URL,
    ONEMAP_SEARCH_URL,
    ONEMAP_TOKEN_URL,
    PARKS_POLL_DOWNLOAD_URL,
    PCD_FORECAST_URL,
    PCD_REALTIME_URL,
    PSI_URL,
    RECYCLING_BINS_POLL_DOWNLOAD_URL,
    SPORTS_FIELDS_POLL_DOWNLOAD_URL,
    TAXI_API_URL,
    TAXI_STANDS_URL,
    TRAFFIC_IMAGES_API_URL,
    TRAFFIC_INCIDENTS_URL,
    TRAIN_SERVICE_ALERTS_URL,
    TTSH_EMERGENCY_WAIT_URL,
    UV_URL,
    VMS_URL,
    WBGT_URL,
    WEATHER_2H_FORECAST_URL,
    WEATHER_24H_FORECAST_URL,
    WOODLANDS_EMERGENCY_WAIT_URL,
    ZIKA_POLL_DOWNLOAD_URL,
)

from backend.bus_views import buses_view
from backend.cache import JsonCache
from backend.healthcare import healthcare_view
from backend.lta_pages import paged_lta_values, secure_batch_link
from backend.models import ApiResponse
from backend.settings import Settings
from backend.upstream import UpstreamClient, UpstreamError

RealtimeMetric = Literal[
    "air-temperature",
    "rainfall",
    "relative-humidity",
    "wind-speed",
]
WeatherAlertResource = Literal["lightning", "flood"]
AmenityKind = Literal["parks", "sports-fields", "recycling-bins", "hawker-centres"]


class ProviderService:
    """Common cached provider request behavior."""

    def __init__(
        self,
        upstream: UpstreamClient,
        cache: JsonCache,
        settings: Settings,
    ) -> None:
        self.upstream = upstream
        self.cache = cache
        self.settings = settings

    def data_gov_headers(self) -> dict[str, str]:
        """Build headers for Data.gov.sg requests, including an optional API key."""
        headers = {"Accept": "application/json"}
        if self.settings.data_gov_api_key:
            headers["X-Api-Key"] = self.settings.data_gov_api_key
        return headers

    def lta_headers(self) -> dict[str, str]:
        """Build authenticated headers for LTA DataMall requests."""
        if not self.settings.lta_api_key:
            raise UpstreamError("LTA_API_KEY is not configured", 503)
        return {
            "Accept": "application/json",
            "AccountKey": self.settings.lta_api_key,
        }

    async def cached_get(
        self,
        namespace: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        ttl: int | None = None,
        stale_ttl: int | None = None,
    ) -> ApiResponse:
        """Fetch JSON through the shared cache with request parameters in its key."""
        key_parameters = {"url": url, **(params or {})}
        return await self.cache.get_or_fetch(
            namespace,
            key_parameters,
            lambda: self.upstream.get_json(
                url,
                params=params,
                headers=headers,
            ),
            ttl_seconds=ttl,
            stale_seconds=stale_ttl,
        )

    async def cached_text(
        self,
        namespace: str,
        url: str,
        *,
        ttl: int,
        stale_ttl: int = 86_400,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        """Fetch and cache an official HTML page as text."""
        request_headers = {"Accept": "text/html", **(headers or {})}
        return await self.cache.get_or_fetch(
            namespace,
            {"url": url},
            lambda: self.upstream.get_text(
                url,
                headers=request_headers,
            ),
            ttl_seconds=ttl,
            stale_seconds=stale_ttl,
        )


class LocationService(ProviderService):
    """OneMap address search and legacy nearby transport endpoints."""

    def __init__(
        self,
        upstream: UpstreamClient,
        cache: JsonCache,
        settings: Settings,
    ) -> None:
        super().__init__(upstream, cache, settings)
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    async def search(
        self,
        query: str,
        page: int,
        include_geometry: bool,
    ) -> ApiResponse:
        """Search OneMap for Singapore addresses and optional geometry."""
        params = {
            "searchVal": query,
            "returnGeom": "Y" if include_geometry else "N",
            "getAddrDetails": "Y",
            "pageNum": page,
        }
        return await self.cached_get(
            "locations:search",
            ONEMAP_SEARCH_URL,
            params=params,
            ttl=86400,
        )

    async def nearby(
        self,
        kind: Literal["bus-stops", "mrt-stations"],
        latitude: float,
        longitude: float,
        radius_m: int,
    ) -> ApiResponse:
        """Return legacy OneMap nearby bus-stop or MRT/LRT results."""
        urls = {
            "bus-stops": ONEMAP_NEAREST_BUS_STOPS_URL,
            "mrt-stations": ONEMAP_NEAREST_MRT_STOPS_URL,
        }
        token = await self._get_token()
        return await self.cached_get(
            f"locations:nearby:{kind}",
            urls[kind],
            params={
                "latitude": latitude,
                "longitude": longitude,
                "radius_in_meters": radius_m,
            },
            headers={"Authorization": token} if token else None,
            ttl=600,
        )

    async def amenity(self, kind: AmenityKind) -> ApiResponse:
        """Download and cache a public amenity GeoJSON dataset."""
        poll_url = {
            "parks": PARKS_POLL_DOWNLOAD_URL,
            "sports-fields": SPORTS_FIELDS_POLL_DOWNLOAD_URL,
            "recycling-bins": RECYCLING_BINS_POLL_DOWNLOAD_URL,
            "hawker-centres": HAWKER_CENTRES_POLL_DOWNLOAD_URL,
        }[kind]

        async def fetch() -> Any:
            poll = await self.upstream.get_json(
                poll_url,
                headers=self.data_gov_headers(),
            )
            data = poll.get("data", {}) if isinstance(poll, dict) else {}
            download_url = data.get("url") if isinstance(data, dict) else None
            if not isinstance(download_url, str) or not download_url.startswith(
                "https://"
            ):
                raise UpstreamError(
                    "Amenity provider did not return a secure download URL",
                    502,
                )
            return await self.upstream.get_json(download_url)

        return await self.cache.get_or_fetch(
            f"locations:amenity:{kind}",
            {"poll_url": poll_url},
            fetch,
            ttl_seconds=86400,
            stale_seconds=604800,
        )

    async def _get_token(self) -> str | None:
        if self.settings.onemap_api_key:
            return self.settings.onemap_api_key
        if not (
            self.settings.onemap_email
            and self.settings.onemap_email_password
        ):
            return None
        if self._token and time.time() < self._token_expires_at:
            return self._token
        async with self._token_lock:
            if self._token and time.time() < self._token_expires_at:
                return self._token
            payload = {
                "email": self.settings.onemap_email,
                "password": self.settings.onemap_email_password,
            }
            result = await self.upstream.post_json(
                ONEMAP_TOKEN_URL,
                payload=payload,
            )
            token = result.get("access_token") if isinstance(result, dict) else None
            if not token:
                raise UpstreamError("OneMap did not return an access token", 502)
            self._token = str(token)
            self._token_expires_at = time.time() + 86400
            return self._token


class WeatherService(ProviderService):
    """Realtime weather measurements and forecasts."""

    async def realtime(self, metric: RealtimeMetric) -> ApiResponse:
        """Return a cached realtime weather metric."""
        return await self.cached_get(
            f"weather:realtime:{metric}",
            f"{DATA_GOV_REALTIME_API_BASE}/{metric}",
            headers=self.data_gov_headers(),
            ttl=120,
        )

    async def forecast(
        self,
        period: Literal["2-hour", "24-hour"],
    ) -> ApiResponse:
        """Return a cached two-hour or twenty-four-hour weather forecast."""
        url = {
            "2-hour": WEATHER_2H_FORECAST_URL,
            "24-hour": WEATHER_24H_FORECAST_URL,
        }[period]
        return await self.cached_get(
            f"weather:forecast:{period}",
            url,
            headers=self.data_gov_headers(),
            ttl=600,
        )

    async def alert(self, resource: WeatherAlertResource) -> ApiResponse:
        """Return a cached lightning observation or flood-alert feed."""
        url = {
            "lightning": LIGHTNING_URL,
            "flood": FLOOD_ALERTS_URL,
        }[resource]
        return await self.cached_get(
            f"weather:alert:{resource}",
            url,
            headers=self.data_gov_headers(),
            ttl=120,
        )


class EnvironmentService(ProviderService):
    """Environmental indices and disease clusters."""

    async def index(
        self,
        metric: Literal["psi", "uv", "wbgt"],
    ) -> ApiResponse:
        """Return a cached PSI, UV, or WBGT environmental index."""
        url = {"psi": PSI_URL, "uv": UV_URL, "wbgt": WBGT_URL}[metric]
        return await self.cached_get(
            f"environment:{metric}",
            url,
            headers=self.data_gov_headers(),
            ttl=120,
        )

    async def clusters(
        self,
        disease: Literal["dengue", "zika"],
    ) -> ApiResponse:
        """Download and cache dengue or Zika cluster data."""
        poll_url = {
            "dengue": DENGUE_POLL_DOWNLOAD_URL,
            "zika": ZIKA_POLL_DOWNLOAD_URL,
        }[disease]

        async def fetch() -> Any:
            poll = await self.upstream.get_json(
                poll_url,
                headers=self.data_gov_headers(),
            )
            download_url = None
            if isinstance(poll, dict):
                download_url = poll.get("url")
                if not download_url and isinstance(poll.get("data"), dict):
                    download_url = poll["data"].get("url")
            if not isinstance(download_url, str) or not download_url.startswith(
                "https://"
            ):
                raise UpstreamError(
                    "Cluster provider did not return a secure download URL",
                    502,
                )
            return await self.upstream.get_json(download_url)

        return await self.cache.get_or_fetch(
            f"environment:clusters:{disease}",
            {"poll_url": poll_url},
            fetch,
            ttl_seconds=86400,
            stale_seconds=604800,
        )


class HealthcareService(ProviderService):
    """Official hospital emergency queue pages."""

    PAGE_HEADERS: ClassVar[dict[str, str]] = {
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-SG,en;q=0.9",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    }
    SOURCES: ClassVar[dict[str, dict[str, str]]] = {
        "ttsh": {
            "name": "Tan Tock Seng Hospital",
            "url": TTSH_EMERGENCY_WAIT_URL,
        },
        "woodlands": {
            "name": "Woodlands Health",
            "url": WOODLANDS_EMERGENCY_WAIT_URL,
        },
        "ktph": {
            "name": "Khoo Teck Puat Hospital",
            "url": KTPH_EMERGENCY_WAIT_URL,
        },
        "nuhs": {
            "name": "NUHS hospitals",
            "url": NUHS_EMERGENCY_WAIT_URL,
        },
    }

    async def wait_times(self) -> ApiResponse:
        """Fetch, parse, and cache the official hospital wait pages."""

        async def fetch() -> dict[str, Any]:
            results = await asyncio.gather(
                *(
                    self.cached_text(
                        f"healthcare:wait-times:{source}",
                        details["url"],
                        ttl=1_800,
                        stale_ttl=86_400,
                        headers=self.PAGE_HEADERS,
                    )
                    for source, details in self.SOURCES.items()
                ),
                return_exceptions=True,
            )
            pages: dict[str, str] = {}
            errors: dict[str, str] = {}
            for source, result in zip(self.SOURCES, results, strict=True):
                if isinstance(result, BaseException):
                    errors[source] = str(result)
                elif isinstance(result.data, str):
                    pages[source] = result.data
                else:
                    errors[source] = "Provider returned a non-text page"
            view = healthcare_view(pages, self.SOURCES, errors)
            if not view["facilities"] and errors:
                raise UpstreamError(
                    "Hospital waiting-time sources are unavailable",
                    503,
                )
            return view

        return await self.cache.get_or_fetch(
            "healthcare:wait-times",
            {"sources": self.SOURCES, "parser": "last-updated-datetime-v1"},
            fetch,
            ttl_seconds=1_800,
            stale_seconds=86_400,
        )


class TransportService(ProviderService):
    """Road transport, taxi, carpark, and EV data."""

    async def resource(
        self,
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
        """Return a cached road-transport resource from its configured provider."""
        specs = {
            "cameras": (TRAFFIC_IMAGES_API_URL, False, 120),
            "incidents": (TRAFFIC_INCIDENTS_URL, True, 120),
            "travel-times": (EST_TRAVEL_TIMES_URL, True, 120),
            "taxis": (TAXI_API_URL, False, 120),
            "carparks": (CARPARK_AVAILABILITY_URL, True, 120),
            "vms": (VMS_URL, True, 120),
            "faulty-lights": (FAULTY_TRAFFIC_LIGHTS_URL, True, 120),
        }
        url, requires_lta, ttl = specs[resource]
        headers = self.lta_headers() if requires_lta else self.data_gov_headers()
        return await self.cached_get(
            f"transport:{resource}",
            url,
            headers=headers,
            ttl=ttl,
        )

    async def ev_chargers(self, postal_code: str) -> ApiResponse:
        """Return EV charging points matching a six-digit postal code."""
        return await self.cached_get(
            "transport:ev",
            EV_CHARGING_URL,
            params={"PostalCode": postal_code},
            headers=self.lta_headers(),
            ttl=3600,
        )

    async def taxi_stands(self) -> ApiResponse:
        """Return the LTA taxi-stand directory."""
        return await self.cached_get(
            "transport:taxi-stands",
            TAXI_STANDS_URL,
            headers=self.lta_headers(),
            ttl=86400,
        )

    async def all_carparks(self) -> ApiResponse:
        """Return every LTA carpark availability page."""
        return await paged_lta_values(
            self.cached_get,
            self.lta_headers(),
            "transport:carparks",
            CARPARK_AVAILABILITY_URL,
            ttl=120,
            max_skip=5000,
        )

    async def bicycle_parking(
        self,
        latitude: float,
        longitude: float,
        radius_m: int,
    ) -> ApiResponse:
        """Return LTA bicycle parking within Dist km of a point."""
        return await self.cached_get(
            "transport:bicycle-parking",
            BICYCLE_PARKING_URL,
            params={
                "Lat": latitude,
                "Long": longitude,
                "Dist": max(radius_m / 1000.0, 0.1),
            },
            headers=self.lta_headers(),
            ttl=600,
        )

    async def ev_chargers_batch(self) -> ApiResponse:
        """Return island-wide EV chargers from the LTA EVCBatch listing."""

        async def fetch() -> Any:
            listing = await self.upstream.get_json(
                EV_CHARGING_BATCH_URL,
                headers=self.lta_headers(),
            )
            link = secure_batch_link(listing)
            if link is None:
                return listing
            return await self.upstream.get_json(link)

        return await self.cache.get_or_fetch(
            "transport:ev-chargers",
            {"url": EV_CHARGING_BATCH_URL, "representation": "file"},
            fetch,
            ttl_seconds=3600,
            stale_seconds=86400,
        )


class TransitService(ProviderService):
    """Bus and rail transit data, including live nearby bus arrivals."""

    async def _paged_values(
        self,
        fetch: Callable[[int], Awaitable[ApiResponse]],
        *,
        page_size: int = 500,
        max_skip: int,
    ) -> list[dict[str, Any]]:
        """Read cached LTA pages until a short page or an empty page."""
        records: list[dict[str, Any]] = []
        skip = 0
        while skip < max_skip:
            batch = range(skip, min(skip + page_size * 4, max_skip), page_size)
            pages = await asyncio.gather(*(fetch(item) for item in batch))
            finished = False
            for response in pages:
                payload = response.data if isinstance(response.data, dict) else {}
                page = payload.get("value", [])
                if not isinstance(page, list) or not page:
                    finished = True
                    break
                records.extend(item for item in page if isinstance(item, dict))
                if len(page) < page_size:
                    finished = True
                    break
            if finished:
                break
            skip = batch[-1] + page_size
        return records

    async def bus_stops(self, skip: int) -> ApiResponse:
        """Fetch one paginated page of LTA bus stops."""
        return await self.cached_get(
            "transit:bus-stops",
            BUS_STOPS_URL,
            params={"$skip": skip},
            headers=self.lta_headers(),
            ttl=86400,
        )

    async def all_bus_stops(self) -> ApiResponse:
        """Return every LTA bus-stop directory page."""
        return await paged_lta_values(
            self.cached_get,
            self.lta_headers(),
            "transit:bus-stops",
            BUS_STOPS_URL,
            ttl=86400,
            max_skip=15000,
        )

    async def nearby_bus_arrivals(
        self,
        stops_payload: Any,
        latitude: float,
        longitude: float,
        radius_m: int,
    ) -> dict[str, dict[str, Any]]:
        """Fetch live arrivals for every bus stop within the nearby radius."""
        payload = stops_payload if isinstance(stops_payload, dict) else {}
        records = payload.get("value", [])
        if not isinstance(records, list):
            return {}

        def distance_m(record: dict[str, Any]) -> float | None:
            try:
                other_latitude = float(record["Latitude"])
                other_longitude = float(record["Longitude"])
            except (KeyError, TypeError, ValueError):
                return None
            delta_latitude = radians(other_latitude - latitude)
            delta_longitude = radians(other_longitude - longitude)
            value = (
                sin(delta_latitude / 2) ** 2
                + cos(radians(latitude))
                * cos(radians(other_latitude))
                * sin(delta_longitude / 2) ** 2
            )
            return 2 * 6_371_000 * asin(sqrt(value))

        nearby_codes = [
            str(record["BusStopCode"])
            for record in records
            if isinstance(record, dict)
            and record.get("BusStopCode")
            and (distance := distance_m(record)) is not None
            and distance <= radius_m
        ]
        stop_index = {
            str(record["BusStopCode"]): record
            for record in records
            if isinstance(record, dict) and record.get("BusStopCode")
        }
        responses = await asyncio.gather(
            *(self.bus_arrivals(code, None) for code in nearby_codes),
            return_exceptions=True,
        )
        result: dict[str, dict[str, Any]] = {}
        for code, response in zip(nearby_codes, responses, strict=True):
            if isinstance(response, BaseException):
                continue
            result[code] = buses_view(response.data, code, stop_index)
        return result

    async def bus_stop_index(self) -> dict[str, dict[str, Any]]:
        """Load the cached LTA bus-stop directory, keyed by stop code."""
        records = await self._paged_values(self.bus_stops, max_skip=15000)
        return {
            str(record["BusStopCode"]): record
            for record in records
            if record.get("BusStopCode")
        }

    async def bus_arrivals(
        self,
        bus_stop_code: str,
        service_no: str | None,
    ) -> ApiResponse:
        """Fetch bus arrivals for a stop, optionally filtered by service number."""
        params = {"BusStopCode": bus_stop_code}
        if service_no:
            params["ServiceNo"] = service_no
        return await self.cached_get(
            "transit:bus-arrivals",
            BUS_ARRIVAL_URL,
            params=params,
            headers=self.lta_headers(),
            ttl=30,
        )

    async def bus_services(self, skip: int) -> ApiResponse:
        """Fetch one paginated page of LTA bus service metadata."""
        return await self.cached_get(
            "transit:bus-services",
            BUS_SERVICES_URL,
            params={"$skip": skip},
            headers=self.lta_headers(),
            ttl=86400,
        )

    async def bus_routes(self, skip: int) -> ApiResponse:
        """Fetch one paginated page of LTA bus route metadata."""
        return await self.cached_get(
            "transit:bus-routes",
            BUS_ROUTES_URL,
            params={"$skip": skip},
            headers=self.lta_headers(),
            ttl=86400,
        )

    async def bus_route_records(self, service_no: str) -> list[dict[str, Any]]:
        """Return every cached route stop for one service number."""
        wanted = service_no.upper()
        records = await self._paged_values(self.bus_routes, max_skip=30000)
        return [
            record
            for record in records
            if str(record.get("ServiceNo", "")).upper() == wanted
        ]

    async def rail(
        self,
        resource: Literal["status", "crowding", "forecast"],
        train_line: str | None,
    ) -> ApiResponse:
        """Fetch cached rail status, crowding, or forecast data."""
        specs = {
            "status": (TRAIN_SERVICE_ALERTS_URL, 120),
            "crowding": (PCD_REALTIME_URL, 120),
            "forecast": (PCD_FORECAST_URL, 600),
        }
        url, ttl = specs[resource]
        params = {"TrainLine": train_line} if train_line else None
        return await self.cached_get(
            f"transit:rail:{resource}",
            url,
            params=params,
            headers=self.lta_headers(),
            ttl=ttl,
        )


async def gather_named(
    calls: dict[str, Callable[[], Awaitable[ApiResponse]]],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Run aggregate calls concurrently while retaining partial successes."""
    names = list(calls)
    results = await asyncio.gather(
        *(calls[name]() for name in names),
        return_exceptions=True,
    )
    data: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for name, result in zip(names, results, strict=True):
        if isinstance(result, BaseException):
            errors[name] = str(result)
        else:
            data[name] = result.model_dump(mode="json")
    return data, errors
