import { ref, type ShallowRef } from "vue";
import { AxiosError } from "axios";
import { fetchLayerFeatureById, HttpError } from "@/api/layers";
import type { LayerDto } from "@/contracts/api";
import type { ApiFeature } from "@/contracts/geojson";
import { useFeatureTileCache } from "@/composables/map/useFeatureTileCache";
import { getTilesForViewport } from "@/map/feature-grid";
import {
  formatBbox,
  getCurrentBbox,
  isValidBbox,
  setSourceData,
} from "@/map/maplibrelayers";
import type { Map } from "maplibre-gl";

const DEBOUNCE_MS = 250;
const MIN_ZOOM = 8;
const FEATURE_LIMIT = 500;

export function useFeatureLoading(
  map: ShallowRef<Map | null>,
  onHistoryLimit: () => void,
  maxHistoryEntries = 4096,
) {
  const labelText = ref("Карта загружается...");
  const isLoadingFeature = ref(false);
  const featuresAbortController = ref<AbortController | null>(null);
  const tileCache = useFeatureTileCache();
  let subscriptionGeneration = 0;
  let moveTimer: ReturnType<typeof setTimeout> | null = null;

  async function reloadFeatures(
    layer: LayerDto,
    options: { force?: boolean } = {},
  ): Promise<void> {
    const zoom = map.value?.getZoom();
    if (zoom !== undefined && zoom < MIN_ZOOM) {
      labelText.value = `Zoom ${zoom.toFixed(1)}: приблизьтесь к ${MIN_ZOOM}`;
      if (options.force) throw new Error("Ожидание подходящего масштаба");
      return;
    }

    const bbox = getCurrentBbox(map.value);
    if (!isValidBbox(bbox)) {
      labelText.value = "Bbox невалиден на клиенте";
      if (options.force) throw new Error(labelText.value);
      return;
    }

    stopPendingFeatureWork();
    isLoadingFeature.value = true;
    labelText.value = "Загружаю объекты...";

    const controller = new AbortController();
    featuresAbortController.value = controller;
    const visibleTiles = getVisibleTiles();
    const visibleTileKeys = visibleTiles.map((tile) => tile.key);

    try {
      const { fetchedTiles, requestedTiles } = await tileCache.loadTiles({
        layer,
        tiles: visibleTiles,
        limit: FEATURE_LIMIT,
        signal: controller.signal,
        force: options.force === true,
        waitForAllPages: options.force,
        onBackgroundChange: () => {
          if (
            controller.signal.aborted ||
            featuresAbortController.value !== controller
          ) {
            return;
          }
          syncSourceForTileKeys(layer, visibleTileKeys);
          updateLoadedLabel(layer, bbox, visibleTileKeys, requestedTiles, {
            fetchedTiles,
            background: true,
          });
        },
      });

      if (
        controller.signal.aborted ||
        controller !== featuresAbortController.value
      ) {
        if (options.force) throw new Error("Вид карты изменился");
        return;
      }
      syncSourceForTileKeys(layer, visibleTileKeys);
      updateLoadedLabel(layer, bbox, visibleTileKeys, requestedTiles, {
        fetchedTiles,
      });
    } catch (err: unknown) {
      if (options.force) throw err;
      if (controller.signal.aborted) return;
      if (err instanceof AxiosError && err.code === "ERR_CANCELED") {
        return;
      }
      if (err instanceof HttpError) {
        if (err.status === 404) {
          labelText.value = "Слой не найден (404)";
        } else if (err.status === 422) {
          labelText.value = "Невалидный bbox (422)";
        } else {
          labelText.value = `Ошибка загрузки. HTTP ${err.status}`;
        }
      } else {
        labelText.value = "Сетевая или неизвестная ошибка";
      }
    } finally {
      if (controller === featuresAbortController.value)
        isLoadingFeature.value = false;
    }
  }

  function createMoveEndHandler(
    getActiveLayer: () => LayerDto | null,
  ): () => void {
    return () => {
      if (moveTimer !== null) {
        clearTimeout(moveTimer);
      }

      moveTimer = setTimeout(async () => {
        const currentLayer = getActiveLayer();
        if (!currentLayer) {
          return;
        }
        await reloadFeatures(currentLayer);
      }, DEBOUNCE_MS);
    };
  }

  function clearLayerCache(layerId: string): void {
    subscriptionGeneration++;
    stopPendingFeatureWork();
    tileCache.clearLayer(layerId);
  }

  async function applyPatchedFeature(
    layer: LayerDto,
    feature: ApiFeature,
    verifyUnknown = false,
  ): Promise<void> {
    const generation = subscriptionGeneration;
    if (verifyUnknown && !tileCache.knownVersion(layer.id, feature.id)) {
      try {
        feature = await fetchLayerFeatureById(layer.id, feature.id);
      } catch (error) {
        if (generation !== subscriptionGeneration) return;
        if (!(error instanceof HttpError && error.status === 404)) throw error;
        // UUID удалённого объекта не переиспользуется.
        applyDeletedFeature(layer, feature.id, Number.POSITIVE_INFINITY);
        return;
      }
    }
    if (generation !== subscriptionGeneration) return;
    tileCache.upsertFeature(layer.id, feature);
    syncVisibleSource(layer);
    checkHistoryLimit(layer.id);
  }

  function checkHistoryLimit(layerId: string) {
    if (tileCache.historySize(layerId) >= maxHistoryEntries) onHistoryLimit();
  }

  function applyDeletedFeature(
    layer: LayerDto,
    featureId: string,
    version: number,
  ): void {
    tileCache.removeFeature(layer.id, featureId, version);
    syncVisibleSource(layer);
    checkHistoryLimit(layer.id);
  }

  function stopPendingFeatureWork(): void {
    featuresAbortController.value?.abort();
    featuresAbortController.value = null;
    if (moveTimer !== null) {
      clearTimeout(moveTimer);
      moveTimer = null;
    }
  }

  return {
    labelText,
    reloadFeatures,
    createMoveEndHandler,
    clearLayerCache,
    getSubscriptionGeneration: () => subscriptionGeneration,
    applyPatchedFeature,
    applyCreatedFeature: applyPatchedFeature,
    applyDeletedFeature,
    stopPendingFeatureWork,
  };

  function getVisibleTiles() {
    const zoom = Math.floor(map.value?.getZoom() ?? MIN_ZOOM);
    const bbox = getCurrentBbox(map.value);
    if (!isValidBbox(bbox)) {
      return [];
    }
    return getTilesForViewport(bbox, zoom);
  }

  function syncVisibleSource(layer: LayerDto): void {
    const visibleTileKeys = getVisibleTiles().map((tile) => tile.key);
    syncSourceForTileKeys(layer, visibleTileKeys);
  }

  function syncSourceForTileKeys(layer: LayerDto, tileKeys: string[]): void {
    const featureCollection = tileCache.buildVisibleFeatureCollection(
      layer.id,
      tileKeys,
    );
    setSourceData(map.value, getSourceId(layer), featureCollection);
  }

  function updateLoadedLabel(
    layer: LayerDto,
    bbox: [number, number, number, number],
    tileKeys: string[],
    requestedTiles: number,
    options: { fetchedTiles?: number; background?: boolean } = {},
  ): void {
    const featureCollection = tileCache.buildVisibleFeatureCollection(
      layer.id,
      tileKeys,
    );
    const featureCount = featureCollection.features.length;
    const truncatedTiles = tileCache.getVisibleTruncatedTileCount(
      layer.id,
      tileKeys,
    );
    const backgroundStatus =
      truncatedTiles > 0
        ? ` | background: ${truncatedTiles} pending`
        : options.background
          ? " | background: synced"
          : "";

    if (featureCount === 0) {
      labelText.value = `Layer: ${layer.title} | bbox: ${formatBbox(bbox)} | tiles: ${requestedTiles} | truncated: ${truncatedTiles}${backgroundStatus} | empty | limit ${FEATURE_LIMIT}`;
      return;
    }

    const fetchedChunk =
      options.fetchedTiles !== undefined
        ? ` | fetched: ${options.fetchedTiles}`
        : "";
    labelText.value = `Layer: ${layer.title} | bbox: ${formatBbox(bbox)} | features: ${featureCount} | tiles: ${requestedTiles}${fetchedChunk} | cached: ${tileCache.getReadyTileCount(layer.id)} | truncated: ${truncatedTiles}${backgroundStatus} | limit ${FEATURE_LIMIT}`;
  }
}

function getSourceId(layer: LayerDto): string {
  return `src:${layer.id}`;
}
