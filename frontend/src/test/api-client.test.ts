import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiGet } from "../api/client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("typed API client", () => {
  it("normalizes a raw successful response into an envelope", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ journeys: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiGet("/api/v1/transport/travel-times");

    expect(result.data).toEqual({ journeys: [] });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/transport/travel-times",
      expect.objectContaining({
        headers: { Accept: "application/json" },
      }),
    );
  });

  it("serializes defined query parameters", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ arrivals: [] }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await apiGet("/api/v1/transit/buses", {
      params: { stop_code: "83139", service_no: undefined },
    });

    expect(fetchMock.mock.calls[0][0]).toBe(
      "/api/v1/transit/buses?stop_code=83139",
    );
  });

  it("throws a structured error for non-success responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Service unavailable" }), {
          status: 503,
        }),
      ),
    );

    await expect(apiGet("/api/v1/dashboard")).rejects.toEqual(
      expect.objectContaining<ApiError>({
        name: "ApiError",
        message: "Service unavailable",
        status: 503,
      }),
    );
  });
});
