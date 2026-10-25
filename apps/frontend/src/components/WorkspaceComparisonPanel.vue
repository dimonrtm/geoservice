<script setup lang="ts">
import { computed } from "vue";
import { useWorkOrdersStore } from "@/stores/workOrders";
import { comparisonRows } from "@/domain/workspaceComparison";
import { isLineStringXY } from "@/contracts/workspace-edit";
const store = useWorkOrdersStore();
const rows = computed(() => {
  const m = store.activeComparison;
  if (!m) return [];
  const g = store.activeWorkspace?.workOrder.editVersion.features.features.find(
    (f) => f.id === m.featureId,
  )?.geometry;
  return comparisonRows(
    m.source?.geometry ?? null,
    m.candidate,
    isLineStringXY(g) ? g : null,
  );
});
</script>
<template>
  <section
    v-if="store.activeComparison"
    class="comparison"
    aria-labelledby="comparison-heading"
    data-test="stale-comparison"
  >
    <h3 id="comparison-heading">Сравнение несохранённой попытки</h3>
    <p>
      Данные изменились. Попытка не перенесена на актуальную линию. Предпросмотр
      не изменяет данные.
    </p>
    <p v-if="!store.activeComparison.source">
      Исходные данные прежней попытки недоступны.
    </p>
    <div role="group" aria-label="Предпросмотр линии">
      <button
        v-for="option in [
          { id: 'source', label: 'Исходная' },
          { id: 'candidate', label: 'Попытка' },
          { id: 'current', label: 'Актуальная' },
        ] as const"
        :key="option.id"
        type="button"
        :disabled="option.id === 'source' && !store.activeComparison.source"
        :aria-pressed="store.comparisonPreview === option.id"
        @click="store.comparisonPreview = option.id"
      >
        {{ option.label }}
      </button>
      <button type="button" @click="store.comparisonPreview = null">
        Скрыть предпросмотр
      </button>
    </div>
    <div class="tableScroll">
      <table>
        <caption>
          Координаты XY; каждая строка — вершина линии
        </caption>
        <thead>
          <tr>
            <th>Вершина</th>
            <th>Исходная</th>
            <th>Попытка</th>
            <th>Актуальная</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.index">
            <th>{{ row.index + 1 }}</th>
            <td>{{ row.source?.join(", ") ?? "Недоступно" }}</td>
            <td>{{ row.candidate?.join(", ") ?? "Недоступно" }}</td>
            <td>{{ row.current?.join(", ") ?? "Недоступно" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <button
      type="button"
      data-test="comparison-discard"
      :disabled="!store.canDiscardRejectedAttempt"
      @click="store.discardRejectedAttempt()"
    >
      Отказаться от попытки
    </button>
    <p>Попытка будет удалена. Затем можно заново изменить актуальную линию</p>
  </section>
</template>
<style scoped>
.comparison {
  padding: 12px 16px;
  max-height: 38vh;
  overflow: auto;
  background: #fff7ed;
  flex-shrink: 0;
}
.tableScroll {
  overflow: auto;
}
table {
  border-collapse: collapse;
}
th,
td {
  padding: 6px;
  border: 1px solid #cbd5e1;
}
button {
  min-height: 44px;
  margin: 4px;
  padding: 8px;
}
button:focus-visible {
  outline: 3px solid #2563eb;
}
p {
  font-size: 13px;
}
</style>
