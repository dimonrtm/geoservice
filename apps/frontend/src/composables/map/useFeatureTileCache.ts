import { fetchLayerFeaturesByBbox } from "@/api/layers";
import type { ApiFeatureCollectionResponse, LayerDto } from "@/contracts/api";
import type { ApiFeature, ApiFeatureCollection } from "@/contracts/geojson";
import type {
  FeatureIndex,
  TileDescriptor,
  TileEntry,
  TileIndex,
  TileKey,
} from "@/contracts/map-cache";

type TileLoadHandle = {
  initial: Promise<void>;
  completion: Promise<boolean>;
};

type LayerTileCache = {
  features: FeatureIndex;
  tiles: TileIndex;
  inflight: Map<TileKey, TileLoadHandle>;
};

type LoadTilesArgs = {
  layer: LayerDto;
  tiles: TileDescriptor[];
  limit: number;
  signal?: AbortSignal;
  force?: boolean;
  onBackgroundChange?: () => void;
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
    const loadHandles = tilesToFetch.map((tile) =>
      loadSingleTile(cache, {
        layer: args.layer,
        tile,
        limit: args.limit,
        signal: args.signal,
        now,
      }),
    );

    await Promise.all(loadHandles.map((handle) => handle.initial));

    for (const handle of loadHandles) {
      void handle.completion
        .then((didBackgroundWork) => {
          if (didBackgroundWork) {
            args.onBackgroundChange?.();
          }
        })
        .catch(() => {
          // Background page loading is best-effort; cache state already stores the failure.
        });
    }

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

  function getVisibleTruncatedTileCount(
    layerId: string,
    tileKeys: TileKey[],
  ): number {
    const cache = layerCaches.get(layerId);
    if (!cache) {
      return 0;
    }

    let truncatedCount = 0;
    for (const tileKey of tileKeys) {
      const entry = cache.tiles.get(tileKey);
      if (entry?.data && entry.data.fullyLoaded === false) {
        truncatedCount++;
      }
    }
    return truncatedCount;
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
    getVisibleTruncatedTileCount,
  };

  function getLayerCache(layerId: string): LayerTileCache {
    let cache = layerCaches.get(layerId);
    if (!cache) {
      cache = {
        features: new Map<string, ApiFeature>(),
        tiles: new Map<TileKey, TileEntry>(),
        inflight: new Map<TileKey, TileLoadHandle>(),
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
  if (cache.inflight.has(tileKey)) {
    return false;
  }

  const entry = cache.tiles.get(tileKey);
  return (
    !entry ||
    entry.state !== "ready" ||
    entry.data?.fullyLoaded === false ||
    isExpired(entry, ttlMs, now)
  );
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

function loadSingleTile(
  cache: LayerTileCache,
  args: {
    layer: LayerDto;
    tile: TileDescriptor;
    limit: number;
    signal?: AbortSignal;
    now: () => number;
  },
): TileLoadHandle {
  const existingRequest = cache.inflight.get(args.tile.key);
  if (existingRequest) {
    return existingRequest;
  }

  cache.tiles.set(args.tile.key, { state: "loading", data: null });

  let resolveInitial!: () => void;
  let rejectInitial!: (reason?: unknown) => void;
  let initialSettled = false;

  const initial = new Promise<void>((resolve, reject) => {
    resolveInitial = () => {
      initialSettled = true;
      resolve();
    };
    rejectInitial = (reason?: unknown) => {
      initialSettled = true;
      reject(reason);
    };
  });

  const completion = (async () => {
    let didBackgroundWork = false;
    let currentEntry: TileEntry | null = null;

    try {
      const featureIds = new Set<string>();
      const seenCursors = new Set<string>();
      let totalReturned = 0;

      const firstPage = await fetchLayerFeaturesByBbox({
        layerId: args.layer.id,
        bbox: args.tile.bbox,
        limit: args.limit,
        afterId: null,
        signal: args.signal,
      });

      totalReturned += firstPage.features.length;
      persistTileFeatures(cache.features, firstPage, featureIds);

      currentEntry = {
        state: "ready",
        data: {
          key: args.tile.key,
          bbox: args.tile.bbox,
          loadedAt: args.now(),
          featureIds: [...featureIds],
          meta: firstPage.meta,
          fullyLoaded: firstPage.meta.next_cursor === null,
        },
      };
      cache.tiles.set(args.tile.key, currentEntry);
      resolveInitial();

      let nextCursor = firstPage.meta.next_cursor;
      let currentMeta = firstPage.meta;

      while (nextCursor) {
        if (seenCursors.has(nextCursor)) {
          throw new Error(`Cursor loop detected for tile ${args.tile.key}`);
        }
        seenCursors.add(nextCursor);
        didBackgroundWork = true;

        const page = await fetchLayerFeaturesByBbox({
          layerId: args.layer.id,
          bbox: args.tile.bbox,
          limit: args.limit,
          afterId: nextCursor,
          signal: args.signal,
        });

        totalReturned += page.features.length;
        persistTileFeatures(cache.features, page, featureIds);
        currentMeta = page.meta;
        nextCursor = page.meta.next_cursor;

        currentEntry = {
          state: "ready",
          data: {
            key: args.tile.key,
            bbox: args.tile.bbox,
            loadedAt: args.now(),
            featureIds: [...featureIds],
            meta: {
              bbox: currentMeta.bbox,
              limit: currentMeta.limit,
              returned: totalReturned,
              truncated: nextCursor !== null,
              sort: currentMeta.sort,
              next_cursor: nextCursor,
            },
            fullyLoaded: nextCursor === null,
          },
        };
        cache.tiles.set(args.tile.key, currentEntry);
      }

      return didBackgroundWork;
    } catch (error: unknown) {
      if (!initialSettled) {
        rejectInitial(error);
      }

      const errorMessage =
        error instanceof Error ? error.message : "Tile load failed";
      if (currentEntry?.data) {
        cache.tiles.set(args.tile.key, {
          ...currentEntry,
          error: errorMessage,
        });
      } else {
        cache.tiles.set(args.tile.key, {
          state: "error",
          data: null,
          error: errorMessage,
        });
      }
      throw error;
    } finally {
      cache.inflight.delete(args.tile.key);
    }
  })();

  const handle: TileLoadHandle = { initial, completion };
  cache.inflight.set(args.tile.key, handle);
  return handle;
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
  featureCollection: ApiFeatureCollectionResponse,
  featureIds: Set<string>,
): void {
  for (const feature of featureCollection.features) {
    featureIndex.set(feature.id, feature);
    featureIds.add(feature.id);
  }
}
