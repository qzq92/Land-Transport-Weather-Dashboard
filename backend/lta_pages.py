"""LTA DataMall paging and batch-download helpers."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from backend.models import ApiResponse

CachedGet = Callable[..., Awaitable[ApiResponse]]


def secure_batch_link(payload: Any) -> str | None:
    """Return an HTTPS download link from an LTA batch listing payload."""
    if not isinstance(payload, dict):
        return None
    for key in ("Link", "link", "url"):
        value = payload.get(key)
        if isinstance(value, str) and value.startswith("https://"):
            return value
    items = payload.get("value")
    if isinstance(items, list) and len(items) == 1 and isinstance(items[0], dict):
        link = items[0].get("Link") or items[0].get("url")
        if isinstance(link, str) and link.startswith("https://"):
            return link
    nested = payload.get("data")
    return secure_batch_link(nested) if isinstance(nested, dict) else None


def _page_records(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    page = payload.get("value", [])
    if not isinstance(page, list):
        return []
    return [item for item in page if isinstance(item, dict)]


async def paged_lta_values(
    cached_get: CachedGet,
    headers: dict[str, str],
    namespace: str,
    url: str,
    *,
    ttl: int,
    max_skip: int,
    page_size: int = 50,
    extra_params: dict[str, Any] | None = None,
) -> ApiResponse:
    """Read LTA OData pages in parallel and return one combined value list."""

    async def fetch(skip: int) -> ApiResponse:
        params = {**(extra_params or {}), "$skip": skip}
        return await cached_get(
            namespace,
            url,
            params=params,
            headers=headers,
            ttl=ttl,
        )

    first = await fetch(0)
    records = _page_records(first.data)
    if not records:
        return first.model_copy(update={"data": {"value": []}})
    observed = len(records)
    if observed < page_size:
        return first.model_copy(update={"data": {"value": records}})

    last = first
    skip = observed
    while skip < max_skip:
        batch = [
            skip + observed * index
            for index in range(8)
            if skip + observed * index < max_skip
        ]
        pages = await asyncio.gather(*(fetch(item) for item in batch))
        finished = False
        for response in pages:
            last = response
            page = _page_records(response.data)
            if not page:
                finished = True
                break
            records.extend(page)
            if len(page) < page_size:
                finished = True
                break
        if finished:
            break
        skip = batch[-1] + observed
    return last.model_copy(update={"data": {"value": records}})
