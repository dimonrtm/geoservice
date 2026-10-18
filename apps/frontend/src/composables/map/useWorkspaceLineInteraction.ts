import { computed, onBeforeUnmount, ref, watch, type Ref } from "vue";
import { Marker, type Map, type MapMouseEvent } from "maplibre-gl";
import type { WorkspaceResponse } from "@/contracts/work-orders";
import { isLocalDraftDirty } from "@/domain/workspaceDraft";
import {
  vertexMoveBlockReason,
  lineSelectionBlockReason,
} from "@/domain/workspaceLineInteraction";
import { useWorkOrdersStore } from "@/stores/workOrders";
import { useAuthStore } from "@/stores/auth";
import { setWorkspaceDraftData } from "@/map/workspace-layers";

export function useWorkspaceLineInteraction(
  map: Ref<Map>,
  workspace: Ref<WorkspaceResponse>,
) {
  const store = useWorkOrdersStore();
  const auth = useAuthStore();
  const message = ref("");
  const choices = ref<Array<{ id: string; label: string }>>([]);
  const confirmation = ref<{
    featureId: string | null;
    draft: typeof store.localDraft;
  } | null>(null);
  let marker: Marker | null = null;
  let markerTarget: string | null = null;
  let disposed = false;
  let suppressClick = false;
  let clickTimer: ReturnType<typeof setTimeout> | undefined;
  const contextKey = computed(
    () =>
      `${auth.user?.id ?? ""}:${store.activeWorkspaceKey ?? ""}:${workspace.value.workOrder.editVersion.draftVersionToken}`,
  );
  const available = computed(
    () =>
      auth.isAuthenticated &&
      auth.user?.role === "editor" &&
      store.activeWorkspace === workspace.value &&
      !store.recoveryRecord &&
      !store.storageError &&
      !["FEATURE_NOT_EDITABLE", "WORK_ORDER_CONTEXT_INVALID"].includes(
        store.saveError ?? "",
      ) &&
      ["idle", "editing", "rejected"].includes(store.phase),
  );

  function removeMarker() {
    clearTimeout(clickTimer);
    suppressClick = false;
    marker?.off("dragstart", startDrag);
    marker?.off("drag", drag);
    marker?.off("dragend", endDrag);
    marker?.remove();
    marker = null;
    markerTarget = null;
  }
  function startDrag() {
    suppressClick = true;
    clearTimeout(clickTimer);
  }
  function endDrag() {
    suppressClick = true;
    clearTimeout(clickTimer);
    clickTimer = setTimeout(() => {
      suppressClick = false;
    }, 0);
  }
  function drag() {
    const draft = store.localDraft;
    if (
      disposed ||
      !available.value ||
      !draft ||
      !marker ||
      markerTarget !== draft.featureId
    )
      return;
    const { lng, lat } = marker.getLngLat();
    const xy: [number, number] = [lng, lat];
    const candidate = {
      ...draft.candidateGeometry,
      coordinates: draft.candidateGeometry.coordinates.map((point, i) =>
        i === 1 ? xy : ([...point] as [number, number]),
      ),
    };
    const reason = vertexMoveBlockReason(
      candidate,
      workspace.value.workOrder.scope.aoi.geometry,
    );
    if (reason || !store.moveLocalVertex(xy)) {
      marker.setLngLat(draft.candidateGeometry.coordinates[1]!);
      message.value =
        reason ??
        "Изменение сейчас недоступно. Завершите восстановление рабочего пространства.";
    } else message.value = "";
  }
  function sync() {
    if (disposed) return;
    const draft = store.localDraft;
    const matching = store.activeWorkspace === workspace.value;
    setWorkspaceDraftData(map.value, workspace.value, matching ? draft : null);
    if (
      !available.value ||
      !draft ||
      lineSelectionBlockReason(workspace.value, draft.featureId)
    ) {
      removeMarker();
      return;
    }
    if (markerTarget !== draft.featureId) {
      removeMarker();
      const element = document.createElement("div");
      element.className = "workspaceVertexHandle";
      element.setAttribute(
        "aria-label",
        "Переместить внутреннюю вершину линии",
      );
      element.title = "Перетащите внутреннюю вершину";
      marker = new Marker({ element, draggable: true, anchor: "center" })
        .setLngLat(draft.candidateGeometry.coordinates[1]!)
        .addTo(map.value);
      marker.on("dragstart", startDrag);
      marker.on("drag", drag);
      marker.on("dragend", endDrag);
      markerTarget = draft.featureId;
    } else marker?.setLngLat(draft.candidateGeometry.coordinates[1]!);
  }
  function select(featureId: string | null) {
    choices.value = [];
    if (!available.value) {
      message.value =
        "Редактирование недоступно: дождитесь завершения сохранения или восстановления.";
      return;
    }
    if (featureId !== null) {
      const reason = lineSelectionBlockReason(workspace.value, featureId);
      if (reason) {
        message.value = reason;
        return;
      }
      if (store.localDraft?.featureId === featureId) {
        message.value = "";
        return;
      }
    }
    if (store.localDraft && isLocalDraftDirty(store.localDraft)) {
      confirmation.value = { featureId, draft: store.localDraft };
      return;
    }
    applySelection(featureId);
  }
  function applySelection(featureId: string | null) {
    if (featureId === null) store.cancelLocalEdit();
    else if (!store.beginLocalEdit(featureId, 1)) {
      message.value =
        "Не удалось выбрать линию. Проверьте состояние рабочей области.";
      return;
    }
    message.value = "";
  }
  function confirmDiscard() {
    const pending = confirmation.value;
    confirmation.value = null;
    if (!pending || !available.value || pending.draft !== store.localDraft)
      return;
    if (pending.featureId !== null) {
      const reason = lineSelectionBlockReason(
        workspace.value,
        pending.featureId,
      );
      if (reason) {
        message.value = reason;
        return;
      }
    }
    if (store.cancelLocalEdit()) applySelection(pending.featureId);
  }
  function click(event: MapMouseEvent) {
    if (suppressClick || confirmation.value || disposed) return;
    if (
      event.originalEvent.target instanceof Element &&
      event.originalEvent.target.closest(
        ".workspaceVertexHandle, .workspaceInteraction",
      )
    )
      return;
    if (!available.value) {
      message.value =
        "Редактирование недоступно: дождитесь завершения сохранения или восстановления.";
      return;
    }
    const layers = [
      "workspace:features:lines",
      "workspace:features:points",
      "workspace:features:polygons",
    ].filter((id) => map.value.getLayer(id));
    if (!layers.length) return;
    const { x, y } = event.point;
    const ids = [
      ...new Set(
        map.value
          .queryRenderedFeatures(
            [
              [x - 5, y - 5],
              [x + 5, y + 5],
            ],
            { layers },
          )
          .map((hit) => String(hit.id)),
      ),
    ];
    const eligible = ids.filter(
      (id) => !lineSelectionBlockReason(workspace.value, id),
    );
    choices.value = [];
    if (eligible.length > 1) {
      message.value = "";
      choices.value = eligible.map((id) => {
        const feature =
          workspace.value.workOrder.editVersion.features.features.find(
            (item) => item.id === id,
          )!;
        return {
          id,
          label: `${String(feature.properties.assetCode ?? "Линия")} · ${id}`,
        };
      });
    } else if (eligible.length === 1) select(eligible[0]!);
    else if (ids.length)
      message.value = [
        ...new Set(
          ids.map((id) => lineSelectionBlockReason(workspace.value, id)),
        ),
      ].join(" ");
    else select(null);
  }
  watch(
    contextKey,
    () => {
      confirmation.value = null;
      choices.value = [];
      message.value = "";
      removeMarker();
    },
    { flush: "sync" },
  );
  watch(
    available,
    (value) => {
      if (!value) {
        confirmation.value = null;
        choices.value = [];
        removeMarker();
      }
    },
    { flush: "sync" },
  );
  watch(
    () => [workspace.value, store.localDraft, available.value] as const,
    sync,
    { immediate: true, flush: "post" },
  );
  watch(
    map,
    (next, previous) => {
      previous?.off("click", click);
      removeMarker();
      next.on("click", click);
      sync();
    },
    { immediate: true },
  );
  onBeforeUnmount(() => {
    disposed = true;
    clearTimeout(clickTimer);
    map.value.off("click", click);
    removeMarker();
  });
  return { message, choices, confirmation, select, confirmDiscard };
}
