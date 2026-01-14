<script setup lang="ts">
import CheckAuthComponent from "./components/CheckAuthComponent.vue";
import MapView from "./components/MapView.vue";
import "./assets/main.css";
</script>

<template>
  <CheckAuthComponent />
  <MapView />
</template>

<style scoped>
.page {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.content {
  flex: 1;
  min-height: 0;
} /* важно для flex-раскладки */
</style>
