"""API behavior, health, CORS, and validation tests."""

import httpx
from backend.main import create_app
from backend.settings import Settings
from fastapi.testclient import TestClient


def build_client(
    handler,
) -> tuple[TestClient, object]:
    settings = Settings(
        _env_file=None,
        cors_origins=["https://dashboard.example"],
        lta_api_key="test-lta-key",
        cache_ttl_jitter_ratio=0,
        redis_url=None,
    )
    app = create_app(
        settings,
        http_transport=httpx.MockTransport(handler),
    )
    return TestClient(app), app


def test_health_and_lifespan_owned_http_client() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client, app = build_client(handler)
    with client:
        live = client.get("/api/v1/health/live")
        ready = client.get("/api/v1/health/ready")
        assert live.json()["status"] == "ok"
        assert ready.json()["status"] == "ok"
        assert ready.json()["components"]["redis"]["status"] == "disabled"
        assert app.state.http_client.is_closed is False

    assert app.state.http_client.is_closed is True


def test_cors_allows_only_the_configured_origin() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client, _app = build_client(handler)
    with client:
        allowed = client.options(
            "/api/v1/health/live",
            headers={
                "Origin": "https://dashboard.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        denied = client.get(
            "/api/v1/health/live",
            headers={"Origin": "https://untrusted.example"},
        )

    assert allowed.status_code == 200
    assert (
        allowed.headers["access-control-allow-origin"]
        == "https://dashboard.example"
    )
    assert "access-control-allow-origin" not in denied.headers


def test_strict_query_and_path_validation_prevents_provider_calls() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={})

    client, _app = build_client(handler)
    with client:
        invalid_code = client.get(
            "/api/v1/transit/bus/arrivals",
            params={"bus_stop_code": "1234"},
        )
        invalid_skip = client.get(
            "/api/v1/transit/bus/stops",
            params={"skip": "501"},
        )
        invalid_metric = client.get(
            "/api/v1/weather/realtime/temperature",
        )
        invalid_coordinates = client.get(
            "/api/v1/locations/nearby/bus-stops",
            params={"latitude": 91, "longitude": 103.8},
        )

    assert {
        invalid_code.status_code,
        invalid_skip.status_code,
        invalid_metric.status_code,
        invalid_coordinates.status_code,
    } == {422}
    assert calls == 0


def test_provider_error_is_safely_translated() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"secret": "provider details"})

    client, _app = build_client(handler)
    with client:
        response = client.get("/api/v1/transport/incidents")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Upstream provider returned HTTP 429"
    }
