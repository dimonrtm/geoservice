<script setup lang="ts">
import type { WorkOrderDataIssue } from "@/contracts/work_order/work-order-response-error";
defineProps<{ issues: readonly WorkOrderDataIssue[] }>();
</script>

<template>
  <ul
    v-if="issues.length"
    class="workOrderDataIssues"
    aria-label="Ошибки данных наряда"
    data-test="work-order-data-issues"
  >
    <li v-for="issue in issues" :key="issue.field">{{ issue.message }}</li>
  </ul>
</template>

<style scoped>
.workOrderDataIssues {
  margin: 8px 0;
  padding-left: 20px;
  color: #b91c1c;
  font-size: 13px;
  text-align: left;
  overflow-wrap: anywhere;
}
</style>
