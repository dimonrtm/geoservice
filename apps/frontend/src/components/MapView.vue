<template>
  <div class="modal">
    <h3>Выберите слой</h3>
    <select v-model="activeLayerId" @change="onChangeLayer">
      <option v-for="layer in layers" :key="layer.id" :value="layer.id">
        {{ layer.title ?? layer.name }}
      </option>
    </select>
  </div>
  <div>
    <button type="button" @click="saveChange">Сохранить</button>
    <button type="button" @click="deleteFeature">Удалить</button>
  </div>
  <div class="mapRoot">
    <div class="badge">{{ labelText }}</div>
    <div ref="mapEl" class="mapCanvas"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, shallowRef, watch } from "vue";
import {
  Map,
  NavigationControl,
  type StyleSpecification,
  type MapLayerMouseEvent,
} from "maplibre-gl";
import type { LayerDto } from "@/api/layers";
import { fetchLayers, fetchLayerFeaturesByBbox, HttpError } from "@/api/layers";
import "maplibre-gl/dist/maplibre-gl.css";
import { AxiosError } from "axios";
import {
  ensureLayerOnMap,
  getCurrentBbox,
  setSourceData,
  isValidBbox,
  setAnyLayerVisibility,
  formatBbox,
  BboxClose,
  ensureEditSource,
  ensureEditLayer,
  renderEditOverlay,
  type VersionIndex,
  buildVersionIndex,
} from "@/map/maplibrelayers";
import type { Bbox } from "@/map/maplibrelayers";
import { useEditStore } from "@/stores/edit";
type Polygon = import("geojson").Polygon;

const mapEl = ref<HTMLDivElement | null>(null);
const map = shallowRef<Map | null>(null);
const layers = ref<LayerDto[]>([]);
let activeLayer = ref<LayerDto | null>(null);
const activeLayerId = ref<string | null>(null);
let labelText = ref("Карта загружается...");
let layerAbortController = ref<AbortController | null>(null);
const featuresAbortController = ref<AbortController | null>(null);
let moveTimer: number | null = null;
const DEBOUNCE_MS = 250;
const isLoadingFeature = ref(false);
const lastRequestedBbox = ref<Bbox | null>(null);
const BBOX_EPS = 0.002;
const MIN_ZOOM = 8;
const editStore = useEditStore();
let stopWatch: (() => void) | null = null;
let versionIndex: VersionIndex | null = null;
const style: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [
    {
      id: "osm",
      type: "raster",
      source: "osm",
    },
  ],
};

onMounted(() => {
  if (!mapEl.value) {
    return;
  }
  map.value = new Map({
    container: mapEl.value,
    style,
    center: [70.1902, 52.937],
    zoom: 7,
  });
  map.value.addControl(new NavigationControl(), "top-right");
  map.value.once("load", async () => {
    labelText.value = "Карта готова. Загружаю слои...";
    const controller = new AbortController();
    layerAbortController.value = controller;
    layers.value = await fetchLayers(controller.signal);
    if (layers.value.length === 0) {
      labelText.value = "Слоев нет";
      return;
    }
    activeLayerId.value = layers.value[0]?.id ?? null;
    activeLayer.value = layers.value[0] ?? null;
    if (!activeLayer.value) {
      labelText.value = "Слои загружены, но выбрать нечего";
      return;
    }
    labelText.value = `Слои загружены ${layers.value.length}. Выбран ${activeLayer.value?.title}`;
    ensureLayerOnMap(map.value, activeLayer.value);
    for (var layer of layers.value) {
      setAnyLayerVisibility(map.value, layer, false);
    }
    setAnyLayerVisibility(map.value, activeLayer.value, true);
    await reloadFeatures(activeLayer.value);
    map.value?.on("moveend", scheduleReload);
    map.value?.on("click", `layer:${activeLayer.value.id}`, onLayerClick);
    ensureEditSource(map.value);
    ensureEditLayer(map.value);
    renderEditOverlay(map.value, editStore.edit);
    stopWatch = watch([() => editStore.edit, map], ([nextEditState, m]) => {
      if (!m) {
        return;
      }
      renderEditOverlay(m, nextEditState);
    });
  });
  console.log("Карта создана");
});

