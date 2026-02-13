<script setup lang="ts">
import CheckAuthComponent from "./components/CheckAuthComponent.vue";
import MapPageView from "./components/MapPageView.vue";
import "./assets/main.css";
</script>

<template>
  <div class="page">
    <div class="topPanel">
      <CheckAuthComponent />
    </div>
    <div class="content">
      <MapPageView class="mapSlot" />
    </div>
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.topPanel {
  flex: 0 0 auto;
  padding: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.95);
  z-index: 10;
  max-height: 240px;
  overflow: auto;
}
.content {
  flex: 1 1 auto;
  min-height: 0;
  position: relative;
  overflow: hidden;
}
.mapSlot {
  height: 100%;
  width: 100%;
  min-height: 0;
}
</style>
