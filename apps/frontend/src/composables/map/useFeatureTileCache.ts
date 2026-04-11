import { fetchLayerFeaturesByBbox } from "@/api/layers";
import type { LayerDto } from "@/contracts/api";
import type { ApiFeature, ApiFeatureCollection } from "@/contracts/geojson";
import type {
  FeatureIndex,
  TileDescriptor,
  TileEntry,
  TileIndex,
  TileKey,
} from "@/contracts/map-cache";

type LayerTileCache = {
  features: FeatureIndex;
  tiles: TileIndex;
  inflight: Map<TileKey, Promise<void>>;
};

type LoadTilesArgs = {
  layer: LayerDto;
  tiles: TileDescriptor[];
  limit: number;
  signal?: AbortSignal;
  force?: boolean;
};

type FeatureTileCacheOptions = {
  ttlMs?: number;
  now?: () => number;
};

const DEFAULT_TILE_TTL_MS = 5 * 60 * 1000;

const emptyFeatureCollection: ApiFeatureCollection = {
  type: "FeatureCollection",
  features: [],
};

export function useFeatureTileCache(options: FeatureTileCacheOptions = {}) {
  const ttlMs = options.ttlMs ?? DEFAULT_TILE_TTL_MS;
  const now = options.now ?? Date.now;
  const layerCaches = new Map<string, LayerTileCache>();

  async function loadTiles(args: LoadTilesArgs): Promise<{
    featureCollection: ApiFeatureCollection;
    requestedTiles: number;
    fetchedTiles: number;
  }> {
    const cache = getLayerCache(args.layer.id);
    const tileKeys = args.tiles.map((tile) => tile.key);
    const tilesToFetch = args.tiles.filter((tile) =>
      shouldFetchTile(cache, tile.key, args.force === true, ttlMs, now),
    );

    await Promise.all(
      tilesToFetch.map((tile) =>
        loadSingleTile(cache, {
          layer: args.layer,
          tile,
          limit: args.limit,
          signal: args.signal,
          now,
        }),
      ),
    );

    return {
      featureCollection: buildFeatureCollection(cache, tileKeys),
      requestedTiles: tileKeys.length,
      fetchedTiles: tilesToFetch.length,
    };
  }

  function clearLayer(layerId: string): void {
    layerCaches.delete(layerId);
  }

  function invalidateTiles(layerId: string, tileKeys: TileKey[]): void {
    const cache = layerCaches.get(layerId);
    if (!cache) {
      return;
    }

    for (const tileKey of tileKeys) {
      cache.tiles.delete(tileKey);
    }
  }

  function invalidateFeature(layerId: string, featureId: string): void {
    const cache = layerCaches.get(layerId);
    if (!cache) {
      return;
    }

    for (const [tileKey, entry] of cache.tiles.entries()) {
      if (!entry.data?.featureIds.includes(featureId)) {
        continue;
      }
      cache.tiles.delete(tileKey);
    }
  }

  function upsertFeature(layerId: string, feature: ApiFeature): void {
    const cache = getLayerCache(layerId);
    cache.features.set(feature.id, feature);
  }

  function removeFeature(layerId: string, featureId: string): void {
    const cache = layerCaches.get(layerId);
    if (!cache) {
      return;
    }

    cache.features.delete(featureId);
    for (const [tileKey, entry] of cache.tiles.entries()) {
      if (!entry.data) {
        continue;
      }

      const nextFeatureIds = entry.data.featureIds.filter(
        (id) => id !== featureId,
      );
      if (nextFeatureIds.length === entry.data.featureIds.length) {
        continue;
      }

      cache.tiles.set(tileKey, {
        ...entry,
        data: {
          ...entry.data,
          featureIds: nextFeatureIds,
        },
      });
    }
  }

  function buildVisibleFeatureCollection(
    layerId: string,
    tileKeys: TileKey[],
  ): ApiFeatureCollection {
    const cache = getLayerCache(layerId);
    return buildFeatureCollection(cache, tileKeys);
  }

  function getReadyTileCount(layerId: string): number {
    const cache = layerCaches.get(layerId);
    if (!cache) {
      return 0;
    }

    let readyCount = 0;
    for (const entry of cache.tiles.values()) {
      if (entry.state === "ready") {
        readyCount++;
      }
    }
    return readyCount;
  }

  return {
    loadTiles,
    clearLayer,
    invalidateTiles,
    invalidateFeature,
    upsertFeature,
    removeFeature,
    buildVisibleFeatureCollection,
    getReadyTileCount,
  };

  function getLayerCache(layerId: string): LayerTileCache {
    let cache = layerCaches.get(layerId);
    if (!cache) {
      cache = {
        features: new Map<string, ApiFeature>(),
        tiles: new Map<TileKey, TileEntry>(),
        inflight: new Map<TileKey, Promise<void>>(),
      };
      layerCaches.set(layerId, cache);
    }
    return cache;
  }
}

