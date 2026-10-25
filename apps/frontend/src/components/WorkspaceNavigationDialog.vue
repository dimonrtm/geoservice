<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { useWorkOrdersStore } from "@/stores/workOrders";
import type { NavigationChoice } from "@/domain/workspaceNavigation";
import { containDialogFocus } from "@/domain/dialogFocus";
const store = useWorkOrdersStore(),
  dialog = ref<HTMLDialogElement | null>(null);
let previous: HTMLElement | null = null;
watch(
  () => store.navigation?.id,
  async (id) => {
    if (id) {
      previous = document.activeElement as HTMLElement;
      await nextTick();
      dialog.value?.showModal();
      dialog.value?.querySelector<HTMLButtonElement>("button")?.focus();
    } else {
      dialog.value?.close();
      await nextTick();
      if (previous?.isConnected) previous.focus();
    }
  },
);
function choose(choice: NavigationChoice) {
  const id = store.navigation?.id;
  if (id) void store.resolveNavigation(id, choice);
}
</script>
<template>
  <p v-if="store.navigationError" role="alert">{{ store.navigationError }}</p>
  <dialog
    v-if="store.navigation"
    ref="dialog"
    aria-labelledby="navigation-title"
    aria-describedby="navigation-description"
    @cancel.prevent="choose('stay')"
    @keydown="containDialogFocus"
  >
    <h2 id="navigation-title">
      {{
        store.navigation.phase === "dirty"
          ? "Что сделать с локальной правкой?"
          : "Продолжить выход?"
      }}
    </h2>
    <p v-if="store.navigation.phase === 'dirty'" id="navigation-description">
      Можно сохранить правку перед переходом, отказаться от неё или остаться.
    </p>
    <p v-else-if="store.navigation.phase === 'saving'">
      Сохраняем правку и загружаем актуальные данные…
    </p>
    <p v-else>
      Выход не отменяет отправленную команду. Восстановление сохранится в этом
      профиле браузера. При выходе из аккаунта материалы сравнения будут
      удалены.
    </p>
    <p
      v-if="
        store.navigation.target.kind === 'logout' &&
        Object.keys(store.staleComparisons).length
      "
    >
      При выходе из аккаунта перечисленные материалы сравнения будут удалены.
    </p>
    <ul v-if="store.navigation.target.kind === 'logout'">
      <li v-for="(material, key) in store.staleComparisons" :key="key">
        Несохранённая попытка {{ material.commandId }}
      </li>
    </ul>
    <div>
      <button
        type="button"
        data-test="navigation-stay"
        :disabled="store.navigation.phase === 'saving'"
        @click="choose('stay')"
      >
        Остаться
      </button>
      <template v-if="store.navigation.phase === 'dirty'">
        <button
          type="button"
          data-test="navigation-save"
          @click="choose('save')"
        >
          Сохранить и выйти
        </button>
        <button
          type="button"
          data-test="navigation-discard"
          @click="choose('discard')"
        >
          Не сохранять и выйти
        </button>
      </template>
      <button
        v-else-if="store.navigation.phase !== 'saving'"
        type="button"
        data-test="navigation-leave"
        @click="choose('leave')"
      >
        Выйти
      </button>
    </div>
  </dialog>
</template>
<style scoped>
dialog {
  max-width: min(480px, calc(100vw - 48px));
  max-height: calc(100dvh - 48px);
  overflow: auto;
  border: 1px solid #94a3b8;
  border-radius: 8px;
  padding: 20px;
}
dialog::backdrop {
  background: #0f172a80;
}
div {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
button {
  min-height: 44px;
  padding: 8px 14px;
}
button:focus-visible {
  outline: 3px solid #2563eb;
}
</style>
