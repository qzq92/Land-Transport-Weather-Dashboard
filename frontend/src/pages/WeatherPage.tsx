import { useState } from "react";
import { useWeather } from "../api/queries";
import { MapView } from "../components/MapView";
import { QueryState } from "../components/QueryState";
import type { Metric } from "../api/schema";

const WEATHER_LAYERS = [
  {
    id: "air-temperature",
    label: "Temperature averaged across sensors",
    toggle: "Show temperature sensor locations",
  },
  {
    id: "rainfall",
    label: "Rainfall averaged across sensors",
    toggle: "Show rainfall sensor locations",
  },
  {
    id: "relative-humidity",
    label: "Humidity",
    toggle: "Show humidity sensor locations",
  },
  {
    id: "wind-speed",
    label: "Wind Speed averaged across sensors",
    toggle: "Show wind speed sensor locations",
  },
  {
    id: "lightning",
    label: "Lightning observations in last 5 minutes",
    toggle: "Show lightning sensor locations",
  },
  {
    id: "flood",
    label: "Flood Alerts",
    toggle: "Show flood sensor locations",
  },
  {
    id: "wbgt",
    label: "WBGT (Heat Stress) average across sensors",
    toggle: "Show WBGT sensor locations",
  },
] as const;

/** Looks up one weather metric summary for the current layer card. */
function metricText(metrics: Metric[], id: string): string {
  const metric = metrics.find((item) => item.id === id);
  if (!metric || metric.value === "" || metric.value === undefined) return "—";
  if (id === "flood" && (metric.value === 0 || metric.value === "0")) {
    return "No alerts";
  }
  return metric.unit ? `${metric.value} ${metric.unit}` : String(metric.value);
}

/** Realtime weather metrics, sensor map layers, and alert summaries. */
export default function WeatherPage() {
  const query = useWeather();
  const data = query.data?.data;
  const [activeLayers, setActiveLayers] = useState<Set<string>>(() => new Set());

  const toggleLayer = (metric: string) => {
    setActiveLayers((current) => {
      const next = new Set(current);
      if (next.has(metric)) next.delete(metric);
      else next.add(metric);
      return next;
    });
  };

  const mapPoints = (data?.readings ?? [])
    .filter((reading) => activeLayers.has(reading.metric))
    .map((reading) => ({
      ...reading,
      category: reading.metric,
      value: `${reading.value ?? "—"} ${reading.unit}`.trim(),
    }));

  return (
    <QueryState
      loading={query.isPending}
      error={query.error}
      fetching={query.isFetching}
      meta={query.data?.meta}
      onRetry={() => void query.refetch()}
    >
      {data && (
          <div className="weather-operations-layout">
            <ul className="weather-metric-list" aria-label="Weather metrics">
              {WEATHER_LAYERS.map((layer) => (
                <li className={`layer-${layer.id}`} key={layer.id}>
                  <span aria-hidden="true" />
                  <p>{layer.label}</p>
                  <b>{metricText(data.metrics ?? [], layer.id)}</b>
                </li>
              ))}
            </ul>
            <section className="weather-map-panel" aria-label="Sensor map">
              <div className="dashboard-map-controls weather-layer-controls">
                {WEATHER_LAYERS.map((layer) => {
                  const isActive = activeLayers.has(layer.id);
                  return (
                    <button
                      aria-pressed={isActive}
                      className={`layer-${layer.id}${isActive ? " is-active" : ""}`}
                      key={layer.id}
                      onClick={() => toggleLayer(layer.id)}
                      type="button"
                    >
                      {layer.toggle}
                    </button>
                  );
                })}
              </div>
              <MapView
                points={mapPoints}
                height={640}
                ariaLabel="Singapore weather sensor map"
              />
            </section>
          </div>
      )}
    </QueryState>
  );
}
