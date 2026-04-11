import { describe, expect, it } from "vitest";

import {
  clonePolygonGeometry,
  isFeatureGeometry,
  validatePolygonGeometry,
  type PolygonGeometry,
} from "@/contracts/geojson";

describe("geojson contracts", () => {
  it("accepts valid polygon geometry", () => {
    const polygon: PolygonGeometry = {
      type: "Polygon",
      coordinates: [
        [
          [10, 10],
          [20, 10],
          [20, 20],
          [10, 10],
        ],
      ],
    };

    expect(isFeatureGeometry(polygon)).toBe(true);
    expect(validatePolygonGeometry(polygon)).toEqual({
      ok: true,
      value: polygon,
    });
  });

  it("clones polygon geometry deeply", () => {
    const polygon: PolygonGeometry = {
      type: "Polygon",
      coordinates: [
        [
          [10, 10],
          [20, 10],
          [20, 20],
          [10, 10],
        ],
      ],
    };

    const cloned = clonePolygonGeometry(polygon);
    if (!cloned.coordinates[0]) {
      throw new Error("Expected polygon ring to exist");
    }
    cloned.coordinates[0][0] = [99, 99];

    expect(polygon.coordinates[0]?.[0]).toEqual([10, 10]);
  });

  it("rejects polygon with open ring", () => {
    const polygon: PolygonGeometry = {
      type: "Polygon",
      coordinates: [
        [
          [10, 10],
          [20, 10],
          [20, 20],
          [10, 20],
        ],
      ],
    };

    expect(validatePolygonGeometry(polygon)).toEqual({
      ok: false,
      code: "RING_NOT_CLOSED",
      message: "Все кольца полигона должны быть замкнутыми",
    });
  });
});
