<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useWorkOrdersStore } from "@/stores/workOrders";
import { presentWorkspaceCommands } from "@/domain/workspaceCommandPresentation";

const store = useWorkOrdersStore();
const auth = useAuthStore();
const editPanelHeading = ref<HTMLHeadingElement | null>(null);
const dialog = ref<HTMLDialogElement | null>(null);
let previousFocus: HTMLElement | null = null;
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
  () => store.revertConfirmation?.phase,
  async (phase, oldPhase) => {
    if (phase) {
      if (!oldPhase)
        previousFocus = document.activeElement as HTMLElement | null;
      await nextTick();
      if (store.revertConfirmation?.phase !== phase) return;
      if (dialog.value && !dialog.value.open) dialog.value.showModal();
      dialog.value?.querySelector<HTMLButtonElement>("button")?.focus();
    } else {
      const ownedFocus =
        dialog.value?.contains(document.activeElement) ||
        document.activeElement === document.body;
      if (dialog.value?.open) dialog.value.close();
      await nextTick();
      if (!ownedFocus) return;
      if (
        previousFocus?.isConnected &&
        !(previousFocus instanceof HTMLButtonElement && previousFocus.disabled)
      )
        previousFocus.focus();
      else editPanelHeading.value?.focus();
    }
  },
);
function closeRevert() {
  const id = store.revertConfirmation?.confirmationId;
  if (id) store.cancelRevert(id);
}
function proceedRevert() {
  const context = store.revertConfirmation;
  if (!context) return;
  if (context.phase === "resolve-dirty")
    store.discardLocalDraftForRevert(context.confirmationId);
  else void store.confirmRevert(context.confirmationId);
}
function dialogKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    event.preventDefault();
    event.stopPropagation();
    closeRevert();
  }
  if (event.key !== "Tab") return;
  const buttons = dialog.value?.querySelectorAll<HTMLButtonElement>("button");
  if (!buttons?.length) return;
  const first = buttons[0]!,
    last = buttons[buttons.length - 1]!;
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
onBeforeUnmount(closeRevert);

async function focusAfterAction(origin: EventTarget | null) {
  await nextTick();
  if (
    origin instanceof HTMLButtonElement &&
    (origin.disabled || !origin.isConnected) &&
    (document.activeElement === origin ||
      document.activeElement === document.body)
  )
    editPanelHeading.value?.focus();
}
function save(event: MouseEvent) {
  if (!view.value.canSave) return;
  void store.saveLocalDraft();
  void focusAfterAction(event.currentTarget);
}
function cancel(event: MouseEvent) {
  if (!view.value.canCancel) return;
  store.discardLocalChangesKeepingSelection();
  void focusAfterAction(event.currentTarget);
}
function revert() {
  if (view.value.canRevert) store.beginRevert();
}
function recover(event: MouseEvent, action: "command" | "read" | "discard") {
  if (action === "command" && view.value.canRetryCommand)
    void store.retryPendingSave();
  if (action === "read" && view.value.canRetryRead)
    void store.refreshCurrentWorkspace();
  if (action === "discard" && view.value.canDiscardRejectedAttempt)
    store.discardRejectedAttempt();
  void focusAfterAction(event.currentTarget);
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
    </div>
    <div class="commandButtons">
      <button
        v-if="view.canRetryCommand"
        data-test="retry-command"
        type="button"
        @click="recover($event, 'command')"
      >
        Повторить запрос
      </button>
      <button
        v-if="view.canRetryRead"
        data-test="retry-read"
        type="button"
        @click="recover($event, 'read')"
      >
        Повторить загрузку
      </button>
      <button
        v-if="view.canDiscardRejectedAttempt"
        data-test="discard-rejected"
        type="button"
        @click="recover($event, 'discard')"
      >
        Отказаться от попытки
      </button>
    </div>
    <dialog
      v-if="store.revertConfirmation"
      ref="dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="revert-title"
      aria-describedby="revert-description"
      @cancel.prevent="closeRevert"
      @keydown="dialogKeydown"
    >
      <h3 id="revert-title">
        {{
          store.revertConfirmation.phase === "resolve-dirty"
            ? "Отказаться от локальной правки?"
            : "Вернуть исходную геометрию?"
        }}
      </h3>
      <p
        v-if="store.revertConfirmation.phase === 'resolve-dirty'"
        id="revert-description"
      >
        Локальная правка будет окончательно отменена. Отмена следующего
        подтверждения не восстановит её.
      </p>
      <p v-else id="revert-description">
        Линия вернётся к исходной геометрии, сохранённое отличие исчезнет.
        История останется. Это не подтверждает позиционную точность или
        топологию.
      </p>
      <div class="commandButtons">
        <button type="button" data-test="revert-safe" @click="closeRevert">
          {{
            store.revertConfirmation.phase === "resolve-dirty"
              ? "Продолжить редактирование"
              : "Отмена"
          }}
        </button>
        <button type="button" data-test="revert-proceed" @click="proceedRevert">
          {{
            store.revertConfirmation.phase === "resolve-dirty"
              ? "Отказаться от локальной правки"
              : "Вернуть исходную геометрию"
          }}
        </button>
      </div>
    </dialog>
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
dialog {
  max-width: min(480px, calc(100vw - 48px));
  max-height: calc(100dvh - 48px);
  overflow: auto;
  border: 1px solid #94a3b8;
  border-radius: 8px;
  padding: 16px;
  color: #0f172a;
}
dialog::backdrop {
  background: #0f172a80;
}
dialog h3 {
  margin-top: 0;
}
dialog .commandButtons {
  margin-top: 16px;
}
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
