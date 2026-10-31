import { describe, expect, it } from "vitest";
import {
  crowdClockLabel,
  crowdForecastDayLabel,
  crowdLatestReading,
  crowdPeriodLabel,
  crowdReportingPeriod,
  crowdStationCodeSort,
  crowdStationLabel,
} from "../utils/crowding";

describe("crowd station labels", () => {
  it("joins the station code with the official name", () => {
    expect(
      crowdStationLabel({
        id: "ce1",
        station: "CE1",
        station_name: "BAYFRONT MRT STATION",
        line: "CEL",
        level: "low",
      }),
    ).toBe("CE1 BAYFRONT MRT STATION");
  });

  it("keeps the code when the name is missing", () => {
    expect(
      crowdStationLabel({
        id: "unknown",
        station: "XX99",
        line: "CCL",
        level: "unknown",
      }),
    ).toBe("XX99");
  });
});

describe("crowd period labels", () => {
  it("joins start and end times into a period", () => {
    expect(
      crowdPeriodLabel({
        start_time: "2026-09-12T08:00:00+08:00",
        end_time: "2026-09-12T08:10:00+08:00",
      }),
    ).toBe("08:00–08:10");
  });

  it("falls back to the start time when the end is missing", () => {
    expect(
      crowdPeriodLabel({
        start_time: "2026-09-12T08:00:00+08:00",
      }),
    ).toBe("08:00");
  });
});

describe("crowd reporting period", () => {
  it("uses the latest start-to-end interval", () => {
    expect(
      crowdReportingPeriod([
        {
          id: "first",
          station: "CC1",
          line: "CCL",
          level: "low",
          start_time: "2026-09-12T08:00:00+08:00",
          end_time: "2026-09-12T08:10:00+08:00",
        },
        {
          id: "later",
          station: "CC2",
          line: "CCL",
          level: "high",
          start_time: "2026-09-12T08:10:00+08:00",
          end_time: "2026-09-12T08:20:00+08:00",
        },
      ]),
    ).toBe("08:10–08:20");
  });

  it("returns the latest reading for one station", () => {
    expect(
      crowdLatestReading(
        [
          {
            id: "first",
            station: "CC1",
            line: "CCL",
            level: "low",
            start_time: "2026-09-12T08:00:00+08:00",
          },
          {
            id: "later",
            station: "CC1",
            line: "CCL",
            level: "moderate",
            start_time: "2026-09-12T08:10:00+08:00",
          },
        ],
        "CC1",
      )?.level,
    ).toBe("moderate");
  });
});

describe("crowd forecast labels", () => {
  it("uses a 24-hour clock for forecast columns", () => {
    expect(crowdClockLabel("2026-09-12T00:30:00+08:00")).toBe("00:30");
  });

  it("names the forecast day from the first timestamp", () => {
    expect(
      crowdForecastDayLabel([
        {
          id: "cc1",
          station: "CC1",
          line: "CCL",
          level: "low",
          start_time: "2026-09-12T00:00:00+08:00",
        },
      ]),
    ).toBe("Forecast for 12 September 2026");
  });

  it("orders station codes from highest number to lowest", () => {
    expect(["CC1", "CC10", "CC34"].sort(crowdStationCodeSort)).toEqual([
      "CC34",
      "CC10",
      "CC1",
    ]);
  });
});
