"""Integration tests across routers, services, cache, and mocked HTTP."""

import httpx
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.settings import Settings


def make_app(handler):
    settings = Settings(
        _env_file=None,
        cors_origins=["https://dashboard.example"],
        lta_api_key="lta-test",
        onemap_api_key="onemap-test",
        data_gov_api_key="data-test",
    )
    return create_app(
        settings,
        http_transport=httpx.MockTransport(handler),
    )


def test_all_domain_route_families_use_mocked_providers() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if "/poll-download" in request.url.path:
            return httpx.Response(
                200,
                json={"data": {"url": "https://download.example/clusters.json"}},
            )
        if request.url.host == "download.example":
            return httpx.Response(
                200,
                json={"type": "FeatureCollection", "features": []},
            )
        return httpx.Response(
            200,
            json={
                "path": request.url.path,
                "query": dict(request.url.params),
            },
        )

    app = make_app(handler)
    routes = [
        ("/api/v1/locations/search", {"q": "City Hall"}),
        (
            "/api/v1/locations/nearby/bus-stops",
            {"latitude": 1.29, "longitude": 103.85},
        ),
        ("/api/v1/weather/realtime/rainfall", None),
        ("/api/v1/weather/forecasts/2-hour", None),
        ("/api/v1/environment/indices/psi", None),
        ("/api/v1/environment/indices/uv", None),
        ("/api/v1/environment/indices/wbgt", None),
        ("/api/v1/environment/clusters/dengue", None),
        ("/api/v1/transport/cameras", None),
        ("/api/v1/transport/incidents", None),
        ("/api/v1/transport/travel-times", None),
        ("/api/v1/transport/taxis", None),
        ("/api/v1/transport/carparks", None),
        ("/api/v1/transport/ev/chargers", {"postal_code": "018956"}),
        ("/api/v1/transit/bus/stops", None),
        (
            "/api/v1/transit/bus/arrivals",
            {"bus_stop_code": "01012"},
        ),
        ("/api/v1/transit/bus/services", None),
        ("/api/v1/transit/rail/status", None),
        ("/api/v1/transit/rail/banner", None),
        ("/api/v1/transit/rail/crowding", {"train_line": "EWL"}),
        ("/api/v1/transit/rail/forecast", {"train_line": "EWL"}),
        ("/api/v1/weather/realtime", None),
        ("/api/v1/environment", None),
        ("/api/v1/transport", None),
        ("/api/v1/transit/crowding", {"train_line": "EWL"}),
        (
            "/api/v1/transit/buses",
            {"stop_code": "01012", "service_no": "36"},
        ),
        ("/api/v1/nearby/search", {"q": "City Hall"}),
        (
            "/api/v1/nearby",
            {"latitude": 1.29, "longitude": 103.85},
        ),
    ]

    with TestClient(app) as client:
        responses = [
            client.get(path, params=params)
            for path, params in routes
        ]

    assert all(response.status_code == 200 for response in responses)
    assert all(response.json()["meta"]["state"] == "bypass" for response in responses)
    nearby_request = next(
        item for item in requests if "getNearestBusStops" in item.url.path
    )
    assert nearby_request.headers["Authorization"] == "onemap-test"
    lta_request = next(
        item for item in requests if item.url.path.endswith("/TrafficIncidents")
    )
    assert lta_request.headers["AccountKey"] == "lta-test"


def test_dashboard_keeps_partial_results_when_one_provider_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/TrafficIncidents"):
            return httpx.Response(500, json={"message": "failed"})
        return httpx.Response(200, json={"source": request.url.path})

    app = make_app(handler)
    with TestClient(app) as client:
        response = client.get("/api/v1/dashboard")

    body = response.json()
    assert response.status_code == 200
    assert "incidents" in body["errors"]
    assert {
        "metrics",
        "alerts",
        "map_points",
        "checkpoint_cameras",
        "rail_status",
        "operations",
    } == set(body["data"])
    assert {
        "Temperature",
        "Rainfall",
        "Humidity",
        "Wind speed",
    } <= {metric["label"] for metric in body["data"]["metrics"]}


def test_healthcare_wait_times_route_normalizes_official_pages() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "www.ttsh.com.sg":
            return httpx.Response(
                200,
                text=(
                    "<p>No. of Patients Awaiting Consultation: 2</p>"
                    "<p>Average Consult Wait Time: 10 min</p>"
                ),
            )
        if request.url.host == "www.nhghealth.com.sg":
            return httpx.Response(
                200,
                text=(
                    "<p>Number of patients in queue 3 Patients</p>"
                    "<p>Waiting time to see doctor 8 mins</p>"
                ),
            )
        return httpx.Response(
            200,
            text=(
                "<table><tr><th></th><th>Alexandra Hospital</th></tr>"
                "<tr><td>Number of Patients Waiting for Consult</td>"
                "<td>1 patient(s)</td></tr>"
                "<tr><td>Estimated Wait Time to See Doctor</td>"
                "<td>1 hour(s)</td></tr></table>"
            ),
        )

    app = make_app(handler)
    with TestClient(app) as client:
        response = client.get("/api/v1/healthcare/wait-times")

    assert response.status_code == 200
    facilities = response.json()["data"]["facilities"]
    assert {facility["hospital"] for facility in facilities} == {
        "Tan Tock Seng Hospital",
        "Woodlands Health",
        "Alexandra Hospital",
    }
