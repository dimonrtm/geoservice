<template>
  <div class="mapRoot">
    <div class="badge">{{ labelText }}</div>
    <div ref="mapEl" class="mapCanvas"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, shallowRef } from "vue";
import { Map, NavigationControl, type StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const mapEl = ref<HTMLDivElement | null>(null);
const map = shallowRef<Map | null>(null);
let labelText = ref("Карта загружается...");
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
  map.value.once("load", () => {
    labelText.value = "Карта готова";
  });
  console.log("Карта создана");
});

onBeforeUnmount(() => {
  map.value?.remove();
  map.value = null;
  console.log("Карта удалена");
});
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
