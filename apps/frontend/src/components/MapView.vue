<template>
  <div class="mapRoot">
    <div class="badge">{{ labelText }}</div>
    <div ref="mapEl" class="mapCanvas"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, shallowRef } from "vue";
import type { FeatureCollection, Geometry } from "geojson";
import {
  Map,
  NavigationControl,
  type StyleSpecification,
  type GeoJSONSource,
} from "maplibre-gl";
import type { LayerDto } from "@/api/layers";
import { fetchLayers, fetchLayerFeaturesByBbox, HttpError } from "@/api/layers";
import "maplibre-gl/dist/maplibre-gl.css";
import { AxiosError } from "axios";

type Bbox = [number, number, number, number];
const mapEl = ref<HTMLDivElement | null>(null);
const map = shallowRef<Map | null>(null);
const layers = ref<LayerDto[]>([]);
let activeLayer = ref<LayerDto | null>(null);
let labelText = ref("Карта загружается...");
let layerAbortController = ref<AbortController | null>(null);
const featuresAbortController = ref<AbortController | null>(null);
let moveTimer: number | null = null;
const DEBOUNCE_MS = 250;
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
    zoom: 3,
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
    activeLayer.value = layers.value[0] ?? null;
    if (!activeLayer.value) {
      labelText.value = "Слои загружены, но выбрать нечего";
      return;
    }
    labelText.value = `Слои загружены ${layers.value.length}. Выбран ${activeLayer.value?.title}`;
    ensureLayerOnMap(map.value, activeLayer.value);
    await reloadFeatures(activeLayer.value);
    map.value?.on("moveend", sheduleReload);
  });
  console.log("Карта создана");
});

onBeforeUnmount(() => {
  map.value?.off("moveend", sheduleReload);
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
  clearTimeout(moveTimer!);
  console.log("Карта удалена");
});

function ensureLayerOnMap(map: Map | null, layer: LayerDto): void {
  if (!map) {
    return;
  }
  const sourceId = "src:" + layer.id;
  const layerId = "layer:" + layer.id;
  const source = map.getSource(sourceId);
  if (!source) {
    map.addSource(sourceId, {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
  }
  const existLayer = map.getLayer(layerId);
  if (!existLayer) {
    if (layer.geometryType.includes("Point")) {
      map.addLayer({
        id: layerId,
        type: "circle",
        source: sourceId,
        paint: { "circle-color": "#000000" },
      });
    } else if (layer.geometryType.includes("Line")) {
      map.addLayer({
        id: layerId,
        type: "line",
        source: sourceId,
        paint: { "line-color": "#000000" },
      });
    } else {
      map.addLayer({
        id: layerId,
        type: "fill",
        source: sourceId,
        paint: { "fill-color": "#000000" },
      });
    }
  }
}

function getCurrentBbox(map: Map | null): Bbox {
  if (!map) {
    return [0, 0, 0, 0];
  }
  const bounds = map.getBounds();
  return [
    bounds.getWest(),
    bounds.getSouth(),
    bounds.getEast(),
    bounds.getNorth(),
  ];
}

function setSourceData(
  map: Map | null,
  sourceId: string,
  featureCollection: { type: "FeatureCollection"; features: unknown[] },
) {
  if (!map) {
    return;
  }
  const source = map.getSource(sourceId) as GeoJSONSource | undefined;
  if (!source) {
    return;
  }
  source.setData(featureCollection as FeatureCollection<Geometry>);
}

function getSourceId(layer: LayerDto): string {
  return "src:" + layer.id;
}

async function reloadFeatures(layer: LayerDto): Promise<void> {
  featuresAbortController.value?.abort();
  const featuresController = new AbortController();
  featuresAbortController.value = featuresController;
  try {
    const bbox = getCurrentBbox(map.value);
    const featureCollection = await fetchLayerFeaturesByBbox({
      layerId: layer.id,
      bbox: bbox,
      limit: 500,
      signal: featuresController.signal,
    });
    setSourceData(map.value, getSourceId(layer), featureCollection);
    labelText.value = `Загружено фич: ${featureCollection.features.length}`;
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
  }
}

function sheduleReload(): void {
  clearTimeout(moveTimer!);
  moveTimer = setTimeout(() => {
    if (!activeLayer.value) {
      return;
    }
    reloadFeatures(activeLayer.value);
  }, DEBOUNCE_MS);
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