function shouldFetchTile(
  cache: LayerTileCache,
  tileKey: TileKey,
  force: boolean,
  ttlMs: number,
  now: () => number,
): boolean {
  if (force) {
    return true;
  }

  const entry = cache.tiles.get(tileKey);
  return !entry || entry.state !== "ready" || isExpired(entry, ttlMs, now);
}

function isExpired(
  entry: TileEntry,
  ttlMs: number,
  now: () => number,
): boolean {
  if (!entry.data) {
    return true;
  }
  return now() - entry.data.loadedAt >= ttlMs;
}

async function loadSingleTile(
  cache: LayerTileCache,
  args: {
    layer: LayerDto;
    tile: TileDescriptor;
    limit: number;
    signal?: AbortSignal;
    now: () => number;
  },
): Promise<void> {
  const existingRequest = cache.inflight.get(args.tile.key);
  if (existingRequest) {
    await existingRequest;
    return;
  }

  cache.tiles.set(args.tile.key, { state: "loading", data: null });

  const request = (async () => {
    try {
      const featureCollection = await fetchLayerFeaturesByBbox({
        layerId: args.layer.id,
        bbox: args.tile.bbox,
        limit: args.limit,
        signal: args.signal,
      });

      const featureIds = persistTileFeatures(cache.features, featureCollection);
      cache.tiles.set(args.tile.key, {
        state: "ready",
        data: {
          key: args.tile.key,
          bbox: args.tile.bbox,
          loadedAt: args.now(),
          featureIds,
        },
      });
    } catch (error: unknown) {
      cache.tiles.set(args.tile.key, {
        state: "error",
        data: null,
        error: error instanceof Error ? error.message : "Tile load failed",
      });
      throw error;
    } finally {
      cache.inflight.delete(args.tile.key);
    }
  })();

  cache.inflight.set(args.tile.key, request);
  await request;
}

function buildFeatureCollection(
  cache: LayerTileCache,
  tileKeys: TileKey[],
): ApiFeatureCollection {
  if (tileKeys.length === 0) {
    return emptyFeatureCollection;
  }

  const visibleFeatureIds = new Set<string>();
  for (const tileKey of tileKeys) {
    const tile = cache.tiles.get(tileKey);
    if (!tile || tile.state !== "ready" || !tile.data) {
      continue;
    }
    for (const featureId of tile.data.featureIds) {
      visibleFeatureIds.add(featureId);
    }
  }

  const features: ApiFeature[] = [];
  for (const featureId of visibleFeatureIds) {
    const feature = cache.features.get(featureId);
    if (feature) {
      features.push(feature);
    }
  }

  return {
    type: "FeatureCollection",
    features,
  };
}

function persistTileFeatures(
  featureIndex: FeatureIndex,
  featureCollection: ApiFeatureCollection,
): string[] {
  const featureIds = new Set<string>();
  for (const feature of featureCollection.features) {
    featureIndex.set(feature.id, feature);
    featureIds.add(feature.id);
  }
  return [...featureIds];
}
