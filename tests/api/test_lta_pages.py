"""Tests for LTA DataMall paging and batch-link helpers."""

from datetime import UTC, datetime

import pytest
from backend.lta_pages import paged_lta_values, secure_batch_link
from backend.models import ApiResponse, CacheMetadata


def _response(records: list[dict[str, object]]) -> ApiResponse:
    return ApiResponse(
        data={"value": records},
        meta=CacheMetadata(
            state="bypass",
            key="k",
            fetched_at=datetime.now(UTC),
            age_seconds=0,
        ),
    )


def test_secure_batch_link_reads_single_value_link() -> None:
    assert (
        secure_batch_link({"value": [{"Link": "https://download.example/ev.json"}]})
        == "https://download.example/ev.json"
    )
    assert secure_batch_link({"value": [{"latitude": 1.29}]}) is None


@pytest.mark.asyncio
async def test_paged_lta_values_advances_skip_by_actual_page_length() -> None:
    calls: list[int] = []
    pages = {
        0: [{"id": index} for index in range(50)],
        50: [{"id": index} for index in range(50, 60)],
    }

    async def cached_get(
        _namespace: str,
        _url: str,
        *,
        params: dict[str, object],
        headers: dict[str, str],
        ttl: int,
    ) -> ApiResponse:
        _ = headers, ttl
        skip = int(params["$skip"])
        calls.append(skip)
        return _response(pages.get(skip, []))

    result = await paged_lta_values(
        cached_get,
        {"AccountKey": "x"},
        "transit:bus-stops",
        "https://example/BusStops",
        ttl=1,
        max_skip=5000,
    )

    assert [item["id"] for item in result.data["value"]] == list(range(60))
    assert calls[0] == 0
    assert 50 in calls
