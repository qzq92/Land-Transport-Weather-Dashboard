/**
 * API contract types. This file mirrors the planned OpenAPI surface and is
 * intentionally shaped like generated output so it can later be replaced by
 * an OpenAPI generator without changing page imports.
 */

export interface ApiMeta {
  state?: "hit" | "miss" | "bypass" | "degraded" | "stale-if-error" | "stale-while-locked";
  key?: string;
  fetched_at?: string;
  age_seconds?: number;
  stale?: boolean;
  redis_degraded?: boolean;
}

export interface ApiEnvelope<T> {
  data: T;
  meta?: ApiMeta;
  errors?: Record<string, string>;
  generated_at?: string;
}

export interface Metric {
  id: string;
  label: string;
  value: string | number;
  unit?: string;
  trend?: number;
  status?: "good" | "warning" | "critical" | "neutral";
}

export interface GeoPoint {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  category?: string;
  value?: string | number;
  detail?: string;
}

export interface Alert {
  id: string;
  title: string;
  detail?: string;
  severity?: "info" | "warning" | "critical";
  updated_at?: string;
}

export interface RailStatus {
  state: "normal" | "disrupted" | "unknown";
  summary: string;
  detail?: string;
  updated_at?: string;
}

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
  series?: string;
}

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

export interface WeatherReading extends GeoPoint {
  metric: string;
  unit: string;
  observed_at?: string;
}

export interface WeatherData {
  metrics: Metric[];
  readings: WeatherReading[];
  alerts: Alert[];
}

export interface EnvironmentRegion extends GeoPoint {
  psi?: number;
  pollutant?: string;
}

export interface HealthCluster {
  id: string;
  disease: "dengue" | "zika";
  location: string;
  cases?: number;
}

export interface EnvironmentData {
  metrics: Metric[];
  regions: EnvironmentRegion[];
  uv_index: TimeSeriesPoint[];
  clusters: HealthCluster[];
}

export interface TransportData {
  metrics: Metric[];
  points: GeoPoint[];
  incidents: Alert[];
  train_status: Alert[];
}

export interface TravelTime {
  id: string;
  expressway: string;
  direction: string;
  start: string;
  end: string;
  minutes: number;
  distance_km?: number;
}

export interface TravelTimesData {
  journeys: TravelTime[];
  updated_at?: string;
}

export interface TrafficCamera extends GeoPoint {
  image_url: string;
  captured_at?: string;
}

export interface CamerasData {
  cameras: TrafficCamera[];
}

export interface CrowdReading {
  id: string;
  station: string;
  line: string;
  level: "low" | "moderate" | "high" | "unknown";
  start_time?: string;
  end_time?: string;
}

export interface CrowdingData {
  readings: CrowdReading[];
  updated_at?: string;
}

export interface BusVisit {
  minutes: number | null;
  load?: "seats" | "standing" | "limited" | "unknown";
  wheelchair?: boolean;
  type?: string;
}

export interface BusArrival {
  service_no: string;
  destination?: string;
  visits: BusVisit[];
}

export interface BusStop {
  code: string;
  name: string;
  road?: string;
  latitude?: number;
  longitude?: number;
}

export interface BusesData {
  stop?: BusStop;
  arrivals: BusArrival[];
}

export interface BusStopLocations {
  stops: BusStop[];
}

export interface BusRouteStop {
  code: string;
  name: string;
  sequence: number;
  latitude?: number | null;
  longitude?: number | null;
}

export interface BusRouteDirection {
  direction: string;
  origin?: string;
  destination?: string;
  first_bus?: string;
  last_bus?: string;
  stops: BusRouteStop[];
}

export interface BusRouteData {
  service_no: string;
  directions: BusRouteDirection[];
}

export interface NearbyPlace extends GeoPoint {
  distance_m: number;
  address?: string;
}

export interface NearbyData {
  centre: { latitude: number; longitude: number };
  places: NearbyPlace[];
}

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
}

export interface HealthcareSource {
  id: string;
  name: string;
  url: string;
  state: "available" | "unavailable";
  error?: string;
}

export interface HealthcareData {
  facilities: HealthcareFacility[];
  sources: HealthcareSource[];
}

export interface SearchPlace {
  id: string;
  label: string;
  latitude: number;
  longitude: number;
}

export interface paths {
  "/api/v1/dashboard": DashboardData;
  "/api/v1/weather/realtime": WeatherData;
  "/api/v1/environment": EnvironmentData;
  "/api/v1/transport": TransportData;
  "/api/v1/transport/travel-times": TravelTimesData;
  "/api/v1/transport/cameras": CamerasData;
  "/api/v1/transit/crowding": CrowdingData;
  "/api/v1/transit/rail/banner": RailStatus;
  "/api/v1/transit/buses": BusesData;
  "/api/v1/transit/bus/locations": BusStopLocations;
  "/api/v1/transit/bus/routes": BusRouteData;
  "/api/v1/healthcare/wait-times": HealthcareData;
  "/api/v1/nearby": NearbyData;
  "/api/v1/nearby/search": SearchPlace[];
}

export type ApiPath = keyof paths;
