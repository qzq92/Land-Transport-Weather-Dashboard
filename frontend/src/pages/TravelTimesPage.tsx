import { NavLink } from "react-router-dom";
import { useTravelTimes } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { PageHeader } from "../components/PageElements";
import { EmptyState, QueryState } from "../components/QueryState";

export default function TravelTimesPage() {
  const query = useTravelTimes();
  const journeys = query.data?.data.journeys ?? [];

  return (
    <>
      <PageHeader
        title="Estimated travel times"
        description="Current point-to-point journey estimates grouped by expressway and direction."
      />
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
        <DataPanel
          title="Expressway journeys"
          eyebrow={`${journeys.length} live estimates`}
        >
          {journeys.length ? (
            <div className="table-scroll">
              <table>
                <caption className="sr-only">
                  Current estimated expressway travel times
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Expressway</th>
                    <th scope="col">Direction</th>
                    <th scope="col">Route</th>
                    <th scope="col">Estimate</th>
                    <th scope="col">Distance</th>
                  </tr>
                </thead>
                <tbody>
                  {journeys.map((journey) => (
                    <tr key={journey.id}>
                      <td><strong>{journey.expressway}</strong></td>
                      <td>{journey.direction}</td>
                      <td>{journey.start} → {journey.end}</td>
                      <td><span className="time-pill">{journey.minutes} min</span></td>
                      <td>
                        {journey.distance_km === undefined
                          ? "—"
                          : `${journey.distance_km} km`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState>No travel-time estimates are available.</EmptyState>
          )}
        </DataPanel>
      </QueryState>
    </>
  );
}
