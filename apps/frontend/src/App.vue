<script setup lang="ts">
import FileLoader from "./components/FileLoader.vue";
import Map from "./components/Map.vue";
import { ref } from "vue";
const isOpen = ref(true);
</script>

<template>
  <div>
    <button @click="isOpen = !isOpen">toggle</button>
  </div>
  <Map v-if="isOpen" />
  <FileLoader />
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
