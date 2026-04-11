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

  it("refetches expired tiles after ttl", async () => {
    let now = 1_000;
    const cache = useFeatureTileCache({
      ttlMs: 100,
      now: () => now,
    });
    const layer = makeLayer();
    const tile = makeTile("13:1:1");

    fetchLayerFeaturesByBbox
      .mockResolvedValueOnce(makeFeatureCollection(["a"]))
      .mockResolvedValueOnce(makeFeatureCollection(["b"]));

    await cache.loadTiles({ layer, tiles: [tile], limit: 500 });
    now += 50;
    await cache.loadTiles({ layer, tiles: [tile], limit: 500 });
    now += 60;
    const result = await cache.loadTiles({ layer, tiles: [tile], limit: 500 });

    expect(fetchLayerFeaturesByBbox).toHaveBeenCalledTimes(2);
    expect(
      result.featureCollection.features.map((feature) => feature.id),
    ).toEqual(["b"]);
  });

  it("removes deleted feature from visible cache without refetch", async () => {
    const cache = useFeatureTileCache();
    const layer = makeLayer();
    const tiles = [makeTile("13:1:1"), makeTile("13:1:2", 2)];

    fetchLayerFeaturesByBbox
      .mockResolvedValueOnce(makeFeatureCollection(["shared", "a"]))
      .mockResolvedValueOnce(makeFeatureCollection(["shared", "b"]));

    await cache.loadTiles({ layer, tiles, limit: 500 });
    cache.removeFeature(layer.id, "shared");

    const result = cache.buildVisibleFeatureCollection(
      layer.id,
      tiles.map((tile) => tile.key),
    );

    expect(result.features.map((feature) => feature.id).sort()).toEqual([
      "a",
      "b",
    ]);
  });

  it("invalidates tiles containing patched feature and refetches them", async () => {
    const cache = useFeatureTileCache();
    const layer = makeLayer();
    const tiles = [makeTile("13:1:1"), makeTile("13:1:2", 2)];

    fetchLayerFeaturesByBbox
      .mockResolvedValueOnce(makeFeatureCollection(["shared", "a"]))
      .mockResolvedValueOnce(makeFeatureCollection(["shared", "b"]))
      .mockResolvedValueOnce(makeFeatureCollection(["shared", "patched"]))
      .mockResolvedValueOnce(makeFeatureCollection(["shared", "patched"]));

    await cache.loadTiles({ layer, tiles, limit: 500 });
    cache.invalidateFeature(layer.id, "shared");
    const afterInvalidation = cache.buildVisibleFeatureCollection(
      layer.id,
      tiles.map((tile) => tile.key),
    );

    expect(afterInvalidation.features).toEqual([]);

    const reloaded = await cache.loadTiles({
      layer,
      tiles,
      limit: 500,
    });

    expect(fetchLayerFeaturesByBbox).toHaveBeenCalledTimes(4);
    expect(
      reloaded.featureCollection.features.map((feature) => feature.id).sort(),
    ).toEqual(["patched", "shared"]);
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

function makeLayer(): LayerDto {
  return {
    id: "layer-1",
    name: "Layer 1",
    title: "Layer 1",
    geometryType: "Polygon",
    srid: 4326,
  };
}

function makeTile(key: string, y = 1): TileDescriptor {
  return {
    key,
    bbox: [70, 52 + (y - 1) * 0.05, 70.05, 52.05 + (y - 1) * 0.05],
    zoom: 13,
    x: 1,
    y,
    step: 0.05,
  };
}
