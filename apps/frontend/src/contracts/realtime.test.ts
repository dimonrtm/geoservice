import { describe, expect, it } from "vitest";
import {
  isLayerRealtimeEvent,
  parseLayerRealtimeEvent,
} from "@/contracts/realtime";

const feature = {
  type: "Feature",
  id: "feature-1",
  version: 3,
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [10, 10],
        [11, 10],
        [11, 11],
        [10, 10],
      ],
    ],
  },
  properties: {
    name: "test",
  },
};

describe("realtime contracts", () => {
  it("parses connected events", () => {
    expect(
      parseLayerRealtimeEvent(
        JSON.stringify({
          type: "connected",
          layerId: "layer-1",
        }),
      ),
    ).toEqual({
      type: "connected",
      layerId: "layer-1",
    });
  });

  it("accepts feature update events with full feature payload", () => {
    expect(
      isLayerRealtimeEvent({
        type: "feature_updated",
        eventId: "evt_123",
        occurredAt: "2026-04-14T10:20:30Z",
        layerId: "layer-1",
        feature,
      }),
    ).toBe(true);
  });

  it("rejects invalid realtime payloads", () => {
    expect(
      isLayerRealtimeEvent({
        type: "feature_deleted",
        eventId: "evt_123",
        occurredAt: "2026-04-14T10:20:30Z",
        layerId: "layer-1",
      }),
    ).toBe(false);
  });
});
