"""Integration tests across routers, services, cache, and mocked HTTP."""

import httpx
from backend.main import create_app
from backend.settings import Settings
from fastapi.testclient import TestClient


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
        ("/api/v1/transit/crowding/forecast", {"train_line": "EWL"}),
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
    nearby_lta_paths = {item.url.path for item in requests}
    assert {
        "/ltaodataservice/BusStops",
        "/ltaodataservice/TaxiStands",
        "/ltaodataservice/v3/BicycleParking",
        "/ltaodataservice/CarParkAvailabilityv2",
        "/ltaodataservice/EVCBatch",
    } <= nearby_lta_paths
    bicycle_request = next(
        item
        for item in requests
        if item.url.path.endswith("/v3/BicycleParking")
    )
    assert float(bicycle_request.url.params["Dist"]) == 2.0
    assert bicycle_request.headers["AccountKey"] == "lta-test"


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


def test_crowding_route_labels_records_with_requested_train_line() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/PCDRealTime"):
            assert request.url.params["TrainLine"] == "CCL"
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "Station": "CC31 CANTONMENT MRT STATION",
                            "CrowdLevel": "low",
                            "StartTime": "2026-09-12T00:00:00",
                            "EndTime": "2026-09-12T00:10:00",
                        }
                    ]
                },
            )
        return httpx.Response(200, json={"value": []})

    app = make_app(handler)
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/transit/crowding",
            params={"train_line": "CCL"},
        )

    assert response.status_code == 200
    reading = response.json()["data"]["readings"][0]
    assert reading["line"] == "CCL"
    assert reading["station"] == "CC31"
    assert reading["station_name"] == "CANTONMENT MRT STATION"
    assert reading["start_time"] == "2026-09-12T00:00:00"
    assert reading["end_time"] == "2026-09-12T00:10:00"


