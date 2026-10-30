import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useTransport } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { MapView } from "../components/MapView";
import { AlertList } from "../components/PageElements";
import { QueryState } from "../components/QueryState";

const MAP_LAYERS = [
  { category: "taxi", label: "Taxi" },
  { category: "camera", label: "Cameras" },
  { category: "incident", label: "Road alerts" },
  { category: "vms", label: "VMS" },
] as const;

export default function TransportPage() {
  const query = useTransport();
  const data = query.data?.data;
  const [activeLayers, setActiveLayers] = useState<Set<string>>(
    () => new Set(["camera", "incident"]),
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
      <div className="subnav" aria-label="Transport views">
        <NavLink to="/transport" end>Network</NavLink>
        <NavLink to="/transport/travel-times">Travel times</NavLink>
        <NavLink to="/transport/cameras">Cameras</NavLink>
      </div>
      <QueryState
        loading={query.isPending}
        error={query.error}
        fetching={query.isFetching}
        meta={query.data?.meta}
        onRetry={() => void query.refetch()}
      >
        {data && (
          <div className="transport-operations-layout">
            <aside className="transport-operations-rail">
              <DataPanel title="Network summary" eyebrow="Live counts">
                <div className="transport-metric-grid">
                  {(data.metrics ?? []).map((metric) => (
                    <article
                      className={`transport-metric-tile metric-${metric.status ?? "neutral"}`}
                      key={metric.id}
                    >
                      <span>{metric.label}</span>
                      <strong>
                        {metric.value}
                        {metric.unit && <small>{metric.unit}</small>}
                      </strong>
                    </article>
                  ))}
                </div>
              </DataPanel>
              <DataPanel title="Road advisories" eyebrow="Current incidents">
                <AlertList alerts={data.incidents ?? []} />
              </DataPanel>
              <DataPanel title="Rail advisories" eyebrow="MRT and LRT">
                <AlertList alerts={data.train_status ?? []} />
              </DataPanel>
            </aside>
            <DataPanel
              title="Road network map"
              eyebrow="Islandwide operations"
              className="transport-map-card"
            >
              <div className="transport-layer-chips" aria-label="Map layers">
                {MAP_LAYERS.map((layer) => {
                  const isActive = activeLayers.has(layer.category);
                  return (
                    <button
                      aria-pressed={isActive}
                      className={isActive ? "is-active" : ""}
                      key={layer.category}
                      onClick={() => toggleLayer(layer.category)}
                      type="button"
                    >
                      {layer.label}
                    </button>
                  );
                })}
              </div>
              <MapView
                points={(data.points ?? []).filter((point) =>
                  activeLayers.has(point.category ?? ""),
                )}
                height={610}
              />
            </DataPanel>
          </div>
        )}
      </QueryState>
    </>
  );
}
