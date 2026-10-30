import type { ApiEnvelope, ApiPath, paths } from "./schema";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const DEFAULT_TIMEOUT_MS = 12_000;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface RequestOptions {
  params?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
  timeoutMs?: number;
}

function buildUrl(path: ApiPath, params?: RequestOptions["params"]): string {
  const url = new URL(`${API_BASE_URL}${path}`, window.location.origin);
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return API_BASE_URL ? url.toString() : `${url.pathname}${url.search}`;
}

function isEnvelope<T>(value: unknown): value is ApiEnvelope<T> {
  return Boolean(value && typeof value === "object" && "data" in value);
}

export async function apiGet<P extends ApiPath>(
  path: P,
  options: RequestOptions = {},
): Promise<ApiEnvelope<paths[P]>> {
  const timeoutController = new AbortController();
  const timer = window.setTimeout(
    () => timeoutController.abort(),
    options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
  );
  const abortFromParent = () => timeoutController.abort(options.signal?.reason);
  if (options.signal?.aborted) abortFromParent();
  else options.signal?.addEventListener("abort", abortFromParent, { once: true });

  try {
    const response = await fetch(buildUrl(path, options.params), {
      headers: { Accept: "application/json" },
      signal: timeoutController.signal,
    });
    const body: unknown = await response.json().catch(() => undefined);
    if (!response.ok) {
      const detail =
        body && typeof body === "object" && "detail" in body
          ? String(body.detail)
          : `Request failed with status ${response.status}`;
      throw new ApiError(detail, response.status, body);
    }
    return isEnvelope<paths[P]>(body)
      ? body
      : { data: body as paths[P] };
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The request timed out. Please try again.", 408);
    }
    throw new ApiError("Unable to reach the dashboard API.", 0, error);
  } finally {
    window.clearTimeout(timer);
    options.signal?.removeEventListener("abort", abortFromParent);
  }
}

export const api = {
  dashboard: (signal?: AbortSignal) =>
    apiGet("/api/v1/dashboard", { signal }),
  weather: (signal?: AbortSignal) =>
    apiGet("/api/v1/weather/realtime", { signal }),
  environment: (signal?: AbortSignal) =>
    apiGet("/api/v1/environment", { signal }),
  transport: (signal?: AbortSignal) =>
    apiGet("/api/v1/transport", { signal }),
  travelTimes: (signal?: AbortSignal) =>
    apiGet("/api/v1/transport/travel-times", { signal }),
  cameras: (signal?: AbortSignal) =>
    apiGet("/api/v1/transport/cameras", { signal }),
  crowding: (signal?: AbortSignal) =>
    apiGet("/api/v1/transit/crowding", { signal }),
  railStatus: (signal?: AbortSignal) =>
    apiGet("/api/v1/transit/rail/banner", { signal }),
  buses: (
    params: { stop_code: string; service_no?: string },
    signal?: AbortSignal,
  ) =>
    apiGet("/api/v1/transit/buses", {
      params,
      signal,
      timeoutMs: 45_000,
    }),
  busLocations: (signal?: AbortSignal) =>
    apiGet("/api/v1/transit/bus/locations", { signal, timeoutMs: 45_000 }),
  busRoute: (serviceNo: string, signal?: AbortSignal) =>
    apiGet("/api/v1/transit/bus/routes", {
      params: { service_no: serviceNo },
      signal,
      timeoutMs: 45_000,
    }),
  nearby: (
    params: { latitude: number; longitude: number; radius?: number },
    signal?: AbortSignal,
  ) => apiGet("/api/v1/nearby", { params, signal }),
  searchPlaces: (query: string, signal?: AbortSignal) =>
    apiGet("/api/v1/nearby/search", { params: { q: query }, signal }),
};
