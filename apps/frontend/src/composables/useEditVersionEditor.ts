import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { fetchEditVersionMap } from "@/api/editVersionMap";
import { fetchEditVersionChangeSet } from "@/api/editVersionChangeSet";
import { fetchFeatureBaseline } from "@/api/featureBaseline";
import { parseWorkspaceResponse } from "@/contracts/workspace-edit";
import type { WorkspaceResponse } from "@/contracts/work-orders";
import { useEditVersionMapStore } from "@/stores/editVersionMap";
import { useEditVersionChangeSetStore } from "@/stores/editVersionChangeSet";
import { useFeatureBaselineStore } from "@/stores/featureBaseline";

import { projectMap } from "./readEditVersionSnapshot";
export { readEditVersionSnapshot } from "./readEditVersionSnapshot";

export const useEditVersionEditor = defineStore("editVersionEditor", () => {
  const editVersionMap = useEditVersionMapStore(),
    changes = useEditVersionChangeSetStore(),
    baseline = useFeatureBaselineStore();
  const selected = ref<string | null>(null);
  let generation = 0;
  const snapshot = computed(() =>
    editVersionMap.data
      ? projectMap(editVersionMap.data, changes.data, baseline.data)
      : null,
  );
  const failedMapRefresh = computed(
    () => editVersionMap.phase === "error" && editVersionMap.data !== null,
  );
  const canRetry = computed(
    () =>
      failedMapRefresh.value ||
      changes.phase === "error" ||
      baseline.phase === "error",
  );
  const readError = computed(() =>
    failedMapRefresh.value
      ? "Не удалось обновить карту рабочей версии."
      : changes.phase === "error"
        ? "Не удалось загрузить изменения рабочей версии."
        : baseline.phase === "error"
          ? "Не удалось загрузить исходную геометрию линии."
          : null,
  );
  function reset() {
    generation++;
    editVersionMap.reset();
    changes.reset();
    baseline.reset();
    selected.value = null;
  }
  function clearFeatureSelection() {
    if (changes.data?.changeSet) return;
    selected.value = null;
    baseline.reset();
  }
  function readyFor(featureId: string) {
    return (
      editVersionMap.data !== null &&
      editVersionMap.phase === "ready" &&
      changes.data !== null &&
      changes.phase === "ready" &&
      editVersionMap.data.workOrder.editVersion.draftVersionToken ===
        changes.data.draftVersionToken &&
      (!changes.data.changeSet ||
        changes.data.changeSet.featureId === featureId) &&
      baseline.phase === "ready" &&
      baseline.data?.featureId === featureId
    );
  }
  async function selectFeature(featureId: string, manualRetry = false) {
    const order = editVersionMap.data?.workOrder;
    if (
      order &&
      (!changes.data ||
        editVersionMap.phase === "loading" ||
        order.editVersion.draftVersionToken !==
          changes.data.draftVersionToken) &&
      order.editVersion.features.features.some(
        (feature) => feature.id === featureId,
      )
    ) {
      selected.value = featureId;
      return;
    }
    if (
      !order ||
      changes.phase !== "ready" ||
      !changes.data ||
      order.editVersion.draftVersionToken !== changes.data.draftVersionToken ||
      (changes.data.changeSet && changes.data.changeSet.featureId !== featureId)
    )
      return;
    if (
      selected.value === featureId &&
      (readyFor(featureId) ||
        baseline.phase === "loading" ||
        (baseline.phase === "error" && !manualRetry))
    )
      return;
    selected.value = featureId;
    const changeResult = changes.data;
    const mapResult = editVersionMap.data!;
    await baseline.load(async (signal) => {
      const result = await fetchFeatureBaseline(
        order.id,
        order.editVersion.id,
        featureId,
        signal,
      );
      if (changeResult.changeSet)
        parseWorkspaceResponse(
          projectMap(mapResult, changeResult, result),
          order.id,
          order.editVersion.id,
        );
      return result;
    }, true);
  }
  async function synchronize(
    run: number,
    workOrderId: string,
    editVersionId: string,
    onMap?: (map: WorkspaceResponse) => void,
    readMap = true,
  ) {
    while (run === generation) {
      if (readMap) {
        const result = await editVersionMap.load(
          (s) => fetchEditVersionMap(workOrderId, editVersionId, s),
          false,
          true,
        );
        if (!result || run !== generation) return null;
        onMap?.(projectMap(result, null, null));
      }
      const change = await changes.load(
        (s) => fetchEditVersionChangeSet(workOrderId, editVersionId, s),
        true,
      );
      if (run !== generation || !change) return null;
      if (
        editVersionMap.data?.workOrder.editVersion.draftVersionToken !==
        change.draftVersionToken
      ) {
        baseline.reset();
        readMap = true;
        continue;
      }
      const featureId = change.changeSet?.featureId ?? selected.value;
      if (
        featureId &&
        (change.changeSet ||
          editVersionMap.data?.workOrder.editVersion.features.features.some(
            (feature) => feature.id === featureId,
          ))
      )
        await selectFeature(featureId);
      return run === generation ? snapshot.value : null;
    }
    return null;
  }
  async function open(
    workOrderId: string,
    editVersionId: string,
    onMap?: (map: WorkspaceResponse) => void,
  ) {
    reset();
    return synchronize(generation, workOrderId, editVersionId, onMap);
  }
  async function retry() {
    const order = editVersionMap.data?.workOrder;
    if (!order) return;
    if (failedMapRefresh.value || changes.phase === "error")
      await synchronize(
        generation,
        order.id,
        order.editVersion.id,
        undefined,
        failedMapRefresh.value,
      );
    else if (baseline.phase === "error" && selected.value)
      await selectFeature(selected.value, true);
  }
  function applyReadback(value: WorkspaceResponse) {
    const previous = editVersionMap.data?.workOrder;
    const same =
      previous?.id === value.workOrder.id &&
      previous.editVersion.id === value.workOrder.editVersion.id;
    const oldBaseline = same ? baseline.data : null;
    reset();
    const { hasPersistedChangeSet, basicValidation, changeSet, ...version } =
      value.workOrder.editVersion;
    editVersionMap.accept({
      workOrder: { ...value.workOrder, editVersion: version },
    });
    changes.accept({
      draftVersionToken: version.draftVersionToken,
      hasPersistedChangeSet,
      basicValidation,
      changeSet: changeSet
        ? {
            featureId: changeSet.featureId,
            operation: changeSet.operation,
            vertexIndex: changeSet.vertexIndex,
          }
        : null,
    });
    const retained = changeSet
      ? {
          featureId: changeSet.featureId,
          baselineGeometry: changeSet.baselineGeometry,
        }
      : oldBaseline;
    if (
      retained &&
      version.features.features.some((f) => f.id === retained.featureId)
    ) {
      selected.value = retained.featureId;
      baseline.accept(retained);
    }
  }
  return {
    snapshot,
    selected,
    readError,
    canRetry,
    open,
    readyFor,
    selectFeature,
    clearFeatureSelection,
    retry,
    reset,
    applyReadback,
  };
});
