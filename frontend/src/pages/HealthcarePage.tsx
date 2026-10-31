import { useHealthcareWaitTimes } from "../api/queries";
import type { HealthcareFacility, HealthcareSource } from "../api/schema";
import { DataPanel } from "../components/DataPanel";
import { EmptyState, QueryState } from "../components/QueryState";

function formatValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "unavailable";
  }
  return String(value);
}

function metricCell(value: string | number | null | undefined) {
  const display = formatValue(value);
  return (
    <td className={display === "unavailable" ? "is-unavailable" : undefined}>
      {display}
    </td>
  );
}

function updatedLabel(value: string | undefined): string {
  if (!value) return "Update time unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Update time unavailable";
  return `Fetched ${date.toLocaleString()}`;
}

function hospitalHref(facility: HealthcareFacility, sources: HealthcareSource[]): string | undefined {
  if (facility.source_url) return facility.source_url;
  const cluster = facility.cluster.toLowerCase();
  return sources.find((source) => source.id === cluster || source.name.includes(facility.hospital))
    ?.url;
}

export default function HealthcarePage() {
  const query = useHealthcareWaitTimes();
  const data = query.data?.data;
  const sources = data?.sources ?? [];
  const unavailable = sources.filter((source) => source.state === "unavailable");

  return (
    <QueryState
      loading={query.isPending}
      error={query.error}
      fetching={query.isFetching}
      meta={query.data?.meta}
      onRetry={() => void query.refetch()}
    >
      <div className="page-stack">
        <section
          className="healthcare-status-banner"
          aria-label="Healthcare data limitations"
        >
          <div>
            <strong>Limitations</strong>
            <span>
              These are estimates for information only and may change quickly.
              For life-threatening emergencies, call 995. Confirm current
              information with the hospital before making healthcare decisions.
            </span>
          </div>
          {unavailable.length > 0 && (
            <small>
              Unavailable: {unavailable.map((source) => source.name).join(", ")}
            </small>
          )}
        </section>

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
            <div className="table-scroll">
              <table className="healthcare-wait-table">
                <caption className="sr-only">
                  Emergency department queue estimates by hospital
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Hospital</th>
                    <th scope="col">Patients in queue</th>
                    <th scope="col">Wait to see doctor</th>
                    <th scope="col">Bed wait</th>
                    <th scope="col">Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {data.facilities.map((facility) => {
                    const href = hospitalHref(facility, sources);
                    return (
                      <tr key={facility.id}>
                        <th scope="row">
                          {href ? (
                            <a href={href} rel="noreferrer" target="_blank">
                              {facility.hospital}
                            </a>
                          ) : (
                            facility.hospital
                          )}
                          <small>
                            {facility.cluster} · {facility.category}
                          </small>
                        </th>
                        {metricCell(facility.patients_waiting)}
                        {metricCell(facility.wait_to_doctor)}
                        {metricCell(facility.bed_wait)}
                        {metricCell(facility.updated_at)}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState>
              No hospital waiting-time data is currently available.
            </EmptyState>
          )}
        </DataPanel>
      </div>
    </QueryState>
  );
}
