import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import NearbyPage from "../pages/NearbyPage";

vi.mock("../api/queries", () => ({
  useNearby: (_latitude: number, _longitude: number, enabled = true) => ({
    isPending: false,
    isFetching: false,
    error: null,
    data: enabled
      ? {
          data: {
            places: [
              {
                id: "park-1",
                name: "Bishan-Ang Mo Kio Park",
                category: "parks",
                distance_m: 350,
                latitude: 1.36,
                longitude: 103.84,
              },
              {
                id: "bus-stop-12345",
                name: "Bishan Interchange",
                category: "bus-stops",
                detail: "12345",
                distance_m: 420,
                latitude: 1.35,
                longitude: 103.85,
                arrivals: [
                  {
                    service_no: "52",
                    destination: "Bedok",
                    visits: [
                      {
                        minutes: 4,
                        load: "seats",
                        wheelchair: true,
                        type: "DD",
                      },
                      {
                        minutes: 16,
                        load: "standing",
                        wheelchair: false,
                        type: "SD",
                      },
                    ],
                  },
                ],
              },
            ],
          },
        }
      : undefined,
    refetch: () => undefined,
  }),
  usePlaceSearch: (query: string) => ({
    isPending: false,
    isFetching: false,
    error: null,
    data:
      query.trim().length >= 3
        ? {
            data: [
              {
                id: "place-1",
                label: "123456 BISHAN STREET 12",
                latitude: 1.35,
                longitude: 103.85,
              },
            ],
          }
        : { data: [] },
    refetch: () => undefined,
  }),
}));

vi.mock("../components/MapView", () => ({
  MapView: ({
    centre,
    zoom,
  }: {
    centre?: [number, number];
    zoom?: number;
  }) => (
    <div
      data-centre={centre?.join(",")}
      data-testid="nearby-map"
      data-zoom={zoom}
    />
  ),
}));

describe("nearby facilities search", () => {
  it("keeps the search box available before a location is selected", () => {
    render(<NearbyPage />);

    expect(screen.getByLabelText("Address or landmark")).toBeEnabled();
    expect(
      screen.getByPlaceholderText("Postal code or address"),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search" })).toBeDisabled();
    expect(screen.getByTestId("nearby-map")).toHaveAttribute(
      "data-centre",
      "1.3521,103.8198",
    );
    expect(
      screen.getByText(
        "Search for a postal address or landmark to show nearby facilities.",
      ),
    ).toBeInTheDocument();
  });

  it("shows address matches and facilities after a search is selected", async () => {
    const user = userEvent.setup();
    render(<NearbyPage />);

    await user.type(
      screen.getByLabelText("Address or landmark"),
      "123456",
    );
    await user.click(screen.getByRole("button", { name: "Search" }));
    await user.click(
      screen.getByRole("option", { name: "123456 BISHAN STREET 12" }),
    );

    expect(screen.getByTestId("nearby-map")).toHaveAttribute(
      "data-centre",
      "1.35,103.85",
    );
    expect(screen.getByTestId("nearby-map")).toHaveAttribute("data-zoom", "16");
    expect(screen.getByText("Bishan-Ang Mo Kio Park")).toBeInTheDocument();
    expect(screen.getByLabelText("Address or landmark")).toHaveValue(
      "123456 BISHAN STREET 12",
    );
    const legend = screen.getByRole("list", { name: "Map legend" });
    expect(legend).toHaveTextContent("Hawker Centres");
    expect(legend).toHaveTextContent("Parks@SG");
    expect(legend).not.toHaveTextContent("Bus Stops");
    expect(screen.getByRole("button", { name: "Show Parks@SG" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Getting around" }));
    expect(legend).toHaveTextContent("Bus Stops");
    expect(legend).toHaveTextContent("Taxi Stands");
    expect(legend).toHaveTextContent("MRT/LRT");
    expect(legend).not.toHaveTextContent("Parks@SG");
    expect(screen.getByRole("button", { name: "Show Bus Stops" })).toBeInTheDocument();
    expect(screen.getByText("Bishan Interchange")).toBeInTheDocument();
    expect(screen.getByText("52 · Towards Bedok")).toBeInTheDocument();
    expect(screen.getByText("4 min · 16 min")).toBeInTheDocument();
  });
});
