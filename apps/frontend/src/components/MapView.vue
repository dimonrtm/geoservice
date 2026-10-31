<template>
  <div class="page">
    <div v-if="props.mode === 'editing' && mapReady" class="toolbar">
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
      <div v-if="startupState === 'error'" class="startupError" role="alert">
        <div class="startupErrorMessage">
          <h2>Не удалось запустить карту</h2>
          <p>Обновите страницу с помощью кнопки обновления в браузере.</p>
        </div>
      </div>
      <div
        v-if="props.mode !== 'workspace' && startupState !== 'error'"
        class="badge"
      >
        {{ labelText }}
      </div>
      <div
        v-if="props.mode === 'editing' && startupState !== 'error'"
        class="realtimeBadge"
        :class="realtimeBadgeClass"
      >
        {{ realtimeStatusText }}
      </div>
      <div ref="mapEl" class="mapCanvas"></div>
      <WorkspaceLineInteraction
        v-if="
          props.mode === 'workspace' &&
          props.workspaceInteractive &&
          props.workspace &&
          map &&
          mapReady
        "
        :map="map"
        :workspace="props.workspace"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import "maplibre-gl/dist/maplibre-gl.css";
import { useAuthStore } from "@/stores/auth";
import type { LayerDto } from "@/contracts/api";
import type { WorkspaceResponse } from "@/contracts/work-orders";
import { useFeatureLoading } from "@/composables/map/useFeatureLoading";
import { useLayerRealtime } from "@/composables/map/useLayerRealtime";
import { useLayerSelection } from "@/composables/map/useLayerSelection";
import { useMapInstance } from "@/composables/map/useMapInstance";
import { usePolygonEditing } from "@/composables/map/usePolygonEditing";
import WorkspaceLineInteraction from "@/components/WorkspaceLineInteraction.vue";
import {
  ensureWorkspaceLayers,
  fitWorkspaceToAoi,
  setWorkspaceData,
} from "@/map/workspace-layers";

const props = withDefaults(
  defineProps<{
    mode?: "empty" | "editing" | "workspace";
    workspace?: WorkspaceResponse | null;
    workspaceKey?: string | null;
    shouldFitWorkspace?: boolean;
    workspaceInteractive?: boolean;
  }>(),
  {
    mode: "editing",
    workspace: null,
    workspaceKey: null,
    shouldFitWorkspace: false,
    workspaceInteractive: false,
  },
);
const emit = defineEmits<{
  workspaceFitted: [workspaceKey: string];
  readyChange: [ready: boolean];
}>();
const mapEl = ref<HTMLDivElement | null>(null);
const startupState = ref<"loading" | "ready" | "error">("loading");
const mapReady = computed(() => startupState.value === "ready");
let disposed = false;
function setReady(ready: boolean): void {
  startupState.value = ready ? "ready" : "loading";
  emit("readyChange", ready);
}
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

function renderWorkspace(): void {
  if (!map.value || !props.workspace) {
    return;
  }

  ensureWorkspaceLayers(map.value);
  setWorkspaceData(map.value, props.workspace);

  if (props.shouldFitWorkspace && props.workspaceKey) {
    fitWorkspaceToAoi(map.value, props.workspace);
    emit("workspaceFitted", props.workspaceKey);
  }
}

onMounted(async () => {
  setReady(false);
  let currentMap;
  try {
    currentMap = await createMap();
    if (disposed) return;
    if (!currentMap) {
      startupState.value = "error";
      return;
    }

    if (props.mode === "workspace") {
      renderWorkspace();
      setReady(true);
      return;
    }

    if (props.mode === "empty") {
      labelText.value = "Карта готова. Выберите наряд в списке.";
      setReady(true);
      return;
    }
  } catch {
    if (!disposed) startupState.value = "error";
    return;
  }

  try {
    labelText.value = "Карта готова. Загружаю слои...";
    const loadLayersResult = await loadLayers();
    if (disposed) return;
    if (loadLayersResult.status === "empty") {
      labelText.value = "Слоев нет";
      setReady(true);
      return;
    }
    labelText.value = `Слои загружены: ${loadLayersResult.total}. Выбран слой: ${loadLayersResult.layer.title}`;
    bindActiveLayerClick(loadLayersResult.layer.id);
    enableEditingOverlaySync();
    await reloadFeatures(loadLayersResult.layer);
    if (disposed) return;
    await syncRealtimeLayer(loadLayersResult.layer);
    if (disposed) return;
    currentMap.on("moveend", onMoveEnd);
    setReady(true);
  } catch {
    if (!disposed) labelText.value = "Не удалось загрузить данные карты";
  }
});

watch(
  () => [props.mode, props.workspace, props.shouldFitWorkspace] as const,
  () => {
    if (props.mode === "workspace") {
      renderWorkspace();
    }
  },
);

onBeforeUnmount(() => {
  disposed = true;
  setReady(false);
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
  if (!layer || !auth.isAuthenticated) {
    disconnectRealtime();
    return;
  }

  await handleRealtimeLayerChange(layer, auth.isAuthenticated);
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
.startupError {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: grid;
  place-items: center;
  padding: 20px;
  overflow: auto;
  background: #f8fafc;
}
.startupErrorMessage {
  box-sizing: border-box;
  min-width: 0;
  width: 100%;
  max-width: 560px;
  padding: 24px;
  border: 1px solid #e5b4b4;
  border-left: 4px solid #b42318;
  border-radius: 6px;
  background: #fff;
  overflow-wrap: anywhere;
}
.startupErrorMessage h2 {
  margin: 0 0 10px;
  color: #9f241b;
  font-size: 19px;
}
.startupErrorMessage p {
  margin: 0;
  color: #334155;
  line-height: 1.5;
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
