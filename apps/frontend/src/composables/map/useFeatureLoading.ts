import { ref, type ShallowRef } from "vue";
import { AxiosError } from "axios";
import { HttpError } from "@/api/layers";
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

export function useFeatureLoading(map: ShallowRef<Map | null>) {
  const labelText = ref("Карта загружается...");
  const isLoadingFeature = ref(false);
  const featuresAbortController = ref<AbortController | null>(null);
  const tileCache = useFeatureTileCache();
  let moveTimer: ReturnType<typeof setTimeout> | null = null;

  async function reloadFeatures(
    layer: LayerDto,
    options: { force?: boolean } = {},
  ): Promise<void> {
    const zoom = map.value?.getZoom();
    if (zoom !== undefined && zoom < MIN_ZOOM) {
      labelText.value = `Zoom ${zoom.toFixed(1)}: приблизьтесь к ${MIN_ZOOM}`;
      return;
    }

    const bbox = getCurrentBbox(map.value);
    if (!isValidBbox(bbox)) {
      labelText.value = "Bbox невалиден на клиенте";
      return;
    }

    stopPendingFeatureWork();
    isLoadingFeature.value = true;
    labelText.value = "Загружаю объекты...";

    const controller = new AbortController();
    featuresAbortController.value = controller;
    const visibleTiles = getVisibleTiles();

    try {
      const { featureCollection, fetchedTiles, requestedTiles } =
        await tileCache.loadTiles({
          layer,
          tiles: visibleTiles,
          limit: FEATURE_LIMIT,
          signal: controller.signal,
          force: options.force === true,
        });

      setSourceData(map.value, getSourceId(layer), featureCollection);
      const count = featureCollection.features.length;
      if (count === 0) {
        labelText.value = `Layer: ${layer.title} | bbox: ${formatBbox(bbox)} | tiles: ${requestedTiles} | empty | limit ${FEATURE_LIMIT}`;
      } else {
        labelText.value = `Layer: ${layer.title} | bbox: ${formatBbox(bbox)} | features: ${count} | tiles: ${requestedTiles} | fetched: ${fetchedTiles} | cached: ${tileCache.getReadyTileCount(layer.id)} | limit ${FEATURE_LIMIT}`;
      }
    } catch (err: unknown) {
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
    tileCache.clearLayer(layerId);
  }

  async function applyPatchedFeature(
    layer: LayerDto,
    feature: ApiFeature,
  ): Promise<void> {
    tileCache.upsertFeature(layer.id, feature);
    tileCache.invalidateFeature(layer.id, feature.id);
    tileCache.invalidateTiles(
      layer.id,
      getVisibleTiles().map((tile) => tile.key),
    );
    await reloadFeatures(layer);
  }

  async function applyCreatedFeature(
    layer: LayerDto,
    feature: ApiFeature,
  ): Promise<void> {
    tileCache.upsertFeature(layer.id, feature);
    tileCache.invalidateTiles(
      layer.id,
      getVisibleTiles().map((tile) => tile.key),
    );
    await reloadFeatures(layer);
  }

  function applyDeletedFeature(layer: LayerDto, featureId: string): void {
    tileCache.removeFeature(layer.id, featureId);
    syncVisibleSource(layer);
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
    applyPatchedFeature,
    applyCreatedFeature,
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
    const featureCollection = tileCache.buildVisibleFeatureCollection(
      layer.id,
      visibleTileKeys,
    );
    setSourceData(map.value, getSourceId(layer), featureCollection);
  }
}

function getSourceId(layer: LayerDto): string {
  return `src:${layer.id}`;
}
