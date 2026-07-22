<script setup lang="ts">
import { RefreshCw } from "@lucide/vue";
import { nextTick, onMounted, ref, watch } from "vue";

import ActionableError from "@/components/ActionableError.vue";
import MapView from "@/components/MapView.vue";
import UiIconButton from "@/components/ui/UiIconButton.vue";
import WorkspaceDetailsPanel from "@/components/WorkspaceDetailsPanel.vue";
import type { ErrorActionId } from "@/contracts/api-error";
import { useAuthStore } from "@/stores/auth";
import { useWorkOrdersStore } from "@/stores/workOrders";

type WorkspaceDetailsPanelHandle = {
  focusHeading(): void;
};

const workOrders = useWorkOrdersStore();
const auth = useAuthStore();
const detailsPanelRef = ref<WorkspaceDetailsPanelHandle | null>(null);
const workspaceAnnouncement = ref("");

watch(
  () => workOrders.selectedWorkOrderId,
  () => {
    workspaceAnnouncement.value = "";
  },
);

onMounted(async () => {
  await workOrders.loadAssigned();
  if (!workOrders.loadError) {
    await workOrders.restoreOpenedWorkspace();
  }
});

function handleLoadErrorAction(actionId: ErrorActionId): void {
  if (actionId === "retry" || actionId === "refresh") {
    void workOrders.loadAssigned();
    return;
  }
  if (actionId === "sign-in") {
    void auth.logout();
  }
}

function handleWorkspaceErrorAction(actionId: ErrorActionId): void {
  if (actionId === "retry") {
    void workOrders.retrySelectedWorkspaceError();
    return;
  }
  if (actionId === "refresh") {
    void workOrders.loadAssigned();
    return;
  }
  if (actionId === "reopen") {
    void workOrders.reopenSelectedWorkOrder();
    return;
  }
  if (actionId === "sign-in") {
    void auth.logout();
  }
}

function statusLabel(status: string): string {
  if (status === "in_progress") {
    return "В работе";
  }
  return "Назначен";
}

async function openSelectedWorkspace(): Promise<void> {
  const workOrderId = workOrders.selectedWorkOrderId;
  if (!workOrderId) {
    return;
  }

  workspaceAnnouncement.value = "";
  await workOrders.openSelectedWorkOrder();

  const workspace = workOrders.activeWorkspace;
  if (
    workOrders.selectedWorkOrderId !== workOrderId ||
    workspace?.workOrder.id !== workOrderId
  ) {
    return;
  }

  workspaceAnnouncement.value = `Рабочее пространство ${workspace.workOrder.code} загружено`;
  await nextTick();
  detailsPanelRef.value?.focusHeading();
}
</script>

