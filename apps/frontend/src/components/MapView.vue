<template>
  <div class="mapRoot">
    <div class="badge">{{ labelText }}</div>
    <div ref="mapEl" class="mapCanvas"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, shallowRef } from "vue";
import { Map, NavigationControl, type StyleSpecification } from "maplibre-gl";
import type { LayerDto } from "@/api/layers";
import { fetchLayers } from "@/api/layers";
import "maplibre-gl/dist/maplibre-gl.css";

const mapEl = ref<HTMLDivElement | null>(null);
const map = shallowRef<Map | null>(null);
const layers = ref<LayerDto[]>([]);
let activeLayer = ref<LayerDto | null>(null);
let labelText = ref("Карта загружается...");
let layerAbortController = ref<AbortController | null>(null);
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
    console.log(layers.value);
    activeLayer.value = (layers.value[0] as LayerDto) ?? null;
    console.log(activeLayer.value);
    if (layers.value.length === 0) {
      labelText.value = "Слоев нет";
      return;
    }
    labelText.value = `Слои загружены ${layers.value.length}. Выбран ${activeLayer.value?.title}`;
    ensureLayerOnMap(map.value, activeLayer.value);
  });
  console.log("Карта создана");
});

onBeforeUnmount(() => {
  map.value?.remove();
  map.value = null;
  if (layerAbortController.value) {
    layerAbortController.value = null;
  }
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
  font-size: 14;
}
</style>
