<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { ErrorActionId, ErrorPresentation } from "@/contracts/api-error";

const props = defineProps<{
  presentation: ErrorPresentation;
  id?: string;
}>();

const emit = defineEmits<{
  action: [actionId: ErrorActionId];
}>();

const copyStatus = ref("");
const hasDiagnostics = computed(
  () =>
    props.presentation.diagnostics.code !== null ||
    props.presentation.diagnostics.correlationId !== null,
);

watch(
  () => props.presentation.diagnostics.correlationId,
  () => {
    copyStatus.value = "";
  },
);

async function copyCorrelationId(): Promise<void> {
  const correlationId = props.presentation.diagnostics.correlationId;
  if (!correlationId) {
    return;
  }
  try {
    if (!navigator.clipboard) {
      throw new Error("Clipboard API недоступен");
    }
    await navigator.clipboard.writeText(correlationId);
    copyStatus.value = "Код обращения скопирован";
  } catch {
    copyStatus.value = "Не удалось скопировать код обращения";
  }
}

function emitAction(): void {
  const selectedAction = props.presentation.action;
  if (selectedAction) {
    emit("action", selectedAction.id);
  }
}
</script>

<template>
  <div :id="props.id" class="actionableError">
    <div class="errorContent" role="alert">
      <p class="errorSummary">{{ props.presentation.summary }}</p>
      <p v-if="props.presentation.guidance" class="errorGuidance">
        {{ props.presentation.guidance }}
      </p>
    </div>

    <button
      v-if="props.presentation.action"
      class="errorAction"
      data-test="error-action"
      type="button"
      @click="emitAction"
    >
      {{ props.presentation.action.label }}
    </button>

    <details v-if="hasDiagnostics" class="errorDiagnostics">
      <summary>Технические сведения</summary>
      <dl>
        <div v-if="props.presentation.diagnostics.code">
          <dt>Код ошибки</dt>
          <dd data-test="error-code">
            {{ props.presentation.diagnostics.code }}
          </dd>
        </div>
        <div v-if="props.presentation.diagnostics.correlationId">
          <dt>Код обращения</dt>
          <dd data-test="correlation-id">
            {{ props.presentation.diagnostics.correlationId }}
          </dd>
        </div>
      </dl>
      <button
        v-if="props.presentation.diagnostics.correlationId"
        data-test="copy-correlation-id"
        type="button"
        @click="copyCorrelationId"
      >
        Копировать код обращения
      </button>
    </details>

    <p
      class="copyStatus"
      data-test="copy-status"
      aria-live="polite"
      aria-atomic="true"
    >
      {{ copyStatus }}
    </p>
  </div>
</template>

<style scoped>
.actionableError {
  display: grid;
  justify-items: start;
  gap: 10px;
  color: #991b1b;
}

.errorSummary,
.errorGuidance,
.copyStatus {
  margin: 0;
  line-height: 1.4;
}

.errorSummary {
  font-weight: 700;
}

.errorGuidance,
.errorDiagnostics,
.copyStatus {
  font-size: 13px;
}

.errorAction,
.errorDiagnostics button {
  border: 1px solid rgba(153, 27, 27, 0.3);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
  color: #7f1d1d;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.errorDiagnostics dl {
  display: grid;
  gap: 8px;
  margin: 8px 0;
}

.errorDiagnostics dt {
  color: #64748b;
}

.errorDiagnostics dd {
  margin: 2px 0 0;
  overflow-wrap: anywhere;
  color: #0f172a;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}

.copyStatus:empty {
  display: none;
}
</style>
