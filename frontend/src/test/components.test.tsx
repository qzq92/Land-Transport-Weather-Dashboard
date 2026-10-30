import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CheckpointCameraFeeds } from "../components/CheckpointCameraFeeds";
import { DataPanel } from "../components/DataPanel";
import { MetricCard } from "../components/MetricCard";
import { QueryState } from "../components/QueryState";

describe("shared dashboard components", () => {
  it("renders an accessible metric with units and trend", () => {
    render(
      <MetricCard
        id="temperature"
        label="Temperature"
        value={31}
        unit="°C"
        trend={-2}
        status="good"
      />,
    );

    expect(screen.getByText("Temperature")).toBeInTheDocument();
    expect(screen.getByText("31")).toHaveTextContent("31°C");
    expect(screen.getByLabelText("Down 2%")).toBeInTheDocument();
  });

  it("associates panel content with its heading", () => {
    render(
      <DataPanel title="Active notices" eyebrow="Live">
        <p>No disruptions</p>
      </DataPanel>,
    );

    expect(
      screen.getByRole("heading", { name: "Active notices" }),
    ).toBeInTheDocument();
    expect(screen.getByText("No disruptions")).toBeInTheDocument();
  });

  it("shows a retry action for failed requests", () => {
    render(
      <QueryState
        loading={false}
        error={new Error("Network unavailable")}
        onRetry={() => undefined}
      >
        <p>Hidden content</p>
      </QueryState>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Network unavailable");
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
    expect(screen.queryByText("Hidden content")).not.toBeInTheDocument();
  });

  it("labels cached data when the API reports it as stale", () => {
    render(
      <QueryState loading={false} error={null} meta={{ stale: true }}>
        <p>Cached conditions</p>
      </QueryState>,
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Showing the latest cached data",
    );
    expect(screen.getByText("Cached conditions")).toBeInTheDocument();
  });

  it("keeps both checkpoint camera slots visible when a feed is unavailable", () => {
    render(
      <CheckpointCameraFeeds
        cameras={[
          {
            id: "2701",
            name: "2701",
            latitude: 1.45,
            longitude: 103.77,
            image_url: "https://example.test/causeway.jpg",
            captured_at: "2026-10-30T14:00:00Z",
          },
        ]}
      />,
    );

    expect(
      screen.getByRole("img", { name: "Traffic camera view at Causeway" }),
    ).toHaveAttribute("src", "https://example.test/causeway.jpg");
    expect(screen.getByText("Second Link")).toBeInTheDocument();
    expect(screen.getByText("Image not available")).toBeInTheDocument();
  });
});
