<script setup lang="ts">
import {
  Copy,
  FolderOpen,
  LogIn,
  RefreshCw,
  RotateCcw,
  type LucideIcon,
} from "@lucide/vue";
import { computed, ref, watch } from "vue";

import UiButton from "@/components/ui/UiButton.vue";
import type { ErrorActionId, ErrorPresentation } from "@/contracts/api-error";

const props = defineProps<{
  presentation: ErrorPresentation;
  id?: string;
}>();

const emit = defineEmits<{
  action: [actionId: ErrorActionId];
}>();

const copyStatus = ref("");
const isCopying = ref(false);

const errorActionIcons: Record<ErrorActionId, LucideIcon> = {
  retry: RotateCcw,
  refresh: RefreshCw,
  reopen: FolderOpen,
  "sign-in": LogIn,
};

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

  isCopying.value = true;
  try {
    if (!navigator.clipboard) {
      throw new Error("Clipboard API недоступен");
    }
    await navigator.clipboard.writeText(correlationId);
    copyStatus.value = "Код обращения скопирован";
  } catch {
    copyStatus.value = "Не удалось скопировать код обращения";
  } finally {
    isCopying.value = false;
  }
}

function errorActionIcon(actionId: ErrorActionId): LucideIcon {
  return errorActionIcons[actionId];
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

    <UiButton
      v-if="props.presentation.action"
      :icon="errorActionIcon(props.presentation.action.id)"
      variant="error"
      data-test="error-action"
      @click="emitAction"
    >
      {{ props.presentation.action.label }}
    </UiButton>

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
      <UiButton
        v-if="props.presentation.diagnostics.correlationId"
        :icon="Copy"
        variant="error"
        :loading="isCopying"
        loading-label="Копируем…"
        :aria-label="isCopying ? 'Копируем код обращения' : undefined"
        data-test="copy-correlation-id"
        @click="copyCorrelationId"
      >
        Копировать код обращения
      </UiButton>
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
