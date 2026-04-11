import { ref, type ShallowRef } from "vue";
import { AxiosError } from "axios";
import { fetchLayerFeaturesByBbox, HttpError } from "@/api/layers";
import type { LayerDto } from "@/contracts/api";
import {
  BboxClose,
  formatBbox,
  getCurrentBbox,
  isValidBbox,
  setSourceData,
  type Bbox,
} from "@/map/maplibrelayers";
import type { Map } from "maplibre-gl";

const BBOX_EPS = 0.002;
const DEBOUNCE_MS = 250;
const MIN_ZOOM = 8;
const FEATURE_LIMIT = 500;

export function useFeatureLoading(map: ShallowRef<Map | null>) {
  const labelText = ref("Карта загружается...");
  const isLoadingFeature = ref(false);
  const lastRequestedBbox = ref<Bbox | null>(null);
  const featuresAbortController = ref<AbortController | null>(null);
  let moveTimer: ReturnType<typeof setTimeout> | null = null;

  async function reloadFeatures(layer: LayerDto): Promise<void> {
    const zoom = map.value?.getZoom();
    if (zoom !== undefined && zoom < MIN_ZOOM) {
      labelText.value = `Zoom ${zoom.toFixed(1)}: приблизтесь к ${MIN_ZOOM}`;
      return;
    }

    const bbox = getCurrentBbox(map.value);
    if (!isValidBbox(bbox)) {
      labelText.value = "Bbox не валиден на клиенте";
      return;
    }

    if (
      lastRequestedBbox.value &&
      BboxClose(bbox, lastRequestedBbox.value, BBOX_EPS)
    ) {
      return;
    }

    stopPendingFeatureWork();
    isLoadingFeature.value = true;
    labelText.value = "Загружаю объекты...";

    const controller = new AbortController();
    featuresAbortController.value = controller;
    lastRequestedBbox.value = bbox;

    try {
      const featureCollection = await fetchLayerFeaturesByBbox({
        layerId: layer.id,
        bbox,
        limit: FEATURE_LIMIT,
        signal: controller.signal,
      });
      setSourceData(map.value, getSourceId(layer), featureCollection);
      const count = featureCollection.features.length;
      if (count === 0) {
        labelText.value = `Layer: ${layer.title} | bbox: ${formatBbox(bbox)} | пусто | limit ${FEATURE_LIMIT}`;
      } else {
        labelText.value = `Layer: ${layer.title} | bbox: ${formatBbox(bbox)} | features: ${count} | limit ${FEATURE_LIMIT}`;
      }
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.code === "ERR_CANCELED") {
        return;
      }
      if (err instanceof HttpError) {
        if (err.status === 404) {
          labelText.value = "Слой не найден (404)";
        } else if (err.status === 422) {
          labelText.value = "Невалидный Bbox (422)";
        } else {
          labelText.value = `Ошибка загрузки. HTTP ${err.status}`;
        }
      } else {
        labelText.value = "Сетевая/неизвестная ошибка";
      }
    } finally {
      isLoadingFeature.value = false;
    }
  }

  function createMoveEndHandler(
    getActiveLayer: () => LayerDto | null,
  ): () => void {
    return () => {
      if (isLoadingFeature.value) {
        return;
      }

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

  function resetLoadedBbox(): void {
    lastRequestedBbox.value = null;
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
    resetLoadedBbox,
    stopPendingFeatureWork,
  };
}

function getSourceId(layer: LayerDto): string {
  return `src:${layer.id}`;
}
