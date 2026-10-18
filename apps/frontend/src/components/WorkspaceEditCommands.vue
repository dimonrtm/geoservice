<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useWorkOrdersStore } from "@/stores/workOrders";
import { presentWorkspaceCommands } from "@/domain/workspaceCommandPresentation";

const store = useWorkOrdersStore();
const auth = useAuthStore();
const editPanelHeading = ref<HTMLHeadingElement | null>(null);
const notice = ref("");
const view = computed(() =>
  presentWorkspaceCommands(
    store,
    auth.isAuthenticated && auth.user?.role === "editor",
  ),
);
const selectedLabel = computed(() => {
  const draft = store.localDraft;
  if (!draft) return "Выберите линию на карте для редактирования";
  const feature =
    store.activeWorkspace?.workOrder.editVersion.features.features.find(
      (f) => f.id === draft.featureId,
    );
  return `Выбрана линия: ${feature?.properties?.assetCode ?? draft.featureId}`;
});
watch(
  [
    () => `${auth.user?.id ?? ""}:${store.activeWorkspaceKey ?? ""}`,
    () => store.localDraft,
  ],
  () => {
    notice.value = "";
  },
);

async function focusAfterAction(origin: EventTarget | null) {
  await nextTick();
  if (
    origin instanceof HTMLButtonElement &&
    origin.disabled &&
    (document.activeElement === origin ||
      document.activeElement === document.body)
  )
    editPanelHeading.value?.focus();
}
function save(event: MouseEvent) {
  if (!view.value.canSave) return;
  notice.value = "";
  void store.saveLocalDraft();
  void focusAfterAction(event.currentTarget);
}
function cancel(event: MouseEvent) {
  if (!view.value.canCancel) return;
  notice.value = "";
  store.discardLocalChangesKeepingSelection();
  void focusAfterAction(event.currentTarget);
}
function revert() {
  if (view.value.canRevert)
    notice.value = "Возврат к исходному состоянию пока недоступен";
}
</script>

<template>
  <section
    class="editCommands"
    aria-labelledby="workspace-edit-heading"
    data-test="workspace-edit-commands"
  >
    <div class="commandHeader">
      <div>
        <h2 id="workspace-edit-heading" ref="editPanelHeading" tabindex="-1">
          Правка линии
        </h2>
        <p class="selection">{{ selectedLabel }}</p>
      </div>
      <div class="commandButtons" role="group" aria-label="Команды правки">
        <button
          type="button"
          class="primary"
          data-test="save-edit"
          :disabled="!view.canSave"
          aria-describedby="workspace-edit-status"
          @click="save"
        >
          Сохранить
        </button>
        <button
          type="button"
          data-test="cancel-edit"
          :disabled="!view.canCancel"
          aria-describedby="workspace-edit-status"
          @click="cancel"
        >
          Отменить
        </button>
        <button
          type="button"
          data-test="revert-edit"
          :disabled="!view.canRevert"
          aria-describedby="workspace-revert-hint workspace-edit-status"
          @click="revert"
        >
          Сбросить
        </button>
      </div>
    </div>
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      class="status"
      :class="view.severity"
    >
      <p id="workspace-edit-status">
        <span v-if="view.busy" class="spinner" aria-hidden="true"></span
        >{{ view.statusText }}
      </p>
      <p v-if="notice" class="notice">{{ notice }}</p>
    </div>
    <p id="workspace-revert-hint" class="hint">
      «Сбросить» — вернуть линию к исходному состоянию.
      <span
        v-if="
          !store.activeWorkspace?.workOrder.editVersion.hasPersistedChangeSet
        "
        >Сохранённых изменений для сброса нет.</span
      >
    </p>
    <p class="quality">{{ view.positionalAccuracyMessage }}</p>
  </section>
</template>

<style scoped>
.editCommands {
  flex: 0 0 auto;
  min-width: 0;
  padding: 12px 16px;
  border-bottom: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
}
.commandHeader {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px 16px;
}
h2 {
  margin: 0;
  font-size: 16px;
}
p {
  margin: 6px 0 0;
  overflow-wrap: anywhere;
  font-size: 13px;
  line-height: 1.4;
}
.selection,
.hint {
  color: #475569;
}
.commandButtons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
button {
  min-height: 44px;
  padding: 8px 14px;
  border: 1px solid #94a3b8;
  border-radius: 6px;
  background: white;
  color: #0f172a;
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}
button.primary {
  background: #166534;
  color: white;
  border-color: #166534;
}
button:disabled {
  background: #e2e8f0;
  border-color: #cbd5e1;
  color: #475569;
  cursor: default;
}
button:focus-visible,
h2:focus {
  outline: 3px solid #2563eb;
  outline-offset: 3px;
}
.error {
  color: #991b1b;
}
.success {
  color: #166534;
}
.notice {
  color: #334155;
}
.quality {
  color: #78350f;
}
.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 8px;
  border: 2px solid #cbd5e1;
  border-top-color: #166534;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
}
@media (max-width: 760px) {
  .editCommands {
    padding: 12px;
  }
}
</style>
