import { describe, expect, it } from "vitest";
import { resolveMapCentre, SINGAPORE_MAP_CENTRE } from "../utils/map";

describe("map centre", () => {
  it("keeps an explicit centre instead of following marker order", () => {
    expect(resolveMapCentre([1.29, 103.85])).toEqual([1.29, 103.85]);
  });

  it("falls back to Singapore instead of the first visible point", () => {
    expect(resolveMapCentre()).toEqual(SINGAPORE_MAP_CENTRE);
  });
});
