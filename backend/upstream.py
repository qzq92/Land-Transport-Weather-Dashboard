"""Asynchronous HTTP access with consistent provider error handling."""

from typing import Any

import httpx


class UpstreamError(Exception):
    """Safe error raised when an external provider cannot serve a request."""

    def __init__(self, detail: str, status_code: int = 502) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class UpstreamClient:
    """Small wrapper around a lifespan-owned HTTP client."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """GET and decode a JSON response."""
        return await self._request_json(
            "GET",
            url,
            params=params,
            headers=headers,
        )

    async def get_text(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> str:
        """GET and return a successful response body as text."""
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            mapped_status = 503 if status in {408, 425, 429} or status >= 500 else 502
            raise UpstreamError(
                f"Upstream provider returned HTTP {status}",
                mapped_status,
            ) from error
        except httpx.TimeoutException as error:
            raise UpstreamError("Upstream provider timed out", 504) from error
        except httpx.RequestError as error:
            raise UpstreamError("Upstream provider is unavailable", 503) from error

    async def post_json(
        self,
        url: str,
        *,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> Any:
        """POST JSON and decode a JSON response."""
        return await self._request_json(
            "POST",
            url,
            json=payload,
            headers=headers,
        )

    async def _request_json(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Any:
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            mapped_status = 503 if status in {408, 425, 429} or status >= 500 else 502
            raise UpstreamError(
                f"Upstream provider returned HTTP {status}",
                mapped_status,
            ) from error
        except httpx.TimeoutException as error:
            raise UpstreamError("Upstream provider timed out", 504) from error
        except httpx.RequestError as error:
            raise UpstreamError("Upstream provider is unavailable", 503) from error
        except ValueError as error:
            raise UpstreamError(
                "Upstream provider returned invalid JSON",
                502,
            ) from error
