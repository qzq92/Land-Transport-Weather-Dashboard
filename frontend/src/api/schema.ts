/**
 * API contract types. This file mirrors the planned OpenAPI surface and is
 * intentionally shaped like generated output so it can later be replaced by
 * an OpenAPI generator without changing page imports.
 */

/** Describes cache state and fetch timing for an API response. */
export interface ApiMeta {
  state?: "hit" | "miss" | "bypass" | "degraded" | "stale-if-error" | "stale-while-locked";
  key?: string;
  fetched_at?: string;
  age_seconds?: number;
  stale?: boolean;
  redis_degraded?: boolean;
}

/** Wraps a typed API payload with cache metadata and partial errors. */
export interface ApiEnvelope<T> {
  data: T;
  meta?: ApiMeta;
  errors?: Record<string, string>;
  generated_at?: string;
}

/** A dashboard metric card value and optional health state. */
export interface Metric {
  id: string;
  label: string;
  value: string | number;
  unit?: string;
  trend?: number;
  status?: "good" | "warning" | "critical" | "neutral";
}

/** A named geographic point rendered on a map. */
export interface GeoPoint {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  category?: string;
  value?: string | number;
  detail?: string;
}

/** A user-visible operational or environmental alert. */
export interface Alert {
  id: string;
  title: string;
  detail?: string;
  severity?: "info" | "warning" | "critical";
  updated_at?: string;
}

/** Aggregate rail-network status shown in the navigation banner. */
export interface RailStatus {
  state: "normal" | "disrupted" | "unknown";
  summary: string;
  detail?: string;
  updated_at?: string;
}

/** A timestamped numeric value used by charts. */
export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
  series?: string;
}

/** Data returned by the dashboard aggregation endpoint. */
export interface DashboardData {
  metrics: Metric[];
  alerts: Alert[];
  map_points: GeoPoint[];
  checkpoint_cameras: TrafficCamera[];
  rail_status: RailStatus;
  operations: {
    flood_alerts: number;
    lightning_observations: number;
    forecast: Record<string, unknown>;
    traffic: Record<string, number>;
    clusters: HealthCluster[];
  };
}

/** A weather observation associated with a map location. */
export interface WeatherReading extends GeoPoint {
  metric: string;
  unit: string;
  observed_at?: string;
}

/** Realtime weather metrics, readings, and alerts. */
export interface WeatherData {
  metrics: Metric[];
  readings: WeatherReading[];
  alerts: Alert[];
}

/** A regional PSI or pollutant reading. */
export interface EnvironmentRegion extends GeoPoint {
  psi?: number;
  pollutant?: string;
}

/** A dengue or Zika cluster and its optional map coordinates. */
export interface HealthCluster {
  id: string;
  disease: "dengue" | "zika";
  location: string;
  cases?: number;
  latitude?: number;
  longitude?: number;
}

/** Environmental indices, UV series, and disease clusters. */
export interface EnvironmentData {
  metrics: Metric[];
  regions: EnvironmentRegion[];
  uv_index: TimeSeriesPoint[];
  clusters: HealthCluster[];
}

/** Road transport metrics, map points, and train notices. */
export interface TransportData {
  metrics: Metric[];
  points: GeoPoint[];
  incidents: Alert[];
  train_status: Alert[];
}

/** An estimated journey time for an expressway segment. */
export interface TravelTime {
  id: string;
  expressway: string;
  direction: string;
  start: string;
  end: string;
  minutes: number;
  distance_km?: number;
}

/** Expressway journey estimates returned by the transport endpoint. */
export interface TravelTimesData {
  journeys: TravelTime[];
  updated_at?: string;
}

/** A traffic camera image and its capture time. */
export interface TrafficCamera extends GeoPoint {
  image_url: string;
  captured_at?: string;
}

/** Traffic camera records. */
export interface CamerasData {
  cameras: TrafficCamera[];
}

