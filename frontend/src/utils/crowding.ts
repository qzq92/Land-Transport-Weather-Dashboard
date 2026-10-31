import type { CrowdReading } from "../api/schema";

/**
 * Formats a crowd forecast row with its provider station code and official name.
 */
export function crowdStationLabel(reading: CrowdReading): string {
  const name = reading.station_name?.trim();
  if (name && !reading.station.includes(name)) {
    return `${reading.station} ${name}`;
  }
  return reading.station;
}
