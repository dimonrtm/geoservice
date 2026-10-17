import { describe, expect, it } from "vitest";
import type { Polygon, MultiPolygon } from "geojson";
import {
  vertexMoveBlockReason,
  lineSelectionBlockReason,
} from "./workspaceLineInteraction";
import { workspaceFixture, target } from "@/test/workspaceEditFixture";

const square: Polygon = {
  type: "Polygon",
  coordinates: [
    [
      [0, 0],
      [10, 0],
      [10, 10],
      [0, 10],
      [0, 0],
    ],
  ],
};
const line = (middle: [number, number]) => ({
  type: "LineString" as const,
  coordinates: [[1, 1], middle, [9, 1]] as [number, number][],
});
describe("workspace line constraints", () => {
  it("accepts interior, boundary and straight segments without mutating input", () => {
    for (const xy of [
      [5, 5],
      [5, 10],
      [5, 1],
    ] as [number, number][]) {
      const geometry = line(xy);
      const before = JSON.stringify(geometry);
      expect(vertexMoveBlockReason(geometry, square)).toBeNull();
      expect(JSON.stringify(geometry)).toBe(before);
    }
  });
  it("rejects outside, zero segments, backtracking and nonfinite coordinates", () => {
    for (const xy of [
      [5, 11],
      [1, 1],
      [9, 1],
      [0, 1],
      [NaN, 2],
    ] as [number, number][]) {
      expect(vertexMoveBlockReason(line(xy), square)).not.toBeNull();
    }
  });
  it("checks full segments, holes and concavity rather than only vertices", () => {
    const hole: Polygon = {
      ...square,
      coordinates: [
        ...square.coordinates,
        [
          [3, 3],
          [4, 3],
          [4, 4],
          [3, 4],
          [3, 3],
        ],
      ],
    };
    expect(vertexMoveBlockReason(line([5, 5]), hole)).not.toBeNull();
    expect(vertexMoveBlockReason(line([5, 2]), hole)).toBeNull();
    const concave: Polygon = {
      type: "Polygon",
      coordinates: [
        [
          [0, 0],
          [10, 0],
          [10, 10],
          [6, 10],
          [6, 3],
          [4, 3],
          [4, 10],
          [0, 10],
          [0, 0],
        ],
      ],
    };
    expect(vertexMoveBlockReason(line([2, 8]), concave)).not.toBeNull();
  });
  it("checks union coverage for MultiPolygon and permits boundary segments", () => {
    const aoi: MultiPolygon = {
      type: "MultiPolygon",
      coordinates: [
        [
          [
            [0, 0],
            [4, 0],
            [4, 10],
            [0, 10],
            [0, 0],
          ],
        ],
        [
          [
            [6, 0],
            [10, 0],
            [10, 10],
            [6, 10],
            [6, 0],
          ],
        ],
      ],
    };
    expect(vertexMoveBlockReason(line([2, 5]), aoi)).not.toBeNull();
    expect(
      vertexMoveBlockReason(
        {
          type: "LineString",
          coordinates: [
            [0, 0],
            [5, 0],
            [10, 0],
          ],
        },
        square,
      ),
    ).toBeNull();
  });
  it("uses feature semantics and exactly one internal vertex, respecting changeSet", () => {
    const ws = workspaceFixture();
    const feature = ws.workOrder.editVersion.features.features[0]!;
    feature.properties = { featureType: "line", operation: "unchanged" };
    expect(lineSelectionBlockReason(ws, target.featureId)).toBeNull();
    feature.properties.operation = "created";
    expect(lineSelectionBlockReason(ws, target.featureId)).not.toBeNull();
    feature.properties.operation = "unchanged";
    feature.geometry = {
      type: "LineString",
      coordinates: [
        [1, 1],
        [2, 2],
        [3, 2],
        [4, 1],
      ],
    };
    expect(lineSelectionBlockReason(ws, target.featureId)).not.toBeNull();
    const persisted = workspaceFixture(true);
    persisted.workOrder.editVersion.features.features[0]!.properties = {
      featureType: "line",
      operation: "updated",
    };
    persisted.workOrder.editVersion.changeSet!.featureId = "different";
    expect(
      lineSelectionBlockReason(persisted, target.featureId),
    ).not.toBeNull();
  });
});