<template>
  <div class="editorShell">
    <aside class="workOrdersPanel" aria-label="Мои наряды">
      <div class="panelHeader">
        <h1>Мои наряды</h1>
        <UiIconButton
          :icon="RefreshCw"
          label="Обновить"
          tooltip="Обновить список назначенных нарядов"
          tooltip-align="end"
          variant="secondary"
          :loading="workOrders.isLoading"
          loading-label="Обновление списка нарядов"
          data-test="refresh-work-orders"
          @click="workOrders.loadAssigned"
        />
      </div>

      <div
        v-if="workOrders.isLoading"
        class="panelState"
        aria-live="polite"
        aria-atomic="true"
      >
        Загружаем назначенные наряды...
      </div>

      <div v-else-if="workOrders.loadError" class="panelState isError">
        <ActionableError
          :presentation="workOrders.loadError"
          @action="handleLoadErrorAction"
        />
      </div>

      <div
        v-else-if="workOrders.items.length === 0"
        class="panelState"
        aria-live="polite"
        aria-atomic="true"
      >
        Назначенных нарядов нет.
      </div>

      <ul v-else class="workOrderList">
        <li v-for="workOrder in workOrders.items" :key="workOrder.id">
          <div
            class="workOrderCard"
            :class="{
              isSelected: workOrders.selectedWorkOrderId === workOrder.id,
            }"
          >
            <button
              class="workOrderButton"
              type="button"
              :aria-current="
                workOrders.selectedWorkOrderId === workOrder.id
                  ? 'true'
                  : undefined
              "
              :data-test="`work-order-${workOrder.id}`"
              @click="workOrders.selectWorkOrder(workOrder.id)"
            >
              <span class="workOrderCode">{{ workOrder.code }}</span>
              <span class="workOrderTitle">{{ workOrder.title }}</span>
              <span class="workOrderStatus">{{
                statusLabel(workOrder.status)
              }}</span>
              <span v-if="workOrder.description" class="workOrderDescription">
                {{ workOrder.description }}
              </span>
            </button>
          </div>
        </li>
      </ul>
    </aside>

    <section class="workspacePane" aria-label="Рабочая область">
      <WorkspaceDetailsPanel
        v-if="workOrders.selectedWorkOrder"
        ref="detailsPanelRef"
        :work-order="workOrders.selectedWorkOrder"
        :workspace="workOrders.activeWorkspace"
        :is-opening="
          workOrders.openingWorkOrderId === workOrders.selectedWorkOrder.id
        "
        :is-open-action-disabled="workOrders.isOpeningWorkspace"
        :error="workOrders.selectedOpenWorkspaceError"
        @open="openSelectedWorkspace"
        @error-action="handleWorkspaceErrorAction"
      />

      <p
        class="srOnly"
        data-test="workspace-announcement"
        aria-live="polite"
        aria-atomic="true"
      >
        {{ workspaceAnnouncement }}
      </p>

      <MapView
        v-if="workOrders.activeWorkspace"
        class="workspaceMap"
        mode="workspace"
        :workspace="workOrders.activeWorkspace"
        :workspace-key="workOrders.activeWorkspaceKey"
        :should-fit-workspace="
          workOrders.shouldFitWorkspace(workOrders.activeWorkspaceKey)
        "
        @workspace-fitted="workOrders.markWorkspaceFitted"
      />
      <MapView v-else class="workspaceMap" mode="empty" />
    </section>
  </div>
</template>

<style scoped>
.editorShell {
  height: 100%;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
}

.workOrdersPanel {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(15, 23, 42, 0.1);
  background: #f8fafc;
}

.panelHeader {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.panelHeader h1 {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
  color: #0f172a;
}

.panelState {
  padding: 16px;
  color: #475569;
  font-size: 14px;
  line-height: 1.4;
}

.panelState.isError {
  display: grid;
  gap: 10px;
  color: #991b1b;
}

.workOrderList {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  display: grid;
  align-content: start;
  gap: 8px;
  margin: 0;
  padding: 12px;
  list-style: none;
}

.workOrderCard {
  display: grid;
  gap: 8px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}

.workOrderCard.isSelected {
  border-color: #166534;
  box-shadow: inset 3px 0 0 #166534;
}

.workOrderButton {
  width: 100%;
  display: grid;
  gap: 5px;
  padding: 0;
  text-align: left;
  border: 0;
  background: transparent;
  font: inherit;
  cursor: pointer;
}

.workOrderCode {
  font-size: 12px;
  font-weight: 800;
  color: #166534;
}

.workOrderTitle {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.workOrderStatus,
.workOrderDescription {
  font-size: 13px;
  line-height: 1.35;
  color: #475569;
}

.workspacePane {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.workspaceMap {
  flex: 1 1 auto;
  min-height: 0;
}

.srOnly {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 760px) {
  .editorShell {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(220px, 42%) minmax(420px, 1fr);
    overflow-y: auto;
  }

  .workOrdersPanel {
    border-right: 0;
    border-bottom: 1px solid rgba(15, 23, 42, 0.1);
  }

  .workspaceMap {
    min-height: 220px;
  }
}
</style>
