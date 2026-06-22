<template>
  <div class="page">
    <div v-if="props.mode === 'editing'" class="toolbar">
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
      <div
        v-if="props.mode === 'editing'"
        class="realtimeBadge"
        :class="realtimeBadgeClass"
      >
        {{ realtimeStatusText }}
      </div>
      <div ref="mapEl" class="mapCanvas"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import "maplibre-gl/dist/maplibre-gl.css";
import { useAuthStore } from "@/stores/auth";
import type { LayerDto } from "@/contracts/api";
import { useFeatureLoading } from "@/composables/map/useFeatureLoading";
import { useLayerRealtime } from "@/composables/map/useLayerRealtime";
import { useLayerSelection } from "@/composables/map/useLayerSelection";
import { useMapInstance } from "@/composables/map/useMapInstance";
import { usePolygonEditing } from "@/composables/map/usePolygonEditing";

const props = withDefaults(
  defineProps<{
    mode?: "empty" | "editing";
  }>(),
  {
    mode: "editing",
  },
);
const mapEl = ref<HTMLDivElement | null>(null);
const auth = useAuthStore();
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
  applyCreatedFeature,
  applyPatchedFeature,
  applyDeletedFeature,
  stopPendingFeatureWork,
} = useFeatureLoading(map);
const {
  handleLayerChange: handleRealtimeLayerChange,
  disconnect: disconnectRealtime,
  isConnected,
  isReconnecting,
  isSyncingAfterReconnect,
  hasStoppedReconnect,
  isAuthError,
} = useLayerRealtime({
  onFeatureCreated: async (layerId, feature) => {
    const currentLayer = activeLayer.value;
    if (!currentLayer || currentLayer.id !== layerId) {
      return;
    }
    await applyCreatedFeature(currentLayer, feature);
  },
  onFeatureUpdated: async (layerId, feature) => {
    const currentLayer = activeLayer.value;
    if (!currentLayer || currentLayer.id !== layerId) {
      return;
    }
    await applyPatchedFeature(currentLayer, feature);
  },
  onFeatureDeleted: (layerId, featureId) => {
    const currentLayer = activeLayer.value;
    if (!currentLayer || currentLayer.id !== layerId) {
      return;
    }
    applyDeletedFeature(currentLayer, featureId);
  },
  onReconnectSynced: async (layerId) => {
    const currentLayer = activeLayer.value;
    if (!currentLayer || currentLayer.id !== layerId) {
      return;
    }
    await reloadFeatures(currentLayer, { force: true });
  },
});
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
const realtimeStatusText = computed(() => {
  if (isAuthError.value) {
    return "Ошибка авторизации realtime";
  }
  if (isSyncingAfterReconnect.value) {
    return "Синхронизация";
  }
  if (isReconnecting.value) {
    return "Переподключение";
  }
  if (hasStoppedReconnect.value) {
    return "Переподключение остановлено";
  }
  if (isConnected.value) {
    return "Подключено";
  }
  return "Подключение...";
});
const realtimeBadgeClass = computed(() => ({
  isConnected: isConnected.value,
  isReconnecting: isReconnecting.value,
  isSyncing: isSyncingAfterReconnect.value,
  isStopped: hasStoppedReconnect.value,
  isAuthError: isAuthError.value,
}));

onMounted(async () => {
  try {
    const currentMap = await createMap();
    if (!currentMap) {
      return;
    }

    if (props.mode === "empty") {
      labelText.value = "Карта готова. Выберите наряд в списке.";
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
    await syncRealtimeLayer(loadLayersResult.layer);
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
  disconnectRealtime();
  destroyMap();
});

async function onChangeLayer(): Promise<void> {
  const nextLayer = await changeLayer(activeLayerId.value, {
    onCurrentLayerDeactivated: (layer) => {
      unbindActiveLayerClick(layer.id);
      cancelEditing();
      disconnectRealtime();
    },
    onNextLayerActivated: async (layer) => {
      bindActiveLayerClick(layer.id);
      resetInteractionState();
      stopPendingFeatureWork();
      await reloadFeatures(layer);
      await syncRealtimeLayer(layer);
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

async function syncRealtimeLayer(layer: LayerDto | null): Promise<void> {
  if (!layer || !auth.token || !auth.isAuthenticated) {
    disconnectRealtime();
    return;
  }

  await handleRealtimeLayerChange(layer, auth.token);
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
.realtimeBadge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  background: rgba(255, 255, 255, 0.92);
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(15, 23, 42, 0.12);
}
.realtimeBadge.isConnected {
  color: #0f766e;
}
.realtimeBadge.isReconnecting,
.realtimeBadge.isSyncing {
  color: #b45309;
}
.realtimeBadge.isStopped,
.realtimeBadge.isAuthError {
  color: #b91c1c;
}
</style>
