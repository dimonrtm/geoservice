<template>
  <div class="page">
    <div class="toolbar">
      <div class="modal">
        <h3>Выберите слой</h3>
        <select v-model="activeLayerId" @change="onChangeLayer">
          <option v-for="layer in layers" :key="layer.id" :value="layer.id">
            {{ layer.title ?? layer.name }}
          </option>
        </select>
      </div>

      <div class="actions">
        <button type="button" @click="saveChange">Сохранить</button>
        <button type="button" @click="deleteFeature">Удалить</button>
      </div>
    </div>

    <div class="mapRoot">
      <div class="badge">{{ labelText }}</div>
      <div ref="mapEl" class="mapCanvas"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ref,
  onMounted,
  onBeforeUnmount,
  shallowRef,
  watch,
  nextTick,
} from "vue";
import {
  Map,
  NavigationControl,
  type StyleSpecification,
  type MapLayerMouseEvent,
  type MapMouseEvent,
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
  movePolygonVertex,
} from "@/map/maplibrelayers";
import type { Bbox } from "@/map/maplibrelayers";
import { useEditStore } from "@/stores/edit";
import { isFiniteNumber, toFiniteNumber } from "@/parsing/common";
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
let dragging = false;
let dragRing = 0;
let dragIndex = 0;
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

onMounted(async () => {
  if (!mapEl.value) {
    return;
  }
  map.value = new Map({
    container: mapEl.value,
    style,
    center: [70.1902, 52.937],
    zoom: 8,
  });
  map.value.addControl(new NavigationControl(), "top-right");
  await nextTick();
  map.value.resize();
  map.value.once("load", async () => {
    await nextTick();
    map.value?.resize();
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
    map.value?.on("mousedown", "edit:vertices:point", onVertexDown);
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
  map.value?.off("mousedown", "edit:vertices:point", onVertexDown);
  map.value?.off("mousemove", onVertexMove);
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
  const layer = layers.value.find((layer) => layer.id === layerId) ?? null;
  if (!layer) {
    labelText.value = "Слой ненайден в списке";
    return;
  }
  if (activeLayer.value) {
    setAnyLayerVisibility(m, activeLayer.value, false);
    m.off("click", `layer:${activeLayer.value.id}`, onLayerClick);
    editStore.edit = {mode: "idle"};
  }
  activeLayer.value = layer;
  ensureLayerOnMap(map.value, layer);
  setAnyLayerVisibility(m, activeLayer.value, true);
  m.on("click", `layer:${layer.id}`, onLayerClick);
  m.off("mousemove", onVertexMove);
  dragging = false;
  featuresAbortController.value?.abort();
  if (moveTimer !== null) {
    clearTimeout(moveTimer);
    moveTimer = null;
  }
  lastRequestedBbox.value = null;
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
  const props = feature.properties as Record<string, unknown>;
  const featureId = typeof props["__id"] === "string" ? props["__id"] : null;
  if (!featureId) {
    return;
  }
  const v = props["__version"];
  const version = isFiniteNumber(v) ? (v as number) : null;
  if (version === null) {
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
      properties: props,
      geometry: polygon,
    });
  }
}

async function saveChange(): Promise<void> {
  await editStore.saveEditing();
}

async function deleteFeature(): Promise<void> {
  const deleted = await editStore.deleteEditing();
  if (editStore.edit.mode === "idle" && activeLayer.value && deleted) {
    lastRequestedBbox.value = null;
    await reloadFeatures(activeLayer.value);
  }
}

function onVertexDown(e: MapLayerMouseEvent): void {
  if (editStore.edit.mode !== "editing") {
    return;
  }
  const m = map.value;
  if (!m) {
    return;
  }
  e.preventDefault();
  if (!e.features?.length || !e.features[0]) {
    return;
  }
  const feature = e.features[0];
  if (feature.properties["ring"] === undefined) {
    return;
  }
  const ring = toFiniteNumber(feature.properties["ring"]);
  if (feature.properties["i"] === undefined) {
    return;
  }
  const i = toFiniteNumber(feature.properties["i"]);
  if (ring === null || i === null) {
    return;
  }
  dragging = true;
  dragRing = ring;
  dragIndex = i;
  m.dragPan.disable();
  m.on("mousemove", onVertexMove);
  m.once("mouseup", onVertexUp);
}

function onVertexMove(e: MapMouseEvent): void {
  if (!dragging) {
    return;
  }
  if (editStore.edit.mode !== "editing") {
    return;
  }
  const session = editStore.edit.session;
  const lng = e.lngLat.lng;
  const lat = e.lngLat.lat;
  const nextGeometry = movePolygonVertex(
    session.draft.geometry,
    dragRing,
    dragIndex,
    lng,
    lat,
  );
  editStore.updateDraft({
    properties: session.draft.properties,
    geometry: nextGeometry,
  });
}

function onVertexUp(): void {
  if (!map.value) {
    return;
  }
  dragging = false;
  map.value.off("mousemove", onVertexMove);
  map.value.dragPan.enable();
}
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.toolbar {
  flex: 0 0 auto;
  padding: 8px;
  background: rgba(255, 255, 255, 0.95);
  position: relative;
  z-index: 10;
}
.modal h3 {
  margin: 0 0 6px 0;
  font-size: 16px;
}
.actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
.mapRoot {
  flex: 1 1 auto;
  min-height: 0;
  position: relative;
}
.mapCanvas {
  position: absolute;
  inset: 0;
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
