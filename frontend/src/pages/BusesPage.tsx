import { type FormEvent, useMemo, useState } from "react";
import { useBusLocations, useBusRoute, useBuses } from "../api/queries";
import type { BusArrival, BusVisit, GeoPoint } from "../api/schema";
import { MapView, type MapPath } from "../components/MapView";
import { EmptyState, QueryState } from "../components/QueryState";
import { TransitSubnav } from "../components/TransitSubnav";

const LOAD_LABELS: Record<NonNullable<BusVisit["load"]>, string> = {
  seats: "Seats",
  standing: "Standing",
  limited: "Limited",
  unknown: "",
};

const ROUTE_COLOURS = ["#35c9ff", "#f5d76e", "#52e0a1", "#ff9f43"];

function serviceRank(serviceNo: string): [number, string] {
  const match = /^(\d+)/.exec(serviceNo);
  return [match ? Number(match[1]) : Number.MAX_SAFE_INTEGER, serviceNo];
}

function soonestMinutes(arrival: BusArrival): number {
  const minutes = arrival.visits
    .map((visit) => visit.minutes)
    .filter((value): value is number => value !== null);
  return minutes.length ? Math.min(...minutes) : Number.POSITIVE_INFINITY;
}

function timeLabel(minutes: number | null): string {
  if (minutes === null) return "—";
  if (minutes <= 0) return "Arr";
  return `${minutes} min`;
}

function featureText(visit: BusVisit | undefined): string {
  if (!visit) return "Live arrival";
  const marks = [
    LOAD_LABELS[visit.load ?? "unknown"],
    visit.wheelchair ? "Wheelchair" : "",
    visit.type === "DD" ? "Double-deck" : visit.type === "BD" ? "Bendy" : "",
  ].filter(Boolean);
  return marks.join(" · ") || "Live arrival";
}

