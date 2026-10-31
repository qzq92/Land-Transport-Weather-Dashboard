import { useState } from "react";
import { useDashboard } from "../api/queries";
import { CheckpointCameraFeeds } from "../components/CheckpointCameraFeeds";
import { DataPanel } from "../components/DataPanel";
import { MapView } from "../components/MapView";
import { QueryState } from "../components/QueryState";

const MAP_LAYERS = [
  { category: "camera", label: "Cameras" },
  { category: "taxi", label: "Taxis" },
  { category: "incident", label: "Road alerts" },
  { category: "vms", label: "Message signs" },
] as const;

function forecastRange(value: unknown, suffix = ""): string {
  if (!value || typeof value !== "object") return "—";
  const record = value as Record<string, unknown>;
  const low = record.low;
  const high = record.high;
  return low !== undefined && high !== undefined
    ? `${low}–${high}${suffix}`
    : "—";
}

export default function HomePage() {
  const query = useDashboard();
  const data = query.data?.data;
  const [activeLayers, setActiveLayers] = useState<Set<string>>(
    () => new Set(),
  );
  const mapPoints = (data?.map_points ?? []).filter((point) =>
    activeLayers.has(point.category ?? ""),
  );

  const toggleLayer = (category: string) => {
    setActiveLayers((current) => {
      const next = new Set(current);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  };

  return (
    <>
      <QueryState
        loading={query.isPending}
        error={query.error}
        fetching={query.isFetching}
        meta={query.data?.meta}
        onRetry={() => void query.refetch()}
      >
        {data && (
            <div className="dashboard-main-grid">
                <DataPanel
                  title="Land Checkpoints Traffic"
                  eyebrow="Live CCTV"
                  className="dashboard-checkpoint-panel"
                >
                  <CheckpointCameraFeeds
                    cameras={data.checkpoint_cameras ?? []}
                  />
                </DataPanel>
                <DataPanel title="Conditions across Singapore" eyebrow="Live map">
                  <div className="dashboard-map-controls" aria-label="Map layers">
                    {MAP_LAYERS.map((layer) => {
                      const isActive = activeLayers.has(layer.category);
                      return (
                        <button
                          aria-pressed={isActive}
                          className={`layer-${layer.category}${isActive ? " is-active" : ""}`}
                          key={layer.category}
                          onClick={() => toggleLayer(layer.category)}
                          type="button"
                        >
                          {layer.label}
                        </button>
                      );
                    })}
                  </div>
                  <MapView points={mapPoints} height={586} />
                </DataPanel>
                <aside className="dashboard-right-rail">
                  <DataPanel title="Live conditions" eyebrow="Weather and environment">
                    <ul className="operations-list">
                      <li><span>Latest flood alerts</span><b>{data.operations.flood_alerts}</b></li>
                      <li><span>Lightning observations (5 min)</span><b>{data.operations.lightning_observations}</b></li>
                      <li>
                        <span>Average 24-hour PSI</span>
                        <b>{data.metrics.find((metric) => metric.id === "psi")?.value ?? "—"}</b>
                      </li>
                    </ul>
                  </DataPanel>
                  <DataPanel title="Next 24-hour forecast" eyebrow="Singapore">
                    <ul className="operations-list">
                      <li><span>Temperature</span><b>{forecastRange(data.operations.forecast.temperature, "°C")}</b></li>
                      <li><span>Humidity</span><b>{forecastRange(data.operations.forecast.relativeHumidity, "%")}</b></li>
                      <li><span>Wind</span><b>{forecastRange((data.operations.forecast.wind as Record<string, unknown> | undefined)?.speed, " km/h")}</b></li>
                      <li><span>Rain forecast</span><b>{((data.operations.forecast.forecast as Record<string, unknown> | undefined)?.text as string | undefined) ?? "—"}</b></li>
                    </ul>
                  </DataPanel>
                  <DataPanel title="Traffic incidents and traffic lights" eyebrow="Live counts">
                    <ul className="operations-list">
                      {Object.entries(data.operations.traffic).map(([category, count]) => (
                        <li key={category}><span>{category}</span><b>{count}</b></li>
                      ))}
                    </ul>
                  </DataPanel>
                  <DataPanel title="Active disease clusters" eyebrow="Dengue and Zika">
                    <ul className="operations-list">
                      <li><span>Dengue</span><b>{data.operations.clusters.filter((cluster) => cluster.disease === "dengue").length}</b></li>
                      <li><span>Zika</span><b>{data.operations.clusters.filter((cluster) => cluster.disease === "zika").length}</b></li>
                    </ul>
                  </DataPanel>
                </aside>
            </div>
        )}
      </QueryState>
    </>
  );
}
