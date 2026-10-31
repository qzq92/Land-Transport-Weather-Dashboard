import { useMemo, useState } from "react";
import { useEnvironment } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { MapView } from "../components/MapView";
import { MetricGrid } from "../components/PageElements";
import { QueryState } from "../components/QueryState";
import { TimeSeriesChart } from "../components/TimeSeriesChart";

export default function EnvironmentPage() {
  const query = useEnvironment();
  const data = query.data?.data;
  const [showPsiLocations, setShowPsiLocations] = useState(true);
  const [showZikaClusters, setShowZikaClusters] = useState(false);
  const [showDengueClusters, setShowDengueClusters] = useState(false);
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);
  const mapPoints = useMemo(
    () => [
      ...(showPsiLocations
        ? (data?.regions ?? []).map((region) => ({
            ...region,
            category: "psi",
            value: region.psi,
            detail: region.pollutant,
          }))
        : []),
      ...(!showZikaClusters
        ? []
        : (data?.clusters ?? [])
            .filter(
              (cluster) =>
                cluster.disease === "zika"
                && cluster.latitude !== undefined
                && cluster.longitude !== undefined,
            )
            .map((cluster) => ({
              id: cluster.id,
              name: cluster.location,
              latitude: cluster.latitude as number,
              longitude: cluster.longitude as number,
              category: "zika",
              value: cluster.cases,
              detail: "Zika cluster",
            }))),
      ...(!showDengueClusters
        ? []
        : (data?.clusters ?? [])
            .filter(
              (cluster) =>
                cluster.disease === "dengue"
                && cluster.latitude !== undefined
                && cluster.longitude !== undefined,
            )
            .map((cluster) => ({
              id: cluster.id,
              name: cluster.location,
              latitude: cluster.latitude as number,
              longitude: cluster.longitude as number,
              category: "dengue",
              value: cluster.cases,
              detail: "Dengue cluster",
            }))),
    ],
    [
      data?.clusters,
      data?.regions,
      showDengueClusters,
      showPsiLocations,
      showZikaClusters,
    ],
  );
  const selectedCluster = (data?.clusters ?? []).find(
    (cluster) =>
      cluster.id === selectedClusterId
      && cluster.latitude !== undefined
      && cluster.longitude !== undefined,
  );

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
          <div
            className="environment-operations-layout"
          >
            <aside className="environment-left-rail">
              <DataPanel title="UV index through the day" eyebrow="Exposure">
                <TimeSeriesChart
                  points={data.uv_index ?? []}
                  title="UV index"
                  unit=" index"
                />
              </DataPanel>
              {(["zika", "dengue"] as const).map((disease) => {
                const clusters = (data.clusters ?? []).filter(
                  (cluster) => cluster.disease === disease,
                );
                return (
                  <DataPanel
                    key={disease}
                    title={`${disease[0].toUpperCase()}${disease.slice(1)} clusters`}
                    eyebrow={`${clusters.length} active areas`}
                  >
                    {clusters.length ? (
                      <ul className="cluster-list">
                        {clusters.map((cluster) => (
                          <li key={cluster.id}>
                            <button
                              className="cluster-list-item"
                              disabled={
                                cluster.latitude === undefined
                                || cluster.longitude === undefined
                              }
                              onClick={() => {
                                setSelectedClusterId(cluster.id);
                                if (cluster.disease === "zika") {
                                  setShowZikaClusters(true);
                                } else {
                                  setShowDengueClusters(true);
                                }
                              }}
                              type="button"
                            >
                              <span>{cluster.location}</span>
                              {cluster.cases !== undefined && (
                                <b>{cluster.cases} cases</b>
                              )}
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="environment-empty">No active clusters reported.</p>
                    )}
                  </DataPanel>
                );
              })}
            </aside>
            <DataPanel title="Regional PSI" eyebrow="Air quality">
                <div className="dashboard-map-controls" aria-label="Environment layers">
                  <button
                    aria-pressed={showPsiLocations}
                    className={`layer-psi${showPsiLocations ? " is-active" : ""}`}
                    onClick={() => setShowPsiLocations((visible) => !visible)}
                    type="button"
                  >
                    {showPsiLocations ? "Hide PSI locations" : "Show PSI locations"}
                  </button>
                  <button
                    aria-pressed={showZikaClusters}
                    className={`layer-zika${showZikaClusters ? " is-active" : ""}`}
                    onClick={() => setShowZikaClusters((visible) => !visible)}
                    type="button"
                  >
                    Show Zika clusters
                  </button>
                  <button
                    aria-pressed={showDengueClusters}
                    className={`layer-dengue${showDengueClusters ? " is-active" : ""}`}
                    onClick={() => setShowDengueClusters((visible) => !visible)}
                    type="button"
                  >
                    Show Dengue clusters
                  </button>
                </div>
                <MapView
                  centre={
                    selectedCluster?.latitude !== undefined
                    && selectedCluster.longitude !== undefined
                      ? [selectedCluster.latitude, selectedCluster.longitude]
                      : undefined
                  }
                  onSelect={(point) => {
                    if (point.category === "zika" || point.category === "dengue") {
                      setSelectedClusterId(point.id);
                    }
                  }}
                  points={mapPoints}
                  height={586}
                  zoom={selectedCluster ? 15 : 13}
                />
            </DataPanel>
            <aside className="environment-right-rail">
              <DataPanel title="Air quality (PSI)" eyebrow="Current status">
                <div className="environment-metric-grid">
                  <MetricGrid metrics={data.metrics ?? []} />
                </div>
                <dl className="psi-legend">
                  <div><dt>Good</dt><dd>0–50</dd></div>
                  <div><dt>Moderate</dt><dd>51–100</dd></div>
                  <div><dt>Unhealthy</dt><dd>101–200</dd></div>
                  <div><dt>Very unhealthy</dt><dd>201–300</dd></div>
                  <div><dt>Hazardous</dt><dd>301+</dd></div>
                </dl>
                <section className="air-quality-explainer">
                  <h3>How are these colours decided?</h3>
                  <p>
                    Each pollutant uses its own health band. The highest
                    sub-index determines the regional PSI colour.
                  </p>
                  <a
                    className="air-quality-source"
                    href="https://www.nea.gov.sg/our-services/pollution-control/air-pollution/psi"
                    rel="noreferrer"
                    target="_blank"
                  >
                    Source: National Environment Agency (NEA) PSI guidance
                  </a>
                  <div className="table-scroll">
                    <table>
                      <caption className="sr-only">
                        Air-quality pollutant health bands
                      </caption>
                      <thead>
                        <tr>
                          <th scope="col">Pollutant</th>
                          <th className="psi-band-good" scope="col">Good</th>
                          <th className="psi-band-moderate" scope="col">Moderate</th>
                          <th className="psi-band-unhealthy" scope="col">Unhealthy</th>
                          <th className="psi-band-very-unhealthy" scope="col">Very unhealthy</th>
                          <th className="psi-band-hazardous" scope="col">Hazardous</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <th scope="row">PM2.5 (µg/m³)</th>
                          <td className="psi-band-good">0–12</td>
                          <td className="psi-band-moderate">13–55</td>
                          <td className="psi-band-unhealthy">56–150</td>
                          <td className="psi-band-very-unhealthy">151–250</td>
                          <td className="psi-band-hazardous">251+</td>
                        </tr>
                        <tr>
                          <th scope="row">PM10 (µg/m³)</th>
                          <td className="psi-band-good">0–54</td>
                          <td className="psi-band-moderate">55–154</td>
                          <td className="psi-band-unhealthy">155–254</td>
                          <td className="psi-band-very-unhealthy">255–354</td>
                          <td className="psi-band-hazardous">355+</td>
                        </tr>
                        <tr>
                          <th scope="row">O₃ (ppb)</th>
                          <td className="psi-band-good">0–54</td>
                          <td className="psi-band-moderate">55–70</td>
                          <td className="psi-band-unhealthy">71–85</td>
                          <td className="psi-band-very-unhealthy">86–105</td>
                          <td className="psi-band-hazardous">106+</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </section>
              </DataPanel>
            </aside>
          </div>
        )}
      </QueryState>
    </>
  );
}
