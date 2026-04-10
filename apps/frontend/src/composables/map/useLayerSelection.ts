import { ref, type ShallowRef } from "vue";
import type { Map } from "maplibre-gl";
import { fetchLayers, type LayerDto } from "@/api/layers";
import { ensureLayerOnMap, setAnyLayerVisibility } from "@/map/maplibrelayers";

export type LoadLayersResult =
  | { status: "empty" }
  | { status: "ready"; layer: LayerDto; total: number };

type ChangeLayerOptions = {
  onCurrentLayerDeactivated?: (layer: LayerDto) => void;
  onNextLayerActivated?: (layer: LayerDto) => Promise<void> | void;
};

export function useLayerSelection(map: ShallowRef<Map | null>) {
  const layers = ref<LayerDto[]>([]);
  const activeLayer = ref<LayerDto | null>(null);
  const activeLayerId = ref<string | null>(null);
  const layerAbortController = ref<AbortController | null>(null);

  async function loadLayers(): Promise<LoadLayersResult> {
    abortLayerLoading();

    const controller = new AbortController();
    layerAbortController.value = controller;

    const nextLayers = await fetchLayers(controller.signal);
    layers.value = nextLayers;
    activeLayer.value = nextLayers[0] ?? null;
    activeLayerId.value = activeLayer.value?.id ?? null;

    if (!activeLayer.value) {
      return { status: "empty" };
    }

    const currentMap = map.value;
    if (currentMap) {
      ensureLayerOnMap(currentMap, activeLayer.value);
      for (const layer of layers.value) {
        setAnyLayerVisibility(currentMap, layer, false);
      }
      setAnyLayerVisibility(currentMap, activeLayer.value, true);
    }

    return {
      status: "ready",
      layer: activeLayer.value,
      total: nextLayers.length,
    };
  }

  async function changeLayer(
    nextLayerId: string | null,
    options: ChangeLayerOptions = {},
  ): Promise<LayerDto | null> {
    const currentMap = map.value;
    if (!currentMap || !nextLayerId) {
      return null;
    }

    const nextLayer =
      layers.value.find((layer) => layer.id === nextLayerId) ?? null;
    if (!nextLayer) {
      return null;
    }

    if (activeLayer.value) {
      setAnyLayerVisibility(currentMap, activeLayer.value, false);
      options.onCurrentLayerDeactivated?.(activeLayer.value);
    }

    activeLayer.value = nextLayer;
    activeLayerId.value = nextLayer.id;

    ensureLayerOnMap(currentMap, nextLayer);
    setAnyLayerVisibility(currentMap, nextLayer, true);
    await options.onNextLayerActivated?.(nextLayer);

    return nextLayer;
  }

  function abortLayerLoading(): void {
    layerAbortController.value?.abort();
    layerAbortController.value = null;
  }

  return {
    layers,
    activeLayer,
    activeLayerId,
    loadLayers,
    changeLayer,
    abortLayerLoading,
  };
}