def test_crowding_forecast_route_uses_pcd_forecast() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/PCDForecast"):
            assert request.url.params["TrainLine"] == "CCL"
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "Date": "2026-09-12T00:00:00+08:00",
                            "Stations": [
                                {
                                    "Station": "CE1",
                                    "Interval": [
                                        {
                                            "Start": "2026-09-12T08:00:00+08:00",
                                            "CrowdLevel": "m",
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                },
            )
        return httpx.Response(200, json={"value": []})

    app = make_app(handler)
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/transit/crowding/forecast",
            params={"train_line": "CCL"},
        )

    assert response.status_code == 200
    reading = response.json()["data"]["readings"][0]
    assert reading["line"] == "CCL"
    assert reading["station"] == "CE1"
    assert reading["station_name"] == "BAYFRONT MRT STATION"
    assert reading["level"] == "moderate"
    assert reading["start_time"] == "2026-09-12T08:00:00+08:00"
    assert reading["end_time"] == "2026-09-12T08:30:00+08:00"


def test_healthcare_wait_times_route_normalizes_official_pages() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/ttsh/ed-queue-status"):
            return httpx.Response(
                200,
                text=(
                    '<div class="s-edq-primary-card__block">'
                    "<span>Number of Patients waiting to be seen</span>"
                    "<span>2</span><span>Patients</span>"
                    "<span>No. of Patients Awaiting Consultation</span>"
                    "</div>"
                    '<div class="s-edq-primary-card__block">'
                    "<span>Waiting time to see doctor</span>"
                    "<span>10</span><span>mins</span>"
                    "<span>Average Consult Wait Time</span>"
                    "</div>"
                    '<p>Last updated at <span class="last_Updated_Date">31 Oct 2026</span>'
                    '<span class="last_Updated_Time">08:20 PM</span>. Refresh.</p>'
                ),
            )
        if request.url.path.endswith("/wh/for-patients-visitors/emergency-care"):
            return httpx.Response(
                200,
                text=(
                    "<p>Number of patients in queue 3 Patients</p>"
                    "<p>Waiting time to see doctor 8 mins</p>"
                    "<p>Last updated at 31 Oct 2026 08:15 PM. Refresh.</p>"
                ),
            )
        if request.url.path.endswith("/ktph/i-want-to/visit-a-e"):
            return httpx.Response(
                200,
                text=(
                    '<div class="s-edq-primary-card__block">'
                    "<span>Number of Patients waiting</span>"
                    "<span>8</span><span>Patients</span>"
                    "<span>No. of Patients Awaiting Consultation</span>"
                    "</div>"
                    '<div class="s-edq-primary-card__block">'
                    "<span>Waiting time to see doctor</span>"
                    "<span>41</span><span>mis</span>"
                    "<span>Average Consult Wait Time</span>"
                    "</div>"
                    '<p>last updated at <span id="last_Updated_Date">31 Oct 2026</span>'
                    '<span id="last_Updated_Time">08:18 PM</span>. Refresh.</p>'
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
                "<p>Last updated at 25 Oct 2026, 03:02:09 AM.</p>"
                "<p>The wait times shown are estimates and provided "
                "for informational purposes.</p>"
                "<p>1E Kent Ridge Road, NUHS Tower Block, Singapore 119228</p>"
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
        "Khoo Teck Puat Hospital",
        "Alexandra Hospital",
    }
    ttsh = next(
        facility
        for facility in facilities
        if facility["hospital"] == "Tan Tock Seng Hospital"
    )
    assert ttsh["patients_waiting"] == 2
    assert ttsh["wait_to_doctor"] == "10 mins"
    assert ttsh["wait_to_doctor_minutes"] == 10
    assert ttsh["source_url"].endswith("/ttsh/ed-queue-status")
    assert ttsh["updated_at"] == "31 Oct 2026 08:20 PM"
    woodlands = next(
        facility
        for facility in facilities
        if facility["hospital"] == "Woodlands Health"
    )
    assert woodlands["patients_waiting"] == 3
    assert woodlands["wait_to_doctor"] == "8 mins"
    assert woodlands["wait_to_doctor_minutes"] == 8
    assert woodlands["updated_at"] == "31 Oct 2026 08:15 PM"
    ktph = next(
        facility
        for facility in facilities
        if facility["hospital"] == "Khoo Teck Puat Hospital"
    )
    assert ktph["patients_waiting"] == 8
    assert ktph["wait_to_doctor"] == "41 mins"
    assert ktph["wait_to_doctor_minutes"] == 41
    assert ktph["updated_at"] == "31 Oct 2026 08:18 PM"
    nuhs = next(
        facility
        for facility in facilities
        if facility["hospital"] == "Alexandra Hospital"
    )
    assert nuhs["updated_at"] == "25 Oct 2026, 03:02:09 AM"


def test_nearby_view_uses_lta_datamall_not_onemap() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path.endswith("/BusStops"):
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "BusStopCode": "01012",
                            "RoadName": "Victoria St",
                            "Description": "Hotel Grand Pacific",
                            "Latitude": 1.29685,
                            "Longitude": 103.853,
                        }
                    ]
                },
            )
        if path.endswith("/TaxiStands"):
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "TaxiCode": "S0001",
                            "Latitude": 1.294,
                            "Longitude": 103.858,
                            "Name": "Bugis Junction",
                            "Type": "Stand",
                        }
                    ]
                },
            )
        if path.endswith("/CarParkAvailabilityv2"):
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "CarParkID": "A12",
                            "Development": "Suntec City",
                            "Location": "1.29375 103.85718",
                            "AvailableLots": 120,
                        }
                    ]
                },
            )
        if path.endswith("/v3/BicycleParking"):
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "Description": "Raffles City",
                            "Latitude": 1.2936,
                            "Longitude": 103.853,
                        }
                    ]
                },
            )
        if path.endswith("/EVCBatch"):
            return httpx.Response(
                200,
                json={"Link": "https://download.example/ev.json"},
            )
        if "/poll-download" in path:
            return httpx.Response(
                200,
                json={"data": {"url": "https://download.example/amenity.json"}},
            )
        if request.url.path.endswith("/ev.json"):
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "locationId": "EV1",
                            "name": "Suntec charger",
                            "latitude": 1.294,
                            "longtitude": 103.857,
                        }
                    ]
                },
            )
        if request.url.host == "download.example":
            return httpx.Response(
                200,
                json={"type": "FeatureCollection", "features": []},
            )
        return httpx.Response(200, json={"value": []})

    app = make_app(handler)
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/nearby",
            params={"latitude": 1.29375, "longitude": 103.85718, "radius": 800},
        )

    assert response.status_code == 200
    places = response.json()["data"]["places"]
    by_category = {place["category"] for place in places}
    names = {place["name"] for place in places}
    assert {
        "bus-stops",
        "taxi-stands",
        "carparks",
        "bicycle-parking",
        "ev-charging",
        "mrt-stations",
    } <= by_category
    assert {
        "Hotel Grand Pacific",
        "Bugis Junction",
        "Suntec City",
        "Raffles City",
        "Suntec charger",
        "CITY HALL MRT STATION",
    } <= names
    assert not any("getNearest" in item.url.path for item in requests)
    bicycle_request = next(
        item for item in requests if item.url.path.endswith("/v3/BicycleParking")
    )
    assert bicycle_request.url.params["Lat"] == "1.29375"
    assert bicycle_request.url.params["Long"] == "103.85718"
    assert float(bicycle_request.url.params["Dist"]) == 0.8
