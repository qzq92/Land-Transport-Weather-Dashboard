import { describe, expect, it } from "vitest";
import { crowdStationLabel } from "../utils/crowding";

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