/** A station crowd-level observation for a time interval. */
export interface CrowdReading {
  id: string;
  station: string;
  station_name?: string;
  line: string;
  level: "low" | "moderate" | "high" | "unknown";
  start_time?: string;
  end_time?: string;
}

/** Station crowd observations returned by the selected train-line query. */
export interface CrowdingData {
  readings: CrowdReading[];
  updated_at?: string;
}

/** One predicted bus arrival visit and passenger-load status. */
export interface BusVisit {
  minutes: number | null;
  load?: "seats" | "standing" | "limited" | "unknown";
  wheelchair?: boolean;
  type?: string;
}

/** Arrivals grouped by bus service number. */
export interface BusArrival {
  service_no: string;
  destination?: string;
  visits: BusVisit[];
}

/** A bus stop and its optional location metadata. */
export interface BusStop {
  code: string;
  name: string;
  road?: string;
  latitude?: number;
  longitude?: number;
}

/** Bus stop details and grouped arrival predictions. */
export interface BusesData {
  stop?: BusStop;
  arrivals: BusArrival[];
}

/** Bus stop locations used by the optional map layer. */
export interface BusStopLocations {
  stops: BusStop[];
}

/** One stop in a bus route direction. */
export interface BusRouteStop {
  code: string;
  name: string;
  sequence: number;
  latitude?: number | null;
  longitude?: number | null;
}

/** A directional bus route with ordered stops and operating hours. */
export interface BusRouteDirection {
  direction: string;
  origin?: string;
  destination?: string;
  first_bus?: string;
  last_bus?: string;
  stops: BusRouteStop[];
}

/** Route directions returned for a bus service. */
export interface BusRouteData {
  service_no: string;
  directions: BusRouteDirection[];
}

/** A nearby facility with distance and optional bus-stop arrival details. */
export interface NearbyPlace extends GeoPoint {
  distance_m: number;
  address?: string;
  arrivals?: BusArrival[];
}

/** Nearby facilities and bus arrivals grouped around the selected map centre. */
export interface NearbyData {
  centre: { latitude: number; longitude: number };
  places: NearbyPlace[];
}

/** Emergency-department queue information for one hospital category. */
export interface HealthcareFacility {
  id: string;
  hospital: string;
  cluster: "NHG" | "NUHS";
  category: "adult" | "children";
  patients_waiting?: number | null;
  wait_to_doctor?: string | null;
  wait_to_doctor_minutes?: number | null;
  bed_wait?: string | null;
  bed_wait_minutes?: number | null;
  updated_at?: string | null;
  source_url?: string;
}

/** Availability and source metadata for a hospital wait-time page. */
export interface HealthcareSource {
  id: string;
  name: string;
  url: string;
  state: "available" | "unavailable";
  error?: string;
}

/** Hospital facilities and their official source-page statuses. */
export interface HealthcareData {
  facilities: HealthcareFacility[];
  sources: HealthcareSource[];
}

/** An address result returned by the OneMap search endpoint. */
export interface SearchPlace {
  id: string;
  label: string;
  latitude: number;
  longitude: number;
}

/** Maps versioned API paths to their response payload types. */
export interface paths {
  "/api/v1/dashboard": DashboardData;
  "/api/v1/weather/realtime": WeatherData;
  "/api/v1/environment": EnvironmentData;
  "/api/v1/transport": TransportData;
  "/api/v1/transport/travel-times": TravelTimesData;
  "/api/v1/transport/cameras": CamerasData;
  "/api/v1/transit/crowding": CrowdingData;
  "/api/v1/transit/crowding/forecast": CrowdingData;
  "/api/v1/transit/rail/banner": RailStatus;
  "/api/v1/transit/buses": BusesData;
  "/api/v1/transit/bus/locations": BusStopLocations;
  "/api/v1/transit/bus/routes": BusRouteData;
  "/api/v1/healthcare/wait-times": HealthcareData;
  "/api/v1/nearby": NearbyData;
  "/api/v1/nearby/search": SearchPlace[];
}

/** A valid path accepted by the typed API client. */
export type ApiPath = keyof paths;
