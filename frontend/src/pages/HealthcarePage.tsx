import { useHealthcareWaitTimes } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { EmptyState, QueryState } from "../components/QueryState";

function formatValue(value: number | null | undefined, fallback = "—"): string {
  return value === null || value === undefined ? fallback : String(value);
}

function updatedLabel(value: string | undefined): string {
  if (!value) return "Update time unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Update time unavailable";
  return `Fetched ${date.toLocaleString()}`;
}

export default function HealthcarePage() {
  const query = useHealthcareWaitTimes();
  const data = query.data?.data;

  return (
    <QueryState
      loading={query.isPending}
      error={query.error}
      fetching={query.isFetching}
      meta={query.data?.meta}
      onRetry={() => void query.refetch()}
    >
      <div className="page-stack">
        <header className="page-header">
          <p className="eyebrow">Healthcare operations</p>
          <h1>Emergency department wait times</h1>
          <p>
            Official queue estimates from participating NHG and NUHS hospitals.
            Patients are triaged by clinical urgency, not arrival order.
          </p>
        </header>

        <DataPanel
          title="Hospital queue status"
          eyebrow="Official estimates"
          action={
            <span className="healthcare-updated">
              {updatedLabel(query.data?.meta?.fetched_at)}
            </span>
          }
        >
          {data?.facilities.length ? (
            <div className="healthcare-wait-grid">
              {data.facilities.map((facility) => (
                <article className="healthcare-wait-card" key={facility.id}>
                  <header>
                    <div>
                      <p className="eyebrow">
                        {facility.cluster} · {facility.category}
                      </p>
                      <h3>{facility.hospital}</h3>
                    </div>
                  </header>
                  <dl>
                    <div>
                      <dt>Patients in queue</dt>
                      <dd>{formatValue(facility.patients_waiting)}</dd>
                    </div>
                    <div>
                      <dt>Wait to see doctor</dt>
                      <dd>{facility.wait_to_doctor ?? "—"}</dd>
                    </div>
                    {facility.bed_wait && (
                      <div>
                        <dt>Bed wait</dt>
                        <dd>{facility.bed_wait}</dd>
                      </div>
                    )}
                  </dl>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState>
              No hospital waiting-time data is currently available.
            </EmptyState>
          )}
        </DataPanel>

        <DataPanel
          title="Sources and limitations"
          eyebrow="Data provenance"
        >
          <p className="healthcare-disclaimer">
            These are estimates for information only and may change quickly.
            For life-threatening emergencies, call 995. Confirm current
            information with the hospital before making healthcare decisions.
          </p>
          <ul className="healthcare-source-list">
            {(data?.sources ?? []).map((source) => (
              <li key={source.id}>
                <a href={source.url} target="_blank" rel="noreferrer">
                  {source.name}
                </a>
                <span className={`source-state is-${source.state}`}>
                  {source.state === "available" ? "Available" : "Unavailable"}
                </span>
              </li>
            ))}
          </ul>
        </DataPanel>
      </div>
    </QueryState>
  );
}
