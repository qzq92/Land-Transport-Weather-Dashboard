import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import EnvironmentPage from "../pages/EnvironmentPage";

vi.mock("../api/queries", () => ({
  useEnvironment: () => ({
    isPending: false,
    isFetching: false,
    error: null,
    data: {
      data: {
        metrics: [],
        regions: [],
        uv_index: [],
        clusters: [
          {
            id: "zika-1",
            disease: "zika",
            location: "Yishun Street 11",
            cases: 2,
            latitude: 1.43,
            longitude: 103.83,
          },
          {
            id: "dengue-1",
            disease: "dengue",
            location: "Bedok North",
            cases: 12,
            latitude: 1.33,
            longitude: 103.93,
          },
        ],
      },
    },
    refetch: () => undefined,
  }),
}));

vi.mock("../components/MapView", () => ({
  MapView: () => <div data-testid="environment-map" />,
}));

vi.mock("../components/TimeSeriesChart", () => ({
  TimeSeriesChart: () => <div data-testid="uv-chart" />,
}));

describe("environment cluster lists", () => {
  it("shows dengue and zika cluster lists without enabling map layers", () => {
    render(<EnvironmentPage />);

    expect(
      screen.getByRole("heading", { name: "Zika clusters" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Dengue clusters" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Yishun Street 11")).toBeInTheDocument();
    expect(screen.getByText("Bedok North")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Show Zika clusters" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(
      screen.getByRole("button", { name: "Show Dengue clusters" }),
    ).toHaveAttribute("aria-pressed", "false");
  });

  it("keeps cluster lists visible after map layers are toggled", async () => {
    const user = userEvent.setup();
    render(<EnvironmentPage />);

    await user.click(screen.getByRole("button", { name: "Show Zika clusters" }));
    await user.click(screen.getByRole("button", { name: "Show Dengue clusters" }));
    await user.click(screen.getByRole("button", { name: "Show Zika clusters" }));
    await user.click(screen.getByRole("button", { name: "Show Dengue clusters" }));

    expect(
      screen.getByRole("heading", { name: "Zika clusters" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Dengue clusters" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Yishun Street 11")).toBeInTheDocument();
    expect(screen.getByText("Bedok North")).toBeInTheDocument();
  });
});
