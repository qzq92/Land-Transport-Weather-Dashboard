import { useMemo, useState } from "react";
import { useCrowding } from "../api/queries";
import type { CrowdReading } from "../api/schema";
import { DataPanel } from "../components/DataPanel";
import { EmptyState, QueryState } from "../components/QueryState";
import { TransitSubnav } from "../components/TransitSubnav";
import { crowdStationLabel } from "../utils/crowding";

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

export default function CrowdingPage() {
  const [selectedLine, setSelectedLine] = useState("CCL");
  const query = useCrowding(selectedLine);
  const readings = query.data?.data.readings ?? EMPTY_READINGS;
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
  const stations = useMemo(() => {
    const labels = new Map<string, string>();
    for (const reading of displayedReadings) {
      if (!labels.has(reading.station)) {
        labels.set(reading.station, crowdStationLabel(reading));
      }
    }
    return [...labels.entries()];
  }, [displayedReadings]);

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
              <div className="crowd-forecast-legend" aria-label="Crowd levels">
                <span><i className="crowd-low" />Low</span>
                <span><i className="crowd-moderate" />Moderate</span>
                <span><i className="crowd-high" />High</span>
              </div>
              <div className="crowd-timeline-scroll">
                <div
                  className="crowd-timeline"
                  style={{
                    gridTemplateColumns: `minmax(240px, 1.6fr) repeat(${timeSlots.length}, minmax(28px, 1fr))`,
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
                  {stations.map(([station, label]) => (
                    <div className="crowd-timeline-row" key={station}>
                      <strong>{label}</strong>
                      {timeSlots.map((timeSlot) => {
                        const reading = displayedReadings.find(
                          (item) =>
                            item.station === station
                            && item.start_time === timeSlot,
                        );
                        return (
                          <span
                            aria-label={`${label} at ${timeSlot}: ${reading?.level ?? "unknown"}`}
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
