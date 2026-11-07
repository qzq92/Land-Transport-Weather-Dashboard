import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import CrowdingPage from "../pages/CrowdingPage";

const realtimeReadings = [
  {
    id: "cc1",
    station: "CC1",
    station_name: "Dhoby Ghaut",
    line: "CCL",
    level: "low",
    start_time: "2026-09-12T08:00:00+08:00",
    end_time: "2026-09-12T08:10:00+08:00",
  },
  {
    id: "cc2",
    station: "CC2",
    station_name: "Bras Basah",
    line: "CCL",
    level: "high",
    start_time: "2026-09-12T08:00:00+08:00",
    end_time: "2026-09-12T08:10:00+08:00",
  },
];

const forecastReadings = [
  ...realtimeReadings,
  {
    id: "cc1-later",
    station: "CC1",
    station_name: "Dhoby Ghaut",
    line: "CCL",
    level: "moderate",
    start_time: "2026-09-12T08:10:00+08:00",
    end_time: "2026-09-12T08:20:00+08:00",
  },
];

vi.mock("../api/queries", () => ({
  useCrowding: () => ({
    isPending: false,
    isFetching: false,
    error: null,
    data: { data: { readings: realtimeReadings } },
    refetch: () => undefined,
  }),
  useCrowdForecast: () => ({
    isPending: false,
    isFetching: false,
    error: null,
    data: { data: { readings: forecastReadings } },
    refetch: () => undefined,
  }),
}));

/** Renders the crowding page under a fixed router path for tests. */
function renderCrowding(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <CrowdingPage />
    </MemoryRouter>,
  );
}

describe("crowding page", () => {
  it("shows one colour cell per station and centres the reporting period", () => {
    renderCrowding("/transit/crowding");

    expect(screen.getByText("08:00–08:10").closest(".crowd-realtime-period")).toBeTruthy();
    expect(screen.getByText("CC1 Dhoby Ghaut")).toBeInTheDocument();
    expect(screen.getByText("CC2 Bras Basah")).toBeInTheDocument();
    expect(screen.queryByText("08:10–08:20")).not.toBeInTheDocument();
    expect(screen.queryByText("Station")).not.toBeInTheDocument();
    expect(document.querySelectorAll(".crowd-realtime-row .crowd-cell")).toHaveLength(2);
  });

  it("shows station names and crowd status on the forecast grid", () => {
    renderCrowding("/transit/crowding/forecast");

    expect(screen.getByText("CC1 Dhoby Ghaut")).toBeInTheDocument();
    expect(screen.getByText("CC2 Bras Basah")).toBeInTheDocument();
    expect(screen.getByLabelText("CC1 Dhoby Ghaut 08:00: low")).toHaveClass(
      "crowd-low",
    );
    expect(screen.getByLabelText("CC2 Bras Basah 08:00: high")).toHaveClass(
      "crowd-high",
    );
    expect(screen.getByText("08:00")).toBeInTheDocument();
    expect(screen.getByText("08:10")).toBeInTheDocument();
    expect(screen.getByText("Station")).toBeInTheDocument();
    expect(screen.getByText("Forecast for 12 September 2026")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "MRT/LRT Station Crowd Forecast" })).toBeInTheDocument();
  });
});