function updatedLabel(fetchedAt: string | undefined): string {
  if (!fetchedAt) return "";
  const date = new Date(fetchedAt);
  if (Number.isNaN(date.getTime())) return "";
  return `Updated ${date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}

export default function BusesPage() {
  const [draftStop, setDraftStop] = useState("");
  const [draftService, setDraftService] = useState("");
  const [stopCode, setStopCode] = useState("");
  const [routeService, setRouteService] = useState("");
  const [serviceFilter, setServiceFilter] = useState("");
  const [sortMode, setSortMode] = useState<"soonest" | "service">("soonest");
  const [showStops, setShowStops] = useState(false);
  const arrivalsQuery = useBuses(stopCode);
  const locationsQuery = useBusLocations(showStops);
  const routeQuery = useBusRoute(routeService);
  const arrivals = arrivalsQuery.data?.data;
  const route = routeQuery.data?.data;

  const displayedArrivals = useMemo(() => {
    const filter = serviceFilter.trim().toLowerCase();
    const rows = (arrivals?.arrivals ?? []).filter(
      (arrival) =>
        !filter || arrival.service_no.toLowerCase().includes(filter),
    );
    return [...rows].sort((left, right) => {
      const [leftRank, leftName] = serviceRank(left.service_no);
      const [rightRank, rightName] = serviceRank(right.service_no);
      if (sortMode === "service") {
        return leftRank - rightRank || leftName.localeCompare(rightName);
      }
      return (
        soonestMinutes(left) - soonestMinutes(right) ||
        leftRank - rightRank ||
        leftName.localeCompare(rightName)
      );
    });
  }, [arrivals?.arrivals, serviceFilter, sortMode]);

  const stopPoints = useMemo<GeoPoint[]>(
    () =>
      (locationsQuery.data?.data.stops ?? []).map((stop) => ({
        id: stop.code,
        name: stop.road ? `${stop.name} · ${stop.road}` : stop.name,
        latitude: stop.latitude ?? Number.NaN,
        longitude: stop.longitude ?? Number.NaN,
        category: "bus-stops",
        detail: stop.code,
      })),
    [locationsQuery.data?.data.stops],
  );

  const routePaths = useMemo<MapPath[]>(
    () =>
      (route?.directions ?? []).flatMap((direction, index) => {
        const positions = direction.stops.flatMap((stop) =>
          stop.latitude != null && stop.longitude != null
            ? [[stop.latitude, stop.longitude] as [number, number]]
            : [],
        );
        return positions.length > 1
          ? [
              {
                id: `${route?.service_no}-${direction.direction}`,
                color: ROUTE_COLOURS[index % ROUTE_COLOURS.length],
                positions,
              },
            ]
          : [];
      }),
    [route],
  );

  const routePoints = useMemo<GeoPoint[]>(() => {
    if (showStops) return [];
    return (route?.directions ?? []).flatMap((direction) =>
      direction.stops.flatMap((stop) =>
        stop.latitude != null && stop.longitude != null
          ? [
              {
                id: `route-${direction.direction}-${stop.code}`,
                name: stop.name,
                latitude: stop.latitude,
                longitude: stop.longitude,
                category: "bus-stops",
                detail: stop.code,
              },
            ]
          : [],
      ),
    );
  }, [route, showStops]);

  function searchStop(event: FormEvent) {
    event.preventDefault();
    const nextStop = draftStop.trim();
    if (!/^\d{5}$/.test(nextStop)) return;
    setStopCode(nextStop);
    setRouteService("");
    setDraftService("");
  }

  function searchRoute(event: FormEvent) {
    event.preventDefault();
    const nextService = draftService.trim();
    if (!/^[A-Za-z0-9]{1,4}$/.test(nextService)) return;
    setRouteService(nextService);
    setStopCode("");
    setDraftStop("");
  }

  function selectStop(point: GeoPoint) {
    const code = typeof point.detail === "string" ? point.detail : point.id;
    if (point.category !== "bus-stops" || !/^\d{5}$/.test(code)) return;
    setDraftStop(code);
    setStopCode(code);
    setRouteService("");
    setDraftService("");
  }

  const stopTitle = arrivals?.stop
    ? arrivals.stop.name.startsWith("Bus stop ")
      ? arrivals.stop.name
      : `${arrivals.stop.name} (${arrivals.stop.code})`
    : "Bus stop";

  return (
    <>
      <TransitSubnav />
      <div className="bus-operations-layout">
        <section className="bus-panel" aria-label="Bus search">
          <div className="bus-search-header">
            <form onSubmit={searchStop}>
              <p>Bus Arrival Timings</p>
              <div className="bus-search-row">
                <label className="sr-only" htmlFor="bus-stop-code">
                  Bus stop code
                </label>
                <input
                  id="bus-stop-code"
                  value={draftStop}
                  onChange={(event) => setDraftStop(event.target.value)}
                  inputMode="numeric"
                  pattern="\d{5}"
                  maxLength={5}
                  placeholder="Enter bus stop code"
                />
                <button
                  type="submit"
                  aria-label="Search bus stop"
                  disabled={!/^\d{5}$/.test(draftStop.trim())}
                >
                  Search
                </button>
              </div>
            </form>
            <form onSubmit={searchRoute}>
              <p>Bus Service Routes</p>
              <div className="bus-search-row">
                <label className="sr-only" htmlFor="bus-service-no">
                  Service number
                </label>
                <input
                  id="bus-service-no"
                  value={draftService}
                  onChange={(event) => setDraftService(event.target.value)}
                  maxLength={4}
                  placeholder="Enter service number (e.g. 21, 23A, CT8)"
                />
                <button
                  type="submit"
                  aria-label="Search bus service"
                  disabled={!/^[A-Za-z0-9]{1,4}$/.test(draftService.trim())}
                >
                  Search
                </button>
              </div>
            </form>
          </div>

          {routeService ? (
            <QueryState
              loading={routeQuery.isPending}
              error={routeQuery.error}
              fetching={routeQuery.isFetching}
              meta={routeQuery.data?.meta}
              onRetry={() => void routeQuery.refetch()}
            >
              {route?.directions.length ? (
                <div className="bus-route-list">
                  {route.directions.map((direction) => (
                    <article key={direction.direction}>
                      <h2>
                        Service {route.service_no} · Direction {direction.direction}
                      </h2>
                      <p>
                        {direction.origin} to {direction.destination}
                        {direction.first_bus && direction.last_bus
                          ? ` · Weekday ${direction.first_bus}–${direction.last_bus}`
                          : ""}
                      </p>
                      <ol>
                        {direction.stops.map((stop) => (
                          <li key={`${direction.direction}-${stop.sequence}-${stop.code}`}>
                            {stop.name}
                            <span>{stop.code}</span>
                          </li>
                        ))}
                      </ol>
                    </article>
                  ))}
                </div>
              ) : (
                <EmptyState>No route was found for this service.</EmptyState>
              )}
            </QueryState>
          ) : (
            <>
              <div className="bus-arrival-toolbar">
                <fieldset>
                  <legend className="sr-only">Sort arrivals</legend>
                  <label>
                    <input
                      type="radio"
                      name="bus-sort"
                      checked={sortMode === "soonest"}
                      onChange={() => setSortMode("soonest")}
                    />
                    Soonest
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="bus-sort"
                      checked={sortMode === "service"}
                      onChange={() => setSortMode("service")}
                    />
                    Service no.
                  </label>
                </fieldset>
                <label>
                  <span className="sr-only">Filter service</span>
                  <input
                    value={serviceFilter}
                    onChange={(event) => setServiceFilter(event.target.value)}
                    placeholder="Filter service (e.g. 12)"
                  />
                </label>
              </div>
              {stopCode ? (
                <QueryState
                  loading={arrivalsQuery.isPending}
                  error={arrivalsQuery.error}
                  fetching={arrivalsQuery.isFetching}
                  meta={arrivalsQuery.data?.meta}
                  onRetry={() => void arrivalsQuery.refetch()}
                >
                  <div className="bus-arrival-board">
                    <header>
                      <div>
                        <p>Stop arrivals</p>
                        <h2>{stopTitle}</h2>
                      </div>
                      <span>{updatedLabel(arrivalsQuery.data?.meta?.fetched_at)}</span>
                    </header>
                    {displayedArrivals.length ? (
                      <div className="bus-arrival-list">
                        {displayedArrivals.map((arrival) => (
                          <article
                            className="bus-arrival-row"
                            key={arrival.service_no}
                          >
                            <strong>{arrival.service_no}</strong>
                            <div>
                              <p>
                                {arrival.destination
                                  ? `Towards ${arrival.destination}`
                                  : "Next buses"}
                              </p>
                              <small>{featureText(arrival.visits[0])}</small>
                            </div>
                            <div className="bus-time-chips">
                              {arrival.visits.map((visit, index) => (
                                <span
                                  className={index === 0 ? "is-next" : undefined}
                                  key={`${arrival.service_no}-${index}`}
                                >
                                  {timeLabel(visit.minutes)}
                                </span>
                              ))}
                            </div>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <EmptyState>No matching arrivals were reported.</EmptyState>
                    )}
                  </div>
                </QueryState>
              ) : (
                <EmptyState>Search for a bus stop to see arrivals.</EmptyState>
              )}
            </>
          )}
        </section>
        <section className="bus-map-panel" aria-label="Bus map">
          <button
            type="button"
            className={showStops ? "is-active" : undefined}
            onClick={() => setShowStops((current) => !current)}
          >
            {locationsQuery.isFetching && showStops
              ? "Loading bus stops…"
              : showStops
                ? "Hide Bus Stop Locations"
                : "Show Bus Stop Locations"}
          </button>
          {showStops && locationsQuery.error && (
            <p className="bus-map-note">Bus stop locations are unavailable.</p>
          )}
          <MapView
            points={showStops ? stopPoints : routePoints}
            paths={routePaths}
            centre={[1.3521, 103.8198]}
            height={720}
            ariaLabel="Bus arrivals map"
            onSelect={selectStop}
          />
        </section>
      </div>
    </>
  );
}
