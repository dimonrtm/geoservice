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
        <button type="button" @click="saveFeature">Сохранить</button>
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
import { onBeforeUnmount, onMounted, ref } from "vue";
import "maplibre-gl/dist/maplibre-gl.css";
import { useFeatureLoading } from "@/composables/map/useFeatureLoading";
import { useLayerSelection } from "@/composables/map/useLayerSelection";
import { useMapInstance } from "@/composables/map/useMapInstance";
import { usePolygonEditing } from "@/composables/map/usePolygonEditing";

const mapEl = ref<HTMLDivElement | null>(null);
const { map, createMap, destroyMap } = useMapInstance(mapEl);
const {
  layers,
  activeLayer,
  activeLayerId,
  loadLayers,
  changeLayer,
  abortLayerLoading,
} = useLayerSelection(map);
const {
  labelText,
  reloadFeatures,
  createMoveEndHandler,
  applyPatchedFeature,
  applyDeletedFeature,
  stopPendingFeatureWork,
} = useFeatureLoading(map);
const {
  enableEditingOverlaySync,
  disableEditingOverlaySync,
  bindActiveLayerClick,
  unbindActiveLayerClick,
  resetInteractionState,
  saveChange,
  deleteEditingFeature,
  cancelEditing,
} = usePolygonEditing(map, activeLayer);
const onMoveEnd = createMoveEndHandler(() => activeLayer.value);

onMounted(async () => {
  try {
    const currentMap = await createMap();
    if (!currentMap) {
      return;
    }

    labelText.value = "Карта готова. Загружаю слои...";
    const loadLayersResult = await loadLayers();
    if (loadLayersResult.status === "empty") {
      labelText.value = "Слоев нет";
      return;
    }
    labelText.value = `Слои загружены: ${loadLayersResult.total}. Выбран слой: ${loadLayersResult.layer.title}`;
    bindActiveLayerClick(loadLayersResult.layer.id);
    enableEditingOverlaySync();
    await reloadFeatures(loadLayersResult.layer);
    currentMap.on("moveend", onMoveEnd);
  } catch {
    labelText.value = "Не удалось инициализировать карту";
  }
});

onBeforeUnmount(() => {
  map.value?.off("moveend", onMoveEnd);
  unbindActiveLayerClick(activeLayer.value?.id);
  disableEditingOverlaySync();
  stopPendingFeatureWork();
  abortLayerLoading();
  destroyMap();
});

async function onChangeLayer(): Promise<void> {
  const nextLayer = await changeLayer(activeLayerId.value, {
    onCurrentLayerDeactivated: (layer) => {
      unbindActiveLayerClick(layer.id);
      cancelEditing();
    },
    onNextLayerActivated: async (layer) => {
      bindActiveLayerClick(layer.id);
      resetInteractionState();
      stopPendingFeatureWork();
      await reloadFeatures(layer);
    },
  });
  if (!nextLayer) {
    labelText.value = "Слой не найден в списке";
  }
}

async function deleteFeature(): Promise<void> {
  const deletedFeatureId = await deleteEditingFeature();
  if (activeLayer.value && deletedFeatureId) {
    applyDeletedFeature(activeLayer.value, deletedFeatureId);
  }
}

async function saveFeature(): Promise<void> {
  const savedFeature = await saveChange();
  if (activeLayer.value && savedFeature) {
    await applyPatchedFeature(activeLayer.value, savedFeature);
  }
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
