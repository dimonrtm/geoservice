<script setup lang="ts">
import { onMounted } from "vue";

import MapView from "@/components/MapView.vue";
import { useWorkOrdersStore } from "@/stores/workOrders";

const workOrders = useWorkOrdersStore();

onMounted(() => {
  void workOrders.loadAssigned();
});

function statusLabel(status: string): string {
  if (status === "in_progress") {
    return "В работе";
  }
  return "Назначен";
}

function actionLabel(status: string): string {
  if (status === "in_progress") {
    return "Продолжить";
  }
  return "Начать";
}

function canShowOpenAction(workOrderId: string): boolean {
  return (
    workOrders.selectedWorkOrderId === workOrderId &&
    !workOrders.isWorkOrderOpened(workOrderId)
  );
}

function openError(workOrderId: string): string | null {
  return workOrders.openWorkspaceErrorByWorkOrderId[workOrderId] ?? null;
}
</script>

<template>
  <div class="editorShell">
    <aside class="workOrdersPanel" aria-label="Мои наряды">
      <div class="panelHeader">
        <h1>Мои наряды</h1>
        <button
          class="refreshButton"
          type="button"
          @click="workOrders.loadAssigned"
        >
          Обновить
        </button>
      </div>

      <div
        v-if="workOrders.isLoading"
        class="panelState"
        aria-live="polite"
        aria-atomic="true"
      >
        Загружаем назначенные наряды...
      </div>

      <div v-else-if="workOrders.errorMessage" class="panelState isError">
        <span role="alert">{{ workOrders.errorMessage }}</span>
        <button
          class="retryButton"
          type="button"
          @click="workOrders.loadAssigned"
        >
          Повторить
        </button>
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

            <div
              v-if="openError(workOrder.id)"
              class="workOrderError"
              role="alert"
              :data-test="`open-work-order-error-${workOrder.id}`"
            >
              {{ openError(workOrder.id) }}
            </div>

            <div
              v-if="canShowOpenAction(workOrder.id)"
              class="workOrderActionRow"
            >
              <button
                class="openWorkspaceButton"
                type="button"
                :data-test="`open-work-order-${workOrder.id}`"
                :disabled="workOrders.isOpeningWorkspace"
                @click="workOrders.openSelectedWorkOrder"
              >
                {{
                  workOrders.isOpeningWorkspace
                    ? "Открываем..."
                    : actionLabel(workOrder.status)
                }}
              </button>
            </div>
          </div>
        </li>
      </ul>
    </aside>

    <section class="mapPane" aria-label="Карта">
      <MapView
        v-if="workOrders.activeWorkspace"
        mode="workspace"
        :workspace="workOrders.activeWorkspace"
        :workspace-key="workOrders.activeWorkspaceKey"
        :should-fit-workspace="
          workOrders.shouldFitWorkspace(workOrders.activeWorkspaceKey)
        "
        @workspace-fitted="workOrders.markWorkspaceFitted"
      />
      <MapView v-else mode="empty" />
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

.refreshButton,
.retryButton {
  border: 1px solid rgba(15, 23, 42, 0.14);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
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

.workOrderError {
  color: #b91c1c;
  font-size: 13px;
  line-height: 1.35;
}

.workOrderActionRow {
  display: flex;
  justify-content: flex-start;
}

.openWorkspaceButton {
  border: 1px solid #166534;
  border-radius: 8px;
  padding: 7px 10px;
  background: #166534;
  color: #fff;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.openWorkspaceButton:disabled {
  opacity: 0.7;
  cursor: wait;
}

.mapPane {
  min-width: 0;
  min-height: 0;
}

@media (max-width: 760px) {
  .editorShell {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(220px, 42%) minmax(260px, 1fr);
  }

  .workOrdersPanel {
    border-right: 0;
    border-bottom: 1px solid rgba(15, 23, 42, 0.1);
  }
}
</style>
