<script setup lang="ts">
import { computed, ref } from "vue";

import ActionableError from "@/components/ActionableError.vue";
import type { ErrorActionId, ErrorPresentation } from "@/contracts/api-error";
import type {
  EditVersionStatus,
  WorkOrderStatus,
  WorkOrderSummary,
  WorkspaceResponse,
} from "@/contracts/work-orders";

const props = defineProps<{
  workOrder: WorkOrderSummary;
  workspace: WorkspaceResponse | null;
  isOpening: boolean;
  isOpenActionDisabled: boolean;
  error: ErrorPresentation | null;
}>();

const emit = defineEmits<{
  open: [];
  errorAction: [actionId: ErrorActionId];
}>();

const titleRef = ref<HTMLHeadingElement | null>(null);

const workOrderStatusText = computed(() =>
  workOrderStatusLabel(props.workOrder.status),
);
const actionText = computed(() => {
  if (props.isOpening) {
    return "Открываем…";
  }
  return props.workOrder.status === "in_progress" ? "Продолжить" : "Начать";
});

function workOrderStatusLabel(status: WorkOrderStatus): string {
  return status === "in_progress" ? "В работе" : "Назначен";
}

function editVersionStatusLabel(status: EditVersionStatus): string {
  return status === "open" ? "Открыта" : status;
}

function focusHeading(): void {
  titleRef.value?.focus();
}

defineExpose({ focusHeading });
</script>

<template>
  <section
    class="workspaceDetailsPanel"
    data-test="workspace-details-panel"
    aria-labelledby="workspace-details-title"
    :aria-busy="props.isOpening ? 'true' : 'false'"
  >
    <header class="detailsHeader">
      <div class="detailsIdentity">
        <div class="detailsContext">
          <span class="workOrderCode" data-test="workspace-code">
            {{ props.workOrder.code }}
          </span>
          <span class="statusBadge" data-test="workspace-status">
            {{ workOrderStatusText }}
          </span>
        </div>
        <h2
          id="workspace-details-title"
          ref="titleRef"
          data-test="workspace-details-title"
          tabindex="-1"
        >
          {{ props.workOrder.title }}
        </h2>
      </div>
    </header>

    <dl
      v-if="props.workspace"
      class="detailsGrid"
      data-test="workspace-details-grid"
    >
      <div class="detailItem isAoi">
        <dt>Область работ</dt>
        <dd data-test="workspace-aoi">
          {{ props.workspace.workOrder.scope.aoi.name }}
        </dd>
      </div>
      <div class="detailItem">
        <dt>Версия</dt>
        <dd data-test="workspace-version-status">
          {{
            editVersionStatusLabel(props.workspace.workOrder.editVersion.status)
          }}
        </dd>
      </div>
      <div class="detailItem">
        <dt>Базовая ревизия</dt>
        <dd data-test="workspace-base-revision">
          {{ props.workspace.workOrder.editVersion.baseNetworkRevision }}
        </dd>
      </div>
      <div class="detailItem">
        <dt>Объекты</dt>
        <dd data-test="workspace-feature-count">
          {{ props.workspace.workOrder.editVersion.features.features.length }}
        </dd>
      </div>
      <div class="detailItem">
        <dt>Связи</dt>
        <dd data-test="workspace-association-count">
          {{ props.workspace.workOrder.editVersion.associations.length }}
        </dd>
      </div>
    </dl>

    <div v-else class="previewBody">
      <p
        v-if="props.workOrder.description"
        class="workOrderDescription"
        data-test="workspace-description"
      >
        {{ props.workOrder.description }}
      </p>

      <ActionableError
        v-if="props.error"
        id="workspace-open-error"
        :presentation="props.error"
        @action="emit('errorAction', $event)"
      />

      <button
        v-else
        class="openAction"
        type="button"
        data-test="workspace-open-action"
        :disabled="props.isOpenActionDisabled"
        @click="emit('open')"
      >
        {{ actionText }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.workspaceDetailsPanel {
  flex: 0 0 auto;
  min-width: 0;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.1);
  background: #fff;
  color: #0f172a;
}

.detailsHeader,
.detailsIdentity {
  min-width: 0;
}

.detailsContext {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 4px;
}

.workOrderCode {
  color: #166534;
  font-size: 12px;
  font-weight: 800;
}

.statusBadge {
  border-radius: 999px;
  padding: 2px 8px;
  background: #ecfdf5;
  color: #166534;
  font-size: 12px;
  font-weight: 700;
}

h2 {
  margin: 0;
  overflow-wrap: anywhere;
  font-size: 18px;
  line-height: 1.3;
}

h2:focus-visible {
  outline: 3px solid rgba(22, 101, 52, 0.35);
  outline-offset: 4px;
}

.previewBody {
  display: grid;
  justify-items: start;
  gap: 10px;
  margin-top: 10px;
}

.workOrderDescription {
  margin: 0;
  line-height: 1.4;
}

.workOrderDescription {
  color: #475569;
  font-size: 14px;
}

.openAction {
  min-width: 112px;
  border: 1px solid #166534;
  border-radius: 8px;
  padding: 8px 12px;
  background: #166534;
  color: #fff;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.openAction:disabled {
  opacity: 0.7;
  cursor: wait;
}

.detailsGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 12px;
  margin: 12px 0 0;
}

.detailItem {
  min-width: 0;
}

.detailItem.isAoi {
  grid-column: span 2;
}

dt {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

dd {
  margin: 2px 0 0;
  overflow-wrap: anywhere;
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

@media (max-width: 760px) {
  .workspaceDetailsPanel {
    padding: 12px;
  }

  .detailsGrid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px 12px;
  }

  .detailItem.isAoi {
    grid-column: 1 / -1;
  }
}
</style>
