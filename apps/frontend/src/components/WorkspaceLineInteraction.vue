<script setup lang="ts">
import { nextTick, ref, toRef, watch } from "vue";
import type { Map } from "maplibre-gl";
import type { WorkspaceResponse } from "@/contracts/work-orders";
import { useWorkspaceLineInteraction } from "@/composables/map/useWorkspaceLineInteraction";
const props = defineProps<{ map: Map; workspace: WorkspaceResponse }>();
const { message, choices, confirmation, select, confirmDiscard } =
  useWorkspaceLineInteraction(toRef(props, "map"), toRef(props, "workspace"));
const panel = ref<HTMLElement | null>(null);
let previousFocus: HTMLElement | null = null;
watch(
  () =>
    confirmation.value
      ? "confirmation"
      : choices.value.length
        ? "choices"
        : "closed",
  async (mode, previousMode) => {
    if (mode !== "closed") {
      if (previousMode === "closed")
        previousFocus = document.activeElement as HTMLElement | null;
      await nextTick();
      panel.value?.querySelector<HTMLButtonElement>("button")?.focus();
    } else {
      if (previousFocus?.isConnected) previousFocus.focus();
      else props.map.getCanvas().focus();
    }
  },
);
function close() {
  confirmation.value = null;
  choices.value = [];
}
function keydown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    event.preventDefault();
    event.stopPropagation();
    close();
  }
  if (event.key !== "Tab") return;
  const buttons = panel.value?.querySelectorAll<HTMLButtonElement>("button");
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
</script>

<template>
  <div
    class="workspaceInteraction"
    @click.stop
    @pointerdown.stop
    @keydown="keydown"
  >
    <p
      v-if="message"
      role="status"
      aria-live="polite"
      class="interactionMessage"
    >
      {{ message }}
    </p>
    <section
      v-if="confirmation"
      ref="panel"
      role="dialog"
      aria-modal="true"
      aria-label="Отменить несохранённую правку?"
      class="interactionPanel"
    >
      <h3>Отменить несохранённую правку?</h3>
      <p>Линия вернётся к последнему сохранённому состоянию.</p>
      <div class="interactionActions">
        <button type="button" data-test="keep-draft" @click="close">
          Продолжить правку
        </button>
        <button type="button" data-test="discard-draft" @click="confirmDiscard">
          Отменить правку
        </button>
      </div>
    </section>
    <section
      v-else-if="choices.length"
      ref="panel"
      role="dialog"
      aria-modal="false"
      aria-label="Выберите линию"
      class="interactionPanel"
    >
      <h3>Выберите линию</h3>
      <ul>
        <li v-for="choice in choices" :key="choice.id">
          <button
            type="button"
            data-test="line-option"
            @click="select(choice.id)"
          >
            {{ choice.label }}
          </button>
        </li>
      </ul>
      <button type="button" @click="close">Закрыть</button>
    </section>
  </div>
</template>

<style scoped>
.workspaceInteraction {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 3;
  max-width: min(380px, calc(100% - 24px));
  max-height: calc(100% - 24px);
  overflow: auto;
  pointer-events: none;
}
.interactionMessage,
.interactionPanel {
  pointer-events: auto;
  background: #fff;
  color: #1e293b;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 12px;
  margin: 0 0 8px;
  box-shadow: 0 2px 10px #0002;
}
h3 {
  margin: 0 0 8px;
  font-size: 16px;
}
p {
  font-size: 14px;
}
ul {
  list-style: none;
  margin: 0 0 10px;
  padding: 0;
  display: grid;
  gap: 6px;
}
button {
  padding: 8px 10px;
  background: #f8fafc;
  color: #0f172a;
  border: 1px solid #94a3b8;
  border-radius: 5px;
  cursor: pointer;
  text-align: left;
  overflow-wrap: anywhere;
}
button:focus-visible {
  outline: 3px solid #2563eb;
  outline-offset: 2px;
}
.interactionActions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
<style>
.workspaceVertexHandle {
  width: 18px;
  height: 18px;
  border: 3px solid #fff;
  border-radius: 50%;
  background: #ea580c;
  box-shadow: 0 0 0 2px #9a3412;
  cursor: grab;
}
.workspaceVertexHandle:active {
  cursor: grabbing;
}
</style>
