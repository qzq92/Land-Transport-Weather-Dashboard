import { useMemo, useState } from "react";
import { useMatch } from "react-router-dom";
import { useCrowdForecast, useCrowding } from "../api/queries";
import type { CrowdReading } from "../api/schema";
import { DataPanel } from "../components/DataPanel";
import { EmptyState, QueryState } from "../components/QueryState";
import { TransitSubnav } from "../components/TransitSubnav";
import {
  crowdClockLabel,
  crowdForecastDayLabel,
  crowdLatestReading,
  crowdLatestTimedReading,
  crowdPeriodLabel,
  crowdReportingPeriod,
  crowdStationCodeSort,
  crowdStationLabel,
} from "../utils/crowding";

const EMPTY_READINGS: CrowdReading[] = [];

const TRAIN_LINES = [
  ["BPL", "Bukit Panjang LRT (BPL)", "#7f8c8d"],
  ["CCL", "Circle Line (CCL)", "#f59e0b"],
  ["CEL", "Circle Line Extension (CEL)", "#f59e0b"],
  ["CGL", "Changi Airport Branch (CGL)", "#009645"],
  ["DTL", "Downtown Line (DTL)", "#005ec4"],
  ["EWL", "East West Line (EWL)", "#009645"],
  ["NEL", "North East Line (NEL)", "#9900aa"],
  ["NSL", "North South Line (NSL)", "#d42e12"],
  ["PLRT", "Punggol LRT (PLRT)", "#748fc4"],
  ["SLRT", "Sengkang LRT (SLRT)", "#748fc4"],
  ["TEL", "Thomson-East Coast Line (TEL)", "#9d5b25"],
] as const;

/** Realtime and forecast MRT/LRT station crowding grids by train line. */
export default function CrowdingPage() {
  const isForecast = Boolean(useMatch("/transit/crowding/forecast"));
  const [selectedLine, setSelectedLine] = useState("CCL");
  const realtimeQuery = useCrowding(selectedLine, !isForecast);
  const forecastQuery = useCrowdForecast(selectedLine, isForecast);
  const query = isForecast ? forecastQuery : realtimeQuery;
  const readings = query.data?.data.readings ?? EMPTY_READINGS;
  const timeSlots = useMemo(() => {
    const slots = new Map<string, string>();
    for (const reading of readings) {
      if (!reading.start_time || slots.has(reading.start_time)) {
        continue;
      }
      slots.set(
        reading.start_time,
        isForecast ? crowdClockLabel(reading.start_time) : crowdPeriodLabel(reading),
      );
    }
    return [...slots.entries()].sort(([left], [right]) => left.localeCompare(right));
  }, [isForecast, readings]);
  const stations = useMemo(() => {
    const labels = new Map<string, string>();
    for (const reading of readings) {
      if (!labels.has(reading.station)) {
        labels.set(reading.station, crowdStationLabel(reading));
      }
    }
    return [...labels.entries()].sort(([left], [right]) =>
      crowdStationCodeSort(left, right),
    );
  }, [readings]);
  const readingsByStationTime = useMemo(() => {
    const index = new Map<string, CrowdReading>();
    for (const reading of readings) {
      if (reading.start_time) {
        index.set(`${reading.station}|${reading.start_time}`, reading);
      }
    }
    return index;
  }, [readings]);
  const reportingReading = crowdLatestTimedReading(readings);
  const reportingPeriod = crowdReportingPeriod(readings);
  const forecastDayLabel = crowdForecastDayLabel(readings);
  const forecastColumns = `minmax(200px, 240px) repeat(${timeSlots.length}, minmax(14px, 1fr))`;
  const title = isForecast
    ? "MRT/LRT Station Crowd Forecast"
    : "MRT/LRT Station Crowd Realtime";
  const emptyMessage = isForecast
    ? "No crowd forecasts are currently available."
    : "No crowd readings are currently available.";

  return (
    <>
      <TransitSubnav />
      <QueryState
        loading={query.isPending}
        error={query.error}
        fetching={query.isFetching}
        meta={query.data?.meta}
        onRetry={() => void query.refetch()}
      >
        <DataPanel
          title={title}
          eyebrow="Public transit"
          className="crowd-forecast-panel"
        >
          {readings.length ? (
            <div className="crowd-forecast-content">
              <label className="crowd-line-select">
                Select train line
                <select
                  className={`crowd-line-select-input line-${selectedLine.toLowerCase()}`}
                  value={selectedLine}
                  onChange={(event) => setSelectedLine(event.target.value)}
                >
                  {TRAIN_LINES.map(([value, label, color]) => (
                    <option
                      key={value}
                      value={value}
                      style={{ color }}
                    >
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              {!isForecast && (
                <div className="crowd-forecast-legend" aria-label="Crowd levels">
                  <span><i className="crowd-low" />Low</span>
                  <span><i className="crowd-moderate" />Moderate</span>
                  <span><i className="crowd-high" />High</span>
                </div>
              )}
              {isForecast ? (
                <div className="crowd-forecast-board">
                  <div className="crowd-forecast-meta">
                    {forecastDayLabel && (
                      <p className="crowd-forecast-day">{forecastDayLabel}</p>
                    )}
                    <div className="crowd-forecast-legend" aria-label="Crowd levels">
                      <span><i className="crowd-low" />Low</span>
                      <span><i className="crowd-moderate" />Moderate</span>
                      <span><i className="crowd-high" />High</span>
                    </div>
                  </div>
                  <div className="crowd-timeline-scroll">
                    <div className="crowd-timeline">
                      <div
                        className="crowd-timeline-header"
                        style={{ gridTemplateColumns: forecastColumns }}
                      >
                        <strong>Station</strong>
                        {timeSlots.map(([timeSlot, label]) => (
                          <time className="crowd-timeline-time" dateTime={timeSlot} key={timeSlot}>
                            {label}
                          </time>
                        ))}
                      </div>
                      {stations.map(([station, label]) => (
                        <div
                          className="crowd-timeline-row"
                          key={station}
                          style={{ gridTemplateColumns: forecastColumns }}
                        >
                          <strong title={label}>{label}</strong>
                          {timeSlots.map(([timeSlot, clock]) => {
                            const reading = readingsByStationTime.get(
                              `${station}|${timeSlot}`,
                            );
                            const level = reading?.level ?? "unknown";
                            return (
                              <span
                                aria-label={`${label} ${clock}: ${level}`}
                                className={`crowd-cell crowd-${level}`}
                                key={`${station}-${timeSlot}`}
                                title={`${clock}: ${level}`}
                              />
                            );
                          })}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="crowd-realtime">
                  {reportingPeriod && (
                    <p className="crowd-realtime-period">
                      <time dateTime={reportingReading?.start_time}>
                        {reportingPeriod}
                      </time>
                    </p>
                  )}
                  <div className="crowd-realtime-grid">
                    {stations.map(([station, label]) => {
                      const reading = crowdLatestReading(readings, station);
                      const level = reading?.level ?? "unknown";
                      return (
                        <div className="crowd-realtime-row" key={station}>
                          <strong>{label}</strong>
                          <span
                            aria-label={`${label}${reportingPeriod ? ` ${reportingPeriod}` : ""}: ${level}`}
                            className={`crowd-cell crowd-${level}`}
                            title={`${reportingPeriod || "Current period"}: ${level}`}
                          />
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <EmptyState>{emptyMessage}</EmptyState>
          )}
        </DataPanel>
      </QueryState>
    </>
  );
}