onBeforeUnmount(() => {
  if (stopWatch) {
    stopWatch();
  }
  stopWatch = null;
  map.value?.off("moveend", scheduleReload);
  map.value?.off("click", `layer:${activeLayer.value?.id}`, onLayerClick);
  map.value?.remove();
  map.value = null;
  if (layerAbortController.value) {
    layerAbortController.value?.abort();
    layerAbortController.value = null;
  }
  if (featuresAbortController.value) {
    featuresAbortController.value?.abort();
    featuresAbortController.value = null;
  }
  if (moveTimer !== null) {
    clearTimeout(moveTimer);
    moveTimer = null;
  }

  console.log("Карта удалена");
});
function getSourceId(layer: LayerDto): string {
  return "src:" + layer.id;
}

async function reloadFeatures(layer: LayerDto): Promise<void> {
  const z = map.value?.getZoom();
  if (z && z < MIN_ZOOM) {
    labelText.value = `Zoom ${z.toFixed(1)}: приблизтесь к ${MIN_ZOOM}`;
    return;
  }
  const limit = 500;
  isLoadingFeature.value = true;
  labelText.value = "Загружаю объекты...";
  featuresAbortController.value?.abort();
  const featuresController = new AbortController();
  featuresAbortController.value = featuresController;
  try {
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
    lastRequestedBbox.value = bbox;
    const featureCollection = await fetchLayerFeaturesByBbox({
      layerId: layer.id,
      bbox: bbox,
      limit: limit,
      signal: featuresController.signal,
    });
    setSourceData(map.value, getSourceId(layer), featureCollection);
    versionIndex = buildVersionIndex(featureCollection);
    const n = featureCollection.features.length;
    if (n == 0) {
      labelText.value = `Layer: ${layer.title} | bbox: ${formatBbox(bbox)} | пусто | limit ${limit}`;
    } else {
      labelText.value = `Layer: ${layer.title} | bbox: ${formatBbox(bbox)} | features: ${n} | limit ${limit}`;
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

function scheduleReload(): void {
  if (isLoadingFeature.value) {
    return;
  }
  if (moveTimer !== null) {
    clearTimeout(moveTimer);
    moveTimer = null;
  }

  moveTimer = setTimeout(async () => {
    if (!activeLayer.value) {
      return;
    }
    await reloadFeatures(activeLayer.value);
  }, DEBOUNCE_MS);
}

async function onChangeLayer(): Promise<void> {
  const m = map.value;
  const layerId = activeLayerId.value;
  if (!m || !layerId) {
    return;
  }
  console.log(layerId);
  const layer = layers.value.find((layer) => layer.id === layerId) ?? null;
  if (!layer) {
    labelText.value = "Слой ненайден в списке";
    return;
  }
  if (activeLayer.value) {
    setAnyLayerVisibility(m, activeLayer.value, false);
    m.off("click", `layer:${activeLayer.value.id}`, onLayerClick);
  }
  activeLayer.value = layer;
  ensureLayerOnMap(map.value, layer);
  setAnyLayerVisibility(m, activeLayer.value, true);
  m.on("click", `layer:${layer.id}`, onLayerClick);
  featuresAbortController.value?.abort();
  if (moveTimer !== null) {
    clearTimeout(moveTimer);
    moveTimer = null;
  }
  await reloadFeatures(layer);
}

function onLayerClick(e: MapLayerMouseEvent): void {
  if (editStore.edit.mode === "editing" && editStore.edit.dirty) {
    return;
  }
  if (!e.features?.length || e.features?.length <= 0) {
    return;
  }
  const feature = e.features[0];
  if (!feature || !feature.properties || !feature.geometry) {
    return;
  }
  const featureId =
    typeof feature.id === "string" || typeof feature.id === "number"
      ? String(feature.id)
      : null;
  if (!featureId) {
    return;
  }
  if (!versionIndex) {
    return;
  }
  const version = versionIndex[featureId];
  if (version === undefined) {
    return;
  }
  if (!activeLayer.value) {
    return;
  }
  if (feature.geometry.type === "Polygon") {
    const polygon = feature.geometry as Polygon;
    editStore.startEditing({
      layerId: activeLayer.value.id,
      featureId: featureId,
      version: version,
      properties: feature.properties,
      geometry: polygon,
    });
  }
}

async function saveChange(): Promise<void> {
  await editStore.saveEditing();
}

async function deleteFeature(): Promise<void> {
  await editStore.deleteEditing();
}
</script>

<style scoped>
.mapRoot {
  position: relative;
  height: 100%;
  width: 100%;
  min-height: 0;
}
.mapCanvas {
  width: 100%;
  height: 100%;
}
.badge {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  background: rgba(255, 255, 255, 0.9);
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 14px;
}
</style>
