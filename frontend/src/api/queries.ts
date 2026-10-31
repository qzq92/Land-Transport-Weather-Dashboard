import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type {
  ApiEnvelope,
  BusRouteData,
  BusStopLocations,
  BusesData,
  HealthcareData,
  NearbyData,
  SearchPlace,
} from "./schema";

const LIVE_QUERY_OPTIONS = {
  staleTime: 60_000,
  refetchInterval: 120_000,
  retry: 2,
} as const;

export const useDashboard = () =>
  useQuery({
    queryKey: ["dashboard"],
    queryFn: ({ signal }) => api.dashboard(signal),
    ...LIVE_QUERY_OPTIONS,
  });

export const useWeather = () =>
  useQuery({
    queryKey: ["weather", "realtime"],
    queryFn: ({ signal }) => api.weather(signal),
    ...LIVE_QUERY_OPTIONS,
  });

export const useEnvironment = () =>
  useQuery({
    queryKey: ["environment"],
    queryFn: ({ signal }) => api.environment(signal),
    staleTime: 5 * 60_000,
    retry: 2,
  });

export const useTransport = () =>
  useQuery({
    queryKey: ["transport"],
    queryFn: ({ signal }) => api.transport(signal),
    ...LIVE_QUERY_OPTIONS,
  });

export const useTravelTimes = () =>
  useQuery({
    queryKey: ["transport", "travel-times"],
    queryFn: ({ signal }) => api.travelTimes(signal),
    ...LIVE_QUERY_OPTIONS,
  });

export const useCameras = () =>
  useQuery({
    queryKey: ["transport", "cameras"],
    queryFn: ({ signal }) => api.cameras(signal),
    ...LIVE_QUERY_OPTIONS,
  });

export const useRailStatus = () =>
  useQuery({
    queryKey: ["transit", "rail", "banner"],
    queryFn: ({ signal }) => api.railStatus(signal),
    ...LIVE_QUERY_OPTIONS,
  });

export const useCrowding = () =>
  useQuery({
    queryKey: ["transit", "crowding"],
    queryFn: ({ signal }) => api.crowding(signal),
    ...LIVE_QUERY_OPTIONS,
  });

export function useBuses(stopCode: string) {
  return useQuery<ApiEnvelope<BusesData>>({
    queryKey: ["transit", "buses", stopCode],
    queryFn: ({ signal }) => api.buses({ stop_code: stopCode }, signal),
    enabled: Boolean(stopCode),
    staleTime: 30_000,
    retry: 1,
  });
}

export function useBusLocations(enabled: boolean) {
  return useQuery<ApiEnvelope<BusStopLocations>>({
    queryKey: ["transit", "bus-locations"],
    queryFn: ({ signal }) => api.busLocations(signal),
    enabled,
    staleTime: 24 * 60 * 60_000,
    retry: 1,
  });
}

export function useBusRoute(serviceNo: string) {
  return useQuery<ApiEnvelope<BusRouteData>>({
    queryKey: ["transit", "bus-route", serviceNo],
    queryFn: ({ signal }) => api.busRoute(serviceNo, signal),
    enabled: Boolean(serviceNo),
    staleTime: 24 * 60 * 60_000,
    retry: 1,
  });
}

export const useHealthcareWaitTimes = () =>
  useQuery<ApiEnvelope<HealthcareData>>({
    queryKey: ["healthcare", "wait-times"],
    queryFn: ({ signal }) => api.healthcareWaitTimes(signal),
    staleTime: 5 * 60_000,
    refetchInterval: 10 * 60_000,
    retry: 1,
  });

export function useNearby(latitude: number, longitude: number) {
  return useQuery<ApiEnvelope<NearbyData>>({
    queryKey: ["nearby", latitude, longitude],
    queryFn: ({ signal }) =>
      api.nearby({ latitude, longitude, radius: 2000 }, signal),
    staleTime: 5 * 60_000,
  });
}

export function usePlaceSearch(query: string) {
  return useQuery<ApiEnvelope<SearchPlace[]>>({
    queryKey: ["nearby", "search", query],
    queryFn: ({ signal }) => api.searchPlaces(query, signal),
    enabled: query.trim().length >= 3,
    staleTime: 10 * 60_000,
  });
}
