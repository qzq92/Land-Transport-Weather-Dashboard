import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import TransportPage from "../pages/TransportPage";

vi.mock("../api/queries", () => ({
  useTransport: () => ({
    isPending: false,
    isFetching: false,
    error: null,
    data: {
      data: {
        metrics: [{ id: "taxis", label: "Taxis", value: 12 }],
        points: [],
        incidents: [
          {
            id: "road-1",
            title: "PIE slow traffic",
            severity: "warning",
          },
        ],
        train_status: [
          {
            id: "rail-1",
            title: "NEL delay",
            detail: "Additional travel time towards HarbourFront.",
            severity: "warning",
          },
        ],
      },
    },
    refetch: () => undefined,
  }),
}));

vi.mock("../components/MapView", () => ({
  MapView: () => <div data-testid="transport-map" />,
}));

describe("transport page layout", () => {
  it("places rail advisories to the right of the map", () => {
    render(
      <MemoryRouter>
        <TransportPage />
      </MemoryRouter>,
    );

    const railHeading = screen.getByRole("heading", { name: "Rail advisories" });
    const mapHeading = screen.getByRole("heading", { name: "Road network map" });
    const roadHeading = screen.getByRole("heading", { name: "Road advisories" });

    expect(railHeading.closest(".transport-right-rail")).toBeTruthy();
    expect(mapHeading.closest(".transport-map-card")).toBeTruthy();
    expect(roadHeading.closest(".transport-operations-rail")).toBeTruthy();
    expect(screen.getByText("NEL delay")).toBeInTheDocument();
    expect(screen.getByText("PIE slow traffic")).toBeInTheDocument();
  });
});
