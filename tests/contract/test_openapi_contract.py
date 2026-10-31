"""Public API contract tests."""

import pytest
from pydantic import ValidationError

from backend.main import create_app
from backend.settings import Settings


def test_openapi_exposes_required_versioned_operations() -> None:
    settings = Settings(_env_file=None)
    schema = create_app(settings).openapi()
    paths = schema["paths"]
    required = {
        "/api/v1/health/live",
        "/api/v1/health/ready",
        "/api/v1/locations/search",
        "/api/v1/locations/nearby/{kind}",
        "/api/v1/weather/realtime/{metric}",
        "/api/v1/weather/forecasts/{period}",
        "/api/v1/environment/indices/{metric}",
        "/api/v1/environment/clusters/{disease}",
        "/api/v1/healthcare/wait-times",
        "/api/v1/transport/{resource}",
        "/api/v1/transport/ev/chargers",
        "/api/v1/transit/bus/stops",
        "/api/v1/transit/bus/arrivals",
        "/api/v1/transit/bus/services",
        "/api/v1/transit/rail/{resource}",
        "/api/v1/dashboard",
    }

    assert required <= set(paths)
    assert schema["components"]["schemas"]["ApiResponse"][
        "additionalProperties"
    ] is False
    assert schema["components"]["schemas"]["CacheMetadata"][
        "additionalProperties"
    ] is False


def test_cors_configuration_rejects_wildcards() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_origins=["*"])
