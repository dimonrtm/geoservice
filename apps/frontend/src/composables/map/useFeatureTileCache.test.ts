import { beforeEach, describe, expect, it, vi } from "vitest";

import { useFeatureTileCache } from "@/composables/map/useFeatureTileCache";
import type { ApiFeatureCollectionResponse, LayerDto } from "@/contracts/api";
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
    const layer = makeLayer();
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

  it("returns the first page immediately and completes the tile in background", async () => {
    const cache = useFeatureTileCache();
    const layer = makeLayer();
    const tile = makeTile("13:1:1");
    const onBackgroundChange = vi.fn();
    const deferredPage = createDeferred<ApiFeatureCollectionResponse>();

    fetchLayerFeaturesByBbox
      .mockResolvedValueOnce(
        makeFeatureCollection(["a"], {
          truncated: true,
          nextCursor: "cursor-1",
        }),
      )
      .mockReturnValueOnce(deferredPage.promise);

    const result = await cache.loadTiles({
      layer,
      tiles: [tile],
      limit: 1,
      onBackgroundChange,
    });

    expect(fetchLayerFeaturesByBbox).toHaveBeenCalledTimes(2);
    expect(fetchLayerFeaturesByBbox).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({ afterId: null }),
    );
    expect(fetchLayerFeaturesByBbox).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({ afterId: "cursor-1" }),
    );
    expect(
      result.featureCollection.features.map((feature) => feature.id),
    ).toEqual(["a"]);
    expect(cache.getVisibleTruncatedTileCount(layer.id, [tile.key])).toBe(1);
    expect(onBackgroundChange).not.toHaveBeenCalled();

    deferredPage.resolve(makeFeatureCollection(["b"]));

    await vi.waitFor(() => {
      expect(onBackgroundChange).toHaveBeenCalledTimes(1);
    });

    const merged = cache.buildVisibleFeatureCollection(layer.id, [tile.key]);
    expect(merged.features.map((feature) => feature.id)).toEqual(["a", "b"]);
    expect(cache.getVisibleTruncatedTileCount(layer.id, [tile.key])).toBe(0);
  });

  it("reuses ready tiles without a second request", async () => {
    const cache = useFeatureTileCache();
    const layer = makeLayer();
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

  it("keeps truncated count while background pages are still loading", async () => {
    const cache = useFeatureTileCache();
    const layer = makeLayer();
    const tile = makeTile("13:1:1");
    const deferredPage = createDeferred<ApiFeatureCollectionResponse>();

    fetchLayerFeaturesByBbox
      .mockResolvedValueOnce(
        makeFeatureCollection(["a"], {
          truncated: true,
          nextCursor: "cursor-a",
        }),
      )
      .mockReturnValueOnce(deferredPage.promise);

    await cache.loadTiles({ layer, tiles: [tile], limit: 1 });

    expect(cache.getVisibleTruncatedTileCount(layer.id, [tile.key])).toBe(1);

    deferredPage.resolve(makeFeatureCollection(["a-2"]));

    await vi.waitFor(() => {
      expect(cache.getVisibleTruncatedTileCount(layer.id, [tile.key])).toBe(0);
    });
  });
});

function makeFeatureCollection(
  ids: string[],
  options: {
    truncated?: boolean;
    limit?: number;
    nextCursor?: string | null;
  } = {},
): ApiFeatureCollectionResponse {
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
    meta: {
      bbox: [10, 10, 20, 20],
      limit: options.limit ?? 500,
      returned: ids.length,
      truncated: options.truncated ?? false,
      sort: "id:asc",
      next_cursor: options.nextCursor ?? null,
    },
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

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}
