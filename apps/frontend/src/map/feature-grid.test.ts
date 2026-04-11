import { describe, expect, it } from "vitest";

import { getGridStepForZoom, getTilesForViewport } from "@/map/feature-grid";

describe("feature grid", () => {
  it("does not create tiles below minimum zoom", () => {
    expect(getGridStepForZoom(8)).toBe(0);
    expect(getTilesForViewport([70, 52, 70.1, 52.1], 8)).toEqual([]);
  });

  it("splits viewport into deterministic tile keys", () => {
    const tiles = getTilesForViewport([70.01, 52.01, 70.23, 52.18], 13);

    expect(tiles.map((tile) => tile.key)).toEqual([
      "13:5000:2840",
      "13:5000:2841",
      "13:5000:2842",
      "13:5000:2843",
      "13:5001:2840",
      "13:5001:2841",
      "13:5001:2842",
      "13:5001:2843",
      "13:5002:2840",
      "13:5002:2841",
      "13:5002:2842",
      "13:5002:2843",
      "13:5003:2840",
      "13:5003:2841",
      "13:5003:2842",
      "13:5003:2843",
      "13:5004:2840",
      "13:5004:2841",
      "13:5004:2842",
      "13:5004:2843",
    ]);
  });

  it("clamps viewport to valid world bounds", () => {
    const tiles = getTilesForViewport([-190, -95, -179.7, -89.7], 10);

    expect(tiles.length).toBeGreaterThan(0);
    expect(tiles[0]?.bbox[0]).toBeGreaterThanOrEqual(-180);
    expect(tiles[0]?.bbox[1]).toBeGreaterThanOrEqual(-90);
    const lastTile = tiles[tiles.length - 1];
    expect(lastTile?.bbox[2]).toBeLessThanOrEqual(180);
    expect(lastTile?.bbox[3]).toBeLessThanOrEqual(90);
  });
});
