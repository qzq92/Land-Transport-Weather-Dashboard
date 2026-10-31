import type { CrowdReading } from "../api/schema";

/**
 * Formats a crowd row with its provider station code and official name.
 */
export function crowdStationLabel(reading: CrowdReading): string {
  const name = reading.station_name?.trim();
  if (name && !reading.station.includes(name)) {
    return `${reading.station} ${name}`;
  }
  return reading.station;
}

function formatCrowdTime(value?: string): string {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleTimeString("en-SG", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Singapore",
  });
}

/**
 * Formats a crowd interval as a start-to-end period for grid headers.
 */
export function crowdPeriodLabel(
  reading: Pick<CrowdReading, "start_time" | "end_time">,
): string {
  const start = formatCrowdTime(reading.start_time);
  const end = formatCrowdTime(reading.end_time);
  if (start && end && start !== end) {
    return `${start}–${end}`;
  }
  return start || end;
}

function byStartTime(left: CrowdReading, right: CrowdReading): number {
  return (left.start_time ?? "").localeCompare(right.start_time ?? "");
}

/**
 * Returns the latest crowd observation for one station.
 */
export function crowdLatestReading(
  readings: CrowdReading[],
  station: string,
): CrowdReading | undefined {
  return readings
    .filter((reading) => reading.station === station)
    .sort(byStartTime)
    .at(-1);
}

/**
 * Returns the newest reading that includes a start or end time.
 */
export function crowdLatestTimedReading(
  readings: CrowdReading[],
): CrowdReading | undefined {
  return readings
    .filter((reading) => reading.start_time || reading.end_time)
    .sort(byStartTime)
    .at(-1);
}

/**
 * Returns the latest start-to-end period across a set of crowd readings.
 */
export function crowdReportingPeriod(readings: CrowdReading[]): string {
  const latest = crowdLatestTimedReading(readings);
  return latest ? crowdPeriodLabel(latest) : "";
}

/**
 * Formats a crowd timestamp as a 24-hour clock label for forecast columns.
 */
export function crowdClockLabel(value?: string): string {
  return formatCrowdTime(value);
}

/**
 * Returns a "Forecast for {date}" caption from the readings' timestamps.
 */
export function crowdForecastDayLabel(readings: CrowdReading[]): string {
  const timed = readings.find((reading) => reading.start_time);
  if (!timed?.start_time) {
    return "";
  }
  const parsed = new Date(timed.start_time);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }
  const formatted = parsed.toLocaleDateString("en-SG", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Asia/Singapore",
  });
  return `Forecast for ${formatted}`;
}

/**
 * Sorts station codes by number descending, matching the line-order grid.
 */
export function crowdStationCodeSort(left: string, right: string): number {
  const parse = (value: string) => {
    const match = /^([A-Za-z]+)(\d+)/.exec(value);
    return match
      ? { prefix: match[1].toUpperCase(), number: Number(match[2]) }
      : { prefix: value.toUpperCase(), number: 0 };
  };
  const first = parse(left);
  const second = parse(right);
  return second.number - first.number || first.prefix.localeCompare(second.prefix);
}
