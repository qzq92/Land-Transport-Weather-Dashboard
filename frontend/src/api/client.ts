import type { ApiEnvelope, ApiPath, paths } from "./schema";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const DEFAULT_TIMEOUT_MS = 12_000;

export class ApiError extends Error {
  /** Creates a normalized error for an API or network failure. */
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
  /** Optional query parameters, cancellation signal, and request timeout. */
  params?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
  timeoutMs?: number;
}

/**
 * Builds an origin-relative or configured absolute API URL.
 * @param path - Typed API path to request.
 * @param params - Optional query parameters appended to the URL.
 */
function buildUrl(path: ApiPath, params?: RequestOptions["params"]): string {
  const url = new URL(`${API_BASE_URL}${path}`, window.location.origin);
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return API_BASE_URL ? url.toString() : `${url.pathname}${url.search}`;
}

/**
 * Detects whether a provider response already uses the API envelope shape.
 * @param value - Parsed JSON body from `fetch`.
 */
function isEnvelope<T>(value: unknown): value is ApiEnvelope<T> {
  return Boolean(value && typeof value === "object" && "data" in value);
}

/**
 * Fetches one typed API path with timeout and error normalization.
 * @param path - Versioned API path from the frontend schema map.
 * @param options - Optional query params, abort signal, and timeout.
 */
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

/** Typed endpoint methods used by the frontend query hooks. */
export const api = {
  /** Fetches the combined home-dashboard aggregate. */
  dashboard: (signal?: AbortSignal) =>
    apiGet("/api/v1/dashboard", { signal }),
  /** Fetches realtime weather metrics, readings, and alerts. */
  weather: (signal?: AbortSignal) =>
    apiGet("/api/v1/weather/realtime", { signal }),
  /** Fetches PSI, UV, WBGT, and disease-cluster environment data. */
  environment: (signal?: AbortSignal) =>
    apiGet("/api/v1/environment", { signal }),
  /** Fetches road transport metrics and map incidents. */
  transport: (signal?: AbortSignal) =>
    apiGet("/api/v1/transport", { signal }),
  /** Fetches expressway travel-time estimates. */
  travelTimes: (signal?: AbortSignal) =>
    apiGet("/api/v1/transport/travel-times", { signal }),
  /** Fetches traffic camera metadata and image URLs. */
  cameras: (signal?: AbortSignal) =>
    apiGet("/api/v1/transport/cameras", { signal }),
  /** Fetches realtime MRT/LRT crowding for one train-line code. */
  crowding: (trainLine?: string, signal?: AbortSignal) =>
    apiGet("/api/v1/transit/crowding", {
      params: { train_line: trainLine },
      signal,
    }),
  /** Fetches 24-hour MRT/LRT crowding forecasts for one train-line code. */
  crowdForecast: (trainLine?: string, signal?: AbortSignal) =>
    apiGet("/api/v1/transit/crowding/forecast", {
      params: { train_line: trainLine },
      signal,
    }),
  /** Fetches the global operational rail-status banner. */
  railStatus: (signal?: AbortSignal) =>
    apiGet("/api/v1/transit/rail/banner", { signal }),
  /** Fetches bus arrivals for one stop, optionally filtered by service. */
  buses: (
    params: { stop_code: string; service_no?: string },
    signal?: AbortSignal,
  ) =>
    apiGet("/api/v1/transit/buses", {
      params,
      signal,
      timeoutMs: 45_000,
    }),
  /** Fetches plottable coordinates for the bus-stop map layer. */
  busLocations: (signal?: AbortSignal) =>
    apiGet("/api/v1/transit/bus/locations", { signal, timeoutMs: 45_000 }),
  /** Fetches ordered route stops for one bus service number. */
  busRoute: (serviceNo: string, signal?: AbortSignal) =>
    apiGet("/api/v1/transit/bus/routes", {
      params: { service_no: serviceNo },
      signal,
      timeoutMs: 45_000,
    }),
  /** Fetches parsed emergency-department queue pages from hospitals. */
  healthcareWaitTimes: (signal?: AbortSignal) =>
    apiGet("/api/v1/healthcare/wait-times", {
      signal,
      timeoutMs: 20_000,
    }),
  /** Fetches LTA and amenity facilities within a search radius. */
  nearby: (
    params: { latitude: number; longitude: number; radius?: number },
    signal?: AbortSignal,
  ) => apiGet("/api/v1/nearby", { params, signal }),
  /** Searches OneMap for address suggestions. */
  searchPlaces: (query: string, signal?: AbortSignal) =>
    apiGet("/api/v1/nearby/search", { params: { q: query }, signal }),
};
