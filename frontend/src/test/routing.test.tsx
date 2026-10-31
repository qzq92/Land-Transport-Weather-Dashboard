import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AppRoutes } from "../App";

vi.mock("../api/queries", () => ({
  useRailStatus: () => ({
    isPending: false,
    data: {
      data: {
        state: "normal",
        summary: "All train services are operational",
        updated_at: "2026-10-30T12:00:00+08:00",
      },
    },
  }),
}));

vi.mock("../pages/HomePage", () => ({
  default: () => <h1>Overview route</h1>,
}));
vi.mock("../pages/WeatherPage", () => ({
  default: () => <h1>Weather route</h1>,
}));
vi.mock("../pages/EnvironmentPage", () => ({
  default: () => <h1>Environment route</h1>,
}));
vi.mock("../pages/HealthcarePage", () => ({
  default: () => <h1>Healthcare route</h1>,
}));
vi.mock("../pages/TransportPage", () => ({
  default: () => <h1>Transport route</h1>,
}));
vi.mock("../pages/TravelTimesPage", () => ({
  default: () => <h1>Travel times route</h1>,
}));
vi.mock("../pages/CamerasPage", () => ({
  default: () => <h1>Cameras route</h1>,
}));
vi.mock("../pages/CrowdingPage", () => ({
  default: () => <h1>Crowding route</h1>,
}));
vi.mock("../pages/BusesPage", () => ({
  default: () => <h1>Buses route</h1>,
}));
vi.mock("../pages/NearbyPage", () => ({
  default: () => <h1>Nearby route</h1>,
}));

describe("application routing", () => {
  it.each([
    ["/", "Overview route"],
    ["/weather/realtime", "Weather route"],
    ["/environment", "Environment route"],
    ["/healthcare", "Healthcare route"],
    ["/transport", "Transport route"],
    ["/transport/travel-times", "Travel times route"],
    ["/transport/cameras", "Cameras route"],
    ["/transit/crowding", "Crowding route"],
    ["/transit/buses", "Buses route"],
    ["/nearby", "Nearby route"],
  ])("renders %s", async (path, heading) => {
    render(
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: heading }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("region", { name: "Rail service status" }),
    ).toBeInTheDocument();
  });

  it("renders a not-found view for unknown paths", async () => {
    render(
      <MemoryRouter initialEntries={["/not-a-route"]}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Page not found" }),
    ).toBeInTheDocument();
  });
});
