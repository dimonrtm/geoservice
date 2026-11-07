<script setup lang="ts">
import { computed } from "vue";
import { useEditVersionCommandsStore } from "@/stores/editVersionCommands";
import { useEditorSessionStore } from "@/stores/editorSession";
import { comparisonRows } from "@/domain/workspaceComparison";
import { isLineStringXY } from "@/contracts/workspace-edit";
const editVersionCommands = useEditVersionCommandsStore();
const editorSession = useEditorSessionStore();
const rows = computed(() => {
  const m = editVersionCommands.activeComparison;
  if (!m) return [];
  const g =
    editorSession.activeWorkspace?.workOrder.editVersion.features.features.find(
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
    v-if="editVersionCommands.activeComparison"
    class="comparison"
    aria-labelledby="comparison-heading"
    data-test="stale-comparison"
  >
    <h3 id="comparison-heading">Сравнение несохранённой попытки</h3>
    <p>
      Данные изменились. Попытка не перенесена на актуальную линию. Предпросмотр
      не изменяет данные.
    </p>
    <p v-if="!editVersionCommands.activeComparison.source">
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
        :disabled="
          option.id === 'source' && !editVersionCommands.activeComparison.source
        "
        :aria-pressed="editVersionCommands.comparisonPreview === option.id"
        @click="editVersionCommands.comparisonPreview = option.id"
      >
        {{ option.label }}
      </button>
      <button
        type="button"
        @click="editVersionCommands.comparisonPreview = null"
      >
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
      :disabled="!editVersionCommands.canDiscardRejectedAttempt"
      @click="editVersionCommands.discardRejectedAttempt()"
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
