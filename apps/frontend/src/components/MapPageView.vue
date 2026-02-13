<script setup lang="ts">
import MapView from "./MapView.vue";
</script>

<template>
  <div class="appRoot">
    <MapView class="mapSlot" />
  </div>
</template>
<style scoped>
.appRoot {
  height: 100%;
  width: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.mapSlot {
  flex: 1 1 auto;
  min-height: 0;
}
</style>
