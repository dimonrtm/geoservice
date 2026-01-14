<template>
  <div ref="mapEl" class="mapEl"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, shallowRef } from "vue";
import { Map, NavigationControl, type StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const mapEl = ref<HTMLDivElement | null>(null);
const map = shallowRef<Map | null>(null);
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
  console.log("Карта создана");
});

onBeforeUnmount(() => {
  map.value?.remove();
  map.value = null;
  console.log("Карта удалена");
});
</script>

<style scoped>
.mapEl {
  width: 100%;
  height: 100%;
}
</style>
