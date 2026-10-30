import { useMemo, useState } from "react";
import { useCrowding } from "../api/queries";
import type { CrowdReading } from "../api/schema";
import { DataPanel } from "../components/DataPanel";
import { EmptyState, QueryState } from "../components/QueryState";
import { TransitSubnav } from "../components/TransitSubnav";

const EMPTY_READINGS: CrowdReading[] = [];

export default function CrowdingPage() {
  const query = useCrowding();
  const readings = query.data?.data.readings ?? EMPTY_READINGS;
  const lines = [...new Set(readings.map((reading) => reading.line))];
  const [selectedLine, setSelectedLine] = useState("");
  const displayedReadings = useMemo(
    () =>
      readings.filter(
        (reading) => !selectedLine || reading.line === selectedLine,
      ),
    [readings, selectedLine],
  );
  const timeSlots = useMemo(
    () =>
      [...new Set(displayedReadings.map((reading) => reading.start_time ?? ""))]
        .filter(Boolean)
        .sort(),
    [displayedReadings],
  );
  const stations = [
    ...new Set(displayedReadings.map((reading) => reading.station)),
  ];

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
          title="MRT/LRT Station Crowd Forecast"
          eyebrow="Public transit"
          className="crowd-forecast-panel"
        >
          {readings.length ? (
            <div className="crowd-forecast-content">
              <label className="crowd-line-select">
                Select train line
                <select
                  value={selectedLine}
                  onChange={(event) => setSelectedLine(event.target.value)}
                >
                  <option value="">All lines</option>
                  {lines.map((line) => (
                    <option key={line} value={line}>{line}</option>
                  ))}
                </select>
              </label>
              <div className="crowd-forecast-legend" aria-label="Crowd levels">
                <span><i className="crowd-low" />Low</span>
                <span><i className="crowd-moderate" />Moderate</span>
                <span><i className="crowd-high" />High</span>
              </div>
              <div className="crowd-timeline-scroll">
                <div
                  className="crowd-timeline"
                  style={{
                    gridTemplateColumns: `minmax(180px, 1fr) repeat(${timeSlots.length}, minmax(28px, 1fr))`,
                  }}
                >
                  <span className="crowd-timeline-station">Station</span>
                  {timeSlots.map((timeSlot) => (
                    <time className="crowd-timeline-time" key={timeSlot}>
                      {new Date(timeSlot).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </time>
                  ))}
                  {stations.map((station) => (
                    <div className="crowd-timeline-row" key={station}>
                      <strong>{station}</strong>
                      {timeSlots.map((timeSlot) => {
                        const reading = displayedReadings.find(
                          (item) =>
                            item.station === station
                            && item.start_time === timeSlot,
                        );
                        return (
                          <span
                            aria-label={`${station} at ${timeSlot}: ${reading?.level ?? "unknown"}`}
                            className={`crowd-cell crowd-${reading?.level ?? "unknown"}`}
                            key={`${station}-${timeSlot}`}
                            title={reading?.level ?? "unknown"}
                          />
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <EmptyState>No crowd forecasts are currently available.</EmptyState>
          )}
        </DataPanel>
      </QueryState>
    </>
  );
}
