import { beforeEach, describe, expect, it, vi } from "vitest";

import { useFeatureTileCache } from "@/composables/map/useFeatureTileCache";
import type { LayerDto } from "@/contracts/api";
import type { ApiFeatureCollection } from "@/contracts/geojson";
import type { TileDescriptor } from "@/contracts/map-cache";

const fetchLayerFeaturesByBbox = vi.fn();

vi.mock("@/api/layers", () => ({
  fetchLayerFeaturesByBbox: (args: unknown) => fetchLayerFeaturesByBbox(args),
}));

describe("feature tile cache", () => {
  beforeEach(() => {
    fetchLayerFeaturesByBbox.mockReset();
  });

  it("deduplicates features aggregated from multiple tiles", async () => {
    const cache = useFeatureTileCache();
    const layer: LayerDto = {
      id: "layer-1",
      name: "Layer 1",
      title: "Layer 1",
      geometryType: "Polygon",
      srid: 4326,
    };
    const tiles: TileDescriptor[] = [
      {
        key: "13:1:1",
        bbox: [70, 52, 70.05, 52.05],
        zoom: 13,
        x: 1,
        y: 1,
        step: 0.05,
      },
      {
        key: "13:1:2",
        bbox: [70, 52.05, 70.05, 52.1],
        zoom: 13,
        x: 1,
        y: 2,
        step: 0.05,
      },
    ];

    fetchLayerFeaturesByBbox
      .mockResolvedValueOnce(makeFeatureCollection(["shared", "a"]))
      .mockResolvedValueOnce(makeFeatureCollection(["shared", "b"]));

    const result = await cache.loadTiles({
      layer,
      tiles,
      limit: 500,
    });

    expect(fetchLayerFeaturesByBbox).toHaveBeenCalledTimes(2);
    expect(
      result.featureCollection.features.map((feature) => feature.id).sort(),
    ).toEqual(["a", "b", "shared"]);
    expect(cache.getReadyTileCount(layer.id)).toBe(2);
  });

  it("reuses ready tiles without a second request", async () => {
    const cache = useFeatureTileCache();
    const layer: LayerDto = {
      id: "layer-1",
      name: "Layer 1",
      title: "Layer 1",
      geometryType: "Polygon",
      srid: 4326,
    };
    const tile: TileDescriptor = {
      key: "13:1:1",
      bbox: [70, 52, 70.05, 52.05],
      zoom: 13,
      x: 1,
      y: 1,
      step: 0.05,
    };

    fetchLayerFeaturesByBbox.mockResolvedValue(
      makeFeatureCollection(["shared"]),
    );

    await cache.loadTiles({ layer, tiles: [tile], limit: 500 });
    await cache.loadTiles({ layer, tiles: [tile], limit: 500 });

    expect(fetchLayerFeaturesByBbox).toHaveBeenCalledTimes(1);
  });
});

function makeFeatureCollection(ids: string[]): ApiFeatureCollection {
  return {
    type: "FeatureCollection",
    features: ids.map((id) => ({
      type: "Feature",
      id,
      version: 1,
      properties: { name: id },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [10, 10],
            [20, 10],
            [20, 20],
            [10, 10],
          ],
        ],
      },
    })),
  };
}
