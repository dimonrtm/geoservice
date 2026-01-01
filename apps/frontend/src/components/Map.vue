<template>
  <!-- Контейнер под карту -->
  <div ref="mapEl" class="map"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import maplibregl, {type Map as MapLibreMap} from "maplibre-gl"

const mapEl = ref<HTMLDivElement | null>(null);
let map: MapLibreMap | null = null
const styleUrl = import.meta.env.VITE_MAP_STYLE_URL as string

onMounted(() => {
if(!mapEl.value) return;

console.log("styleUrl:", styleUrl);
map = new maplibregl.Map({
container: mapEl.value,
style: styleUrl,
center: [76.8897, 43.2389],
zoom: 10
});

map.addControl(new maplibregl.NavigationControl(), "top-right");
map.on("load", () =>{
  console.log("map loaded");
});
map.on("error", (e) =>{
  console.error("map error:", e.error)
});
});

onBeforeUnmount(() => {
  map?.remove();
  map = null;
  console.log("map removed")
});
</script>

<style scoped>
/* ВАЖНО: если высоты нет — карта будет “невидимой” */
.map {
  width: 100%;
  height: 100vh;
}
</style>
