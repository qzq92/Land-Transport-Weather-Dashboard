import { useState } from "react";
import { useEnvironment } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { MapView } from "../components/MapView";
import { MetricGrid } from "../components/PageElements";
import { QueryState } from "../components/QueryState";
import { TimeSeriesChart } from "../components/TimeSeriesChart";

export default function EnvironmentPage() {
  const query = useEnvironment();
  const data = query.data?.data;
  const [showPsiTable, setShowPsiTable] = useState(false);
  const [showZikaClusters, setShowZikaClusters] = useState(false);
  const [showDengueClusters, setShowDengueClusters] = useState(false);

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
            className={`environment-operations-layout${showPsiTable ? " with-psi-table" : ""}`}
          >
            <aside className="environment-left-rail">
              <DataPanel title="UV index through the day" eyebrow="Exposure">
                <TimeSeriesChart
                  points={data.uv_index ?? []}
                  title="UV index"
                  unit=" index"
                />
              </DataPanel>
              {(["zika", "dengue"] as const)
                .filter(
                  (disease) =>
                    (disease === "zika" && showZikaClusters)
                    || (disease === "dengue" && showDengueClusters),
                )
                .map((disease) => {
                const clusters = (data.clusters ?? [])
                  .filter((cluster) => cluster.disease === disease)
                  .slice(0, 5);
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
                            <span>{cluster.location}</span>
                            {cluster.cases !== undefined && (
                              <b>{cluster.cases} cases</b>
                            )}
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
                    aria-pressed={showPsiTable}
                    className={showPsiTable ? "is-active" : ""}
                    onClick={() => setShowPsiTable((visible) => !visible)}
                    type="button"
                  >
                    PSI table view
                  </button>
                  <button
                    aria-pressed={showZikaClusters}
                    className={showZikaClusters ? "is-active" : ""}
                    onClick={() => setShowZikaClusters((visible) => !visible)}
                    type="button"
                  >
                    Show Zika clusters
                  </button>
                  <button
                    aria-pressed={showDengueClusters}
                    className={showDengueClusters ? "is-active" : ""}
                    onClick={() => setShowDengueClusters((visible) => !visible)}
                    type="button"
                  >
                    Show Dengue clusters
                  </button>
                </div>
                <MapView
                  points={(data.regions ?? []).map((region) => ({
                    ...region,
                    category: "environment",
                    value: region.psi,
                    detail: region.pollutant,
                  }))}
                  height={586}
                />
            </DataPanel>
            {showPsiTable && (
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
                  <div className="table-scroll">
                    <table>
                      <caption className="sr-only">
                        Air-quality pollutant health bands
                      </caption>
                      <thead>
                        <tr>
                          <th scope="col">Pollutant</th>
                          <th scope="col">Good</th>
                          <th scope="col">Moderate</th>
                          <th scope="col">Unhealthy</th>
                          <th scope="col">Very unhealthy</th>
                          <th scope="col">Hazardous</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <th scope="row">PM2.5 (µg/m³)</th>
                          <td>0–12</td><td>13–55</td><td>56–150</td>
                          <td>151–250</td><td>251+</td>
                        </tr>
                        <tr>
                          <th scope="row">PM10 (µg/m³)</th>
                          <td>0–54</td><td>55–154</td><td>155–254</td>
                          <td>255–354</td><td>355+</td>
                        </tr>
                        <tr>
                          <th scope="row">O₃ (ppb)</th>
                          <td>0–54</td><td>55–70</td><td>71–85</td>
                          <td>86–105</td><td>106+</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </section>
              </DataPanel>
            </aside>
            )}
          </div>
        )}
      </QueryState>
    </>
  );
}
