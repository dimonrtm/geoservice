<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useWorkspaceRecoveryStore } from "@/stores/workspaceRecovery";
import { useWorkOrdersStore } from "@/stores/workOrders";
import { useAuthStore } from "@/stores/auth";
import { containDialogFocus } from "@/domain/dialogFocus";
const recovery = useWorkspaceRecoveryStore(),
  workspace = useWorkOrdersStore(),
  auth = useAuthStore();
const records = computed(() =>
  Object.values(recovery.records).filter(
    (r) =>
      auth.user?.id === r.command.actorId &&
      workspace.items.some((w) => w.id === r.command.target.workOrderId),
  ),
);
const confirmation = ref<{
    key: string;
    commandId: string;
    epoch: number;
  } | null>(null),
  dialog = ref<HTMLDialogElement | null>(null);
let origin: HTMLElement | null = null;
async function confirm(key: string, commandId: string) {
  origin = document.activeElement as HTMLElement;
  confirmation.value = { key, commandId, epoch: auth.sessionEpoch };
  await nextTick();
  dialog.value?.showModal();
  dialog.value?.querySelector("button")?.focus();
}
function close() {
  confirmation.value = null;
  if (origin?.isConnected) origin.focus();
}
function resume() {
  const c = confirmation.value;
  close();
  if (c) void recovery.resumeAfterAccess(c.key, c.commandId, c.epoch);
}
watch(() => auth.sessionEpoch, close);
function label(id: string) {
  return workspace.items.find((w) => w.id === id)?.code ?? id;
}
</script>
<template>
  <section
    v-if="records.length || recovery.storageError"
    class="recoveryList"
    aria-labelledby="recovery-heading"
  >
    <h2 id="recovery-heading">Восстановление команд</h2>
    <p v-if="recovery.storageError" role="alert">{{ recovery.storageError }}</p>
    <article
      v-for="record in records"
      :key="record.key"
      :data-test="`recovery-${record.command.target.workOrderId}`"
    >
      <strong>{{ label(record.command.target.workOrderId) }}</strong>
      <p role="status">
        {{
          record.requiresAccessConfirmation
            ? "Восстановление остановлено после потери доступа"
            : record.blocks.length
              ? "Требуется ручной разбор"
              : (recovery.readbackErrors[record.key] ??
                (record.outcome.kind === "succeeded"
                  ? "Прежняя операция выполнена. Загружаем актуальные данные"
                  : record.outcome.kind === "rejected"
                    ? "Прежняя операция отклонена"
                    : recovery.phases[record.key] === "sending"
                      ? "Повторяем прежнюю команду"
                      : recovery.phases[record.key] === "retry-wait"
                        ? "Ожидаем повторной попытки"
                        : "Результат операции неизвестен"))
        }}
      </p>
      <button
        v-if="record.requiresAccessConfirmation"
        type="button"
        data-test="resume-recovery"
        @click="confirm(record.key, record.command.request.commandId)"
      >
        Продолжить восстановление
      </button>
      <button
        v-else-if="
          !record.blocks.length &&
          record.outcome.kind === 'unknown' &&
          recovery.phases[record.key] === 'unknown'
        "
        type="button"
        @click="recovery.retry(record.key)"
      >
        Повторить запрос
      </button>
      <button
        v-else-if="!record.blocks.length && recovery.readbackErrors[record.key]"
        type="button"
        @click="recovery.retryRead(record.key)"
      >
        Повторить загрузку
      </button>
      <details v-if="record.blocks.some((b) => b !== 'access')">
        <summary>Данные для ручного разбора</summary>
        <p>
          Сохраните идентификаторы и описание действий для разбора дефекта. Не
          удаляйте контекст и не создавайте новую команду вместо прежней.
        </p>
        <dl>
          <dt>CommandId</dt>
          <dd>{{ record.command.request.commandId }}</dd>
          <dt>WorkOrderId</dt>
          <dd>{{ record.command.target.workOrderId }}</dd>
          <dt>EditVersionId</dt>
          <dd>{{ record.command.target.editVersionId }}</dd>
          <template v-if="record.outcome.kind === 'rejected'"
            ><dt>Код</dt>
            <dd>{{ record.outcome.error.code }}</dd>
            <dt>CorrelationId</dt>
            <dd>
              {{ record.outcome.error.correlationId ?? "Недоступен" }}
            </dd></template
          >
        </dl>
      </details>
    </article>
    <dialog
      v-if="confirmation"
      ref="dialog"
      aria-labelledby="resume-title"
      @cancel.prevent="close"
      @keydown="containDialogFocus"
    >
      <h3 id="resume-title">Продолжить восстановление этой команды?</h3>
      <p>Результат уже отправленной команды будет уточнён в текущей сессии.</p>
      <button type="button" @click="close">Отмена</button
      ><button type="button" data-test="confirm-resume" @click="resume">
        Продолжить
      </button>
    </dialog>
  </section>
</template>
<style scoped>
.recoveryList {
  padding: 12px;
  max-height: 40vh;
  overflow: auto;
  flex-shrink: 0;
}
h2 {
  font-size: 16px;
}
article {
  border: 1px solid #cbd5e1;
  padding: 8px;
  margin-top: 8px;
  font-size: 13px;
}
button {
  min-height: 44px;
  padding: 8px;
  margin: 4px;
}
dd {
  margin: 0;
  overflow-wrap: anywhere;
}
dialog {
  max-width: min(440px, calc(100vw - 48px));
}
dialog::backdrop {
  background: #0f172a80;
}
</style>
