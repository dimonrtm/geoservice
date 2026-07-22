# Icon controls активного operational flow — Implementation Plan

> **Для agentic workers:** REQUIRED SUB-SKILL: используйте `superpowers:subagent-driven-development` (рекомендуется) или `superpowers:executing-plans`, чтобы выполнять этот план task-by-task. Для отслеживания используются checkbox-шаги (`- [ ]`).

**Goal:** Заменить ключевые текстовые controls активного operational flow на согласованные icon+text/icon-only кнопки с доступными tooltip, стабильными loading states и точечной mobile-адаптацией.

**Architecture:** Добавить два domain-agnostic Vue-примитива: `UiButton` для icon+text и `UiIconButton` для icon-only с tooltip. Call sites продолжают владеть действиями и domain state, а примитивы отвечают только за native button semantics, Lucide icon, focus/disabled/loading styles и tooltip behavior.

**Tech Stack:** Vue 3.5, TypeScript 5.9, Vite 7, Vitest 3, Vue Test Utils 2, Pinia 3, `@lucide/vue` v1, CSS.

## Global Constraints

- Канонический дизайн: `docs/superpowers/specs/2026-07-22-operational-icon-controls-design.md`.
- Использовать официальный пакет `@lucide/vue` v1; пакет `lucide-vue-next` переименован в v1, API icon-компонентов сохранён.
- В scope только `App.vue`, `EditorWorkOrdersView.vue`, `WorkspaceDetailsPanel.vue`, `ActionableError.vue`, новые UI-примитивы и соответствующие tests.
- Не менять backend, API contracts, Pinia stores, `LoginScreen.vue` submit, MapLibre controls и legacy toolbar `MapView.vue`.
- Desktop breakpoint равен `760 px`; desktop control height — `36 px`, narrow minimum target — `44 x 44 px`.
- Icon size — `18 px`, `stroke-width="2"`, icon всегда `aria-hidden="true"`.
- Tooltip используется только у icon-only controls: hover delay `500 ms`, immediate keyboard focus, close по `Escape`, `blur` и общему `mouseleave`, hoverable/persistent content.
- `UiButton` и `UiIconButton` по умолчанию рендерят `type="button"`; explicit native `type` может переопределить default.
- Loading устанавливает `disabled` и `aria-busy="true"`; `prefers-reduced-motion: reduce` отключает вращение loader.
- Human-readable plan/spec content остаётся на русском; paths, commands, types, identifiers и code не переводятся.
- Не выполнять `git add`, `git commit` или `git push`. После каждой задачи оставлять changes unstaged и показывать `git status --short` пользователю/reviewer.
- Baseline на 2026-07-22: `App.test.ts`, `EditorWorkOrdersView.test.ts`, `WorkspaceDetailsPanel.test.ts`, `ActionableError.test.ts` — 4 files, 34 tests, все проходят.

## File Structure

- Create `apps/frontend/src/components/ui/ui-controls.css` — общие visual, loading, responsive и tooltip styles двух примитивов.
- Create `apps/frontend/src/components/ui/UiButton.vue` — native icon+text button с stable idle/loading layers.
- Create `apps/frontend/src/components/ui/UiButton.test.ts` — contract tests icon+text примитива.
- Create `apps/frontend/src/components/ui/UiIconButton.vue` — native icon-only button и WAI-style tooltip state machine.
- Create `apps/frontend/src/components/ui/UiIconButton.test.ts` — fake-timer, keyboard и ARIA tests tooltip примитива.
- Modify `apps/frontend/package.json` — добавить `@lucide/vue` v1.
- Modify `apps/frontend/package-lock.json` — зафиксировать resolved Lucide dependency.
- Modify `apps/frontend/src/App.vue` — desktop/mobile logout controls и session-error logout.
- Modify `apps/frontend/src/App.test.ts` — responsive/session logout regressions.
- Modify `apps/frontend/src/components/EditorWorkOrdersView.vue` — icon-only refresh, связанный с `workOrders.isLoading`.
- Modify `apps/frontend/src/components/EditorWorkOrdersView.test.ts` — refresh action/loading/ARIA regressions.
- Modify `apps/frontend/src/components/WorkspaceDetailsPanel.vue` — primary `Начать`/`Продолжить` через `UiButton`.
- Modify `apps/frontend/src/components/WorkspaceDetailsPanel.test.ts` — icon, active label и loading semantics.
- Modify `apps/frontend/src/components/ActionableError.vue` — exhaustive `ErrorActionId` icon mapping и clipboard loading.
- Modify `apps/frontend/src/components/ActionableError.test.ts` — mapping и pending clipboard tests.

---

### Task 1: `UiButton` и общая control-база

**Files:**

- Modify: `apps/frontend/package.json`
- Modify: `apps/frontend/package-lock.json`
- Create: `apps/frontend/src/components/ui/ui-controls.css`
- Create: `apps/frontend/src/components/ui/UiButton.vue`
- Create: `apps/frontend/src/components/ui/UiButton.test.ts`

**Interfaces:**

- Consumes: `LucideIcon` и `LoaderCircle` из `@lucide/vue`.
- Produces: `UiButton` props `icon: LucideIcon`, `variant?: "primary" | "secondary" | "error"`, `loading?: boolean`, `loadingLabel?: string`, `disabled?: boolean`; default slot содержит видимую idle-подпись.
- Produces: общие classes `.uiControl`, `.uiControlIcon`, `.uiControlStableContent`, `.uiControlContent`, `.uiControlLoader`, которые использует Task 2.

- [ ] **Step 1: Добавить текущий официальный Lucide package**

Run из `apps/frontend`:

```powershell
npm install '@lucide/vue@^1.0.0'
```

Expected: exit code `0`; `package.json` содержит dependency `@lucide/vue` с major version `1`, `package-lock.json` содержит resolved package.

- [ ] **Step 2: Написать failing contract tests `UiButton`**

Create `apps/frontend/src/components/ui/UiButton.test.ts`:

```ts
import { mount } from "@vue/test-utils";
import { LoaderCircle, Play } from "@lucide/vue";
import { describe, expect, it, vi } from "vitest";

import UiButton from "@/components/ui/UiButton.vue";

describe("UiButton", () => {
  it("renders icon and text through a native button", () => {
    const wrapper = mount(UiButton, {
      props: { icon: Play, variant: "primary" },
      attrs: { type: "submit", "data-test": "primary-action" },
      slots: { default: "Начать" },
    });

    const button = wrapper.get('[data-test="primary-action"]');
    expect(button.element.tagName).toBe("BUTTON");
    expect(button.attributes("type")).toBe("submit");
    expect(button.classes()).toContain("uiControlPrimary");
    expect(button.get('[data-ui-control-state="idle"]').text()).toBe(
      "Начать",
    );
    expect(
      button.find('[data-ui-control-state="loading"]').exists(),
    ).toBe(false);
    expect(
      button.findAll("svg").every((icon) => icon.attributes("aria-hidden") === "true"),
    ).toBe(true);
  });

  it("keeps idle and loading layers stable while blocking repeated clicks", async () => {
    const onClick = vi.fn();
    const wrapper = mount(UiButton, {
      props: {
        icon: Play,
        loading: true,
        loadingLabel: "Открываем…",
      },
      attrs: { onClick },
      slots: { default: "Продолжить" },
    });

    const button = wrapper.get("button");
    expect(button.attributes("type")).toBe("button");
    expect(button.attributes("disabled")).toBeDefined();
    expect(button.attributes("aria-busy")).toBe("true");
    expect(
      button.get('[data-ui-control-state="idle"]').classes(),
    ).toContain("isHidden");
    expect(
      button.get('[data-ui-control-state="loading"]').classes(),
    ).not.toContain("isHidden");
    expect(button.get('[data-ui-control-state="loading"]').text()).toBe(
      "Открываем…",
    );
    expect(wrapper.findComponent(LoaderCircle).exists()).toBe(true);

    await button.trigger("click");
    expect(onClick).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 3: Запустить test и подтвердить RED**

Run:

```powershell
npm test -- src/components/ui/UiButton.test.ts
```

Expected: FAIL с module resolution error для отсутствующего `@/components/ui/UiButton.vue`.

- [ ] **Step 4: Создать общие control styles**

Create `apps/frontend/src/components/ui/ui-controls.css`:

```css
.uiControl {
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  height: 36px;
  gap: 8px;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0 12px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background-color 120ms ease,
    border-color 120ms ease,
    color 120ms ease;
}

.uiControlPrimary {
  border-color: #166534;
  background: #166534;
  color: #fff;
}

.uiControlPrimary:hover:not(:disabled) {
  border-color: #14532d;
  background: #14532d;
}

.uiControlSecondary {
  border-color: rgba(15, 23, 42, 0.14);
  background: #fff;
  color: #0f172a;
}

.uiControlSecondary:hover:not(:disabled) {
  border-color: rgba(22, 101, 52, 0.55);
  color: #14532d;
}

.uiControlError {
  border-color: rgba(153, 27, 27, 0.3);
  background: #fff;
  color: #7f1d1d;
}

.uiControlError:hover:not(:disabled) {
  border-color: #991b1b;
  background: #fef2f2;
}

.uiControl:focus-visible {
  outline: 3px solid rgba(37, 99, 235, 0.55);
  outline-offset: 2px;
}

.uiControl:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.uiControl[aria-busy="true"] {
  cursor: wait;
}

.uiControlIcon {
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
}

.uiControlStableContent {
  display: grid;
  place-items: center;
}

.uiControlContent {
  grid-area: 1 / 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
}

.uiControlContent.isHidden {
  visibility: hidden;
}

.uiControlLoader {
  animation: ui-control-spin 900ms linear infinite;
}

@keyframes ui-control-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 760px) {
  .uiControl {
    min-height: 44px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .uiControl,
  .uiControlLoader {
    transition: none;
    animation: none;
  }
}
```

- [ ] **Step 5: Реализовать минимальный `UiButton`**

Create `apps/frontend/src/components/ui/UiButton.vue`:

```vue
<script setup lang="ts">
import { LoaderCircle, type LucideIcon } from "@lucide/vue";
import { computed, useAttrs } from "vue";

import "@/components/ui/ui-controls.css";

defineOptions({ inheritAttrs: false });

type UiControlVariant = "primary" | "secondary" | "error";
type NativeButtonType = "button" | "submit" | "reset";

const props = withDefaults(
  defineProps<{
    icon: LucideIcon;
    variant?: UiControlVariant;
    loading?: boolean;
    loadingLabel?: string;
    disabled?: boolean;
  }>(),
  {
    variant: "secondary",
    loading: false,
    disabled: false,
  },
);

const attrs = useAttrs();
const nativeType = computed<NativeButtonType>(() => {
  const candidate = attrs.type;
  return candidate === "submit" || candidate === "reset" || candidate === "button"
    ? candidate
    : "button";
});
const isDisabled = computed(() => props.disabled || props.loading);
const resolvedLoadingLabel = computed(
  () => props.loadingLabel ?? "Выполняется…",
);
</script>

<template>
  <button
    v-bind="$attrs"
    class="uiControl"
    :class="{
      uiControlPrimary: props.variant === 'primary',
      uiControlSecondary: props.variant === 'secondary',
      uiControlError: props.variant === 'error',
    }"
    :type="nativeType"
    :disabled="isDisabled"
    :aria-busy="props.loading ? 'true' : undefined"
  >
    <span class="uiControlStableContent">
      <span
        class="uiControlContent"
        :class="{ isHidden: props.loading }"
        data-ui-control-state="idle"
        :aria-hidden="props.loading ? 'true' : undefined"
      >
        <component
          :is="props.icon"
          class="uiControlIcon"
          :size="18"
          :stroke-width="2"
          aria-hidden="true"
          focusable="false"
        />
        <span><slot /></span>
      </span>

      <span
        v-if="props.loading || props.loadingLabel !== undefined"
        class="uiControlContent"
        :class="{ isHidden: !props.loading }"
        data-ui-control-state="loading"
        :aria-hidden="props.loading ? undefined : 'true'"
      >
        <LoaderCircle
          class="uiControlIcon uiControlLoader"
          :size="18"
          :stroke-width="2"
          aria-hidden="true"
          focusable="false"
        />
        <span>{{ resolvedLoadingLabel }}</span>
      </span>
    </span>
  </button>
</template>
```

- [ ] **Step 6: Запустить focused test и typecheck**

Run:

```powershell
npm test -- src/components/ui/UiButton.test.ts
npm run typecheck
```

Expected: `UiButton.test.ts` PASS; `vue-tsc --noEmit` exit code `0`.

- [ ] **Step 7: Оставить unstaged review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; новые/изменённые Task 1 files показаны unstaged. Не выполнять `git add` или `git commit`.

---

### Task 2: `UiIconButton` и доступный tooltip

**Files:**

- Modify: `apps/frontend/src/components/ui/ui-controls.css`
- Create: `apps/frontend/src/components/ui/UiIconButton.vue`
- Create: `apps/frontend/src/components/ui/UiIconButton.test.ts`

**Interfaces:**

- Consumes: base classes и `UiControlVariant`-значения, зафиксированные Task 1.
- Produces: `UiIconButton` props `icon: LucideIcon`, `label: string`, `tooltip: string`, `tooltipAlign?: "center" | "end"`, `variant?: "primary" | "secondary" | "error"`, `loading?: boolean`, `loadingLabel?: string`, `disabled?: boolean`.
- Produces: stable tooltip DOM node с `role="tooltip"`, уникальным id и `data-state="open" | "closed"`.

- [ ] **Step 1: Написать failing tooltip tests**

Create `apps/frontend/src/components/ui/UiIconButton.test.ts`:

```ts
import { mount } from "@vue/test-utils";
import { LogOut, RefreshCw } from "@lucide/vue";
import { afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import UiIconButton from "@/components/ui/UiIconButton.vue";

afterEach(() => {
  vi.useRealTimers();
});

describe("UiIconButton", () => {
  it("connects a native icon-only button to a persistent tooltip node", () => {
    const wrapper = mount(UiIconButton, {
      props: {
        icon: LogOut,
        label: "Выйти",
        tooltip: "Выйти из GeoService",
        tooltipAlign: "end",
      },
      attrs: { "data-test": "logout-icon" },
    });

    const button = wrapper.get('[data-test="logout-icon"]');
    const tooltip = wrapper.get('[role="tooltip"]');
    expect(button.element.tagName).toBe("BUTTON");
    expect(button.attributes("type")).toBe("button");
    expect(button.attributes("aria-label")).toBe("Выйти");
    expect(button.attributes("aria-describedby")).toBe(
      tooltip.attributes("id"),
    );
    expect(tooltip.text()).toBe("Выйти из GeoService");
    expect(tooltip.attributes("data-state")).toBe("closed");
    expect(tooltip.classes()).toContain("uiControlTooltipEnd");
    expect(button.get("svg").attributes("aria-hidden")).toBe("true");
  });

  it("opens after hover delay and stays open until the shared region is left", async () => {
    vi.useFakeTimers();
    const wrapper = mount(UiIconButton, {
      props: {
        icon: RefreshCw,
        label: "Обновить",
        tooltip: "Обновить список назначенных нарядов",
      },
    });

    const root = wrapper.get(".uiIconButtonRoot");
    const button = wrapper.get("button");
    const tooltip = wrapper.get('[role="tooltip"]');

    await root.trigger("mouseenter");
    vi.advanceTimersByTime(499);
    await nextTick();
    expect(tooltip.attributes("data-state")).toBe("closed");

    vi.advanceTimersByTime(1);
    await nextTick();
    expect(tooltip.attributes("data-state")).toBe("open");

    await button.trigger("mouseout", { relatedTarget: tooltip.element });
    await tooltip.trigger("mouseenter");
    expect(tooltip.attributes("data-state")).toBe("open");

    await root.trigger("mouseleave");
    expect(tooltip.attributes("data-state")).toBe("closed");
  });

  it("opens immediately on focus and closes on Escape", async () => {
    vi.useFakeTimers();
    const wrapper = mount(UiIconButton, {
      props: {
        icon: LogOut,
        label: "Выйти",
        tooltip: "Выйти из GeoService",
      },
    });

    const button = wrapper.get("button");
    const tooltip = wrapper.get('[role="tooltip"]');
    await button.trigger("focus");
    expect(tooltip.attributes("data-state")).toBe("open");

    await button.trigger("keydown", { key: "Escape" });
    expect(tooltip.attributes("data-state")).toBe("closed");

    await button.trigger("blur");
    expect(tooltip.attributes("data-state")).toBe("closed");
  });

  it("uses loading semantics and prevents repeated action", async () => {
    const onClick = vi.fn();
    const wrapper = mount(UiIconButton, {
      props: {
        icon: RefreshCw,
        label: "Обновить",
        tooltip: "Обновить список назначенных нарядов",
        loading: true,
        loadingLabel: "Обновление списка нарядов",
      },
      attrs: { onClick },
    });

    const button = wrapper.get("button");
    expect(button.attributes("aria-label")).toBe(
      "Обновление списка нарядов",
    );
    expect(button.attributes("aria-busy")).toBe("true");
    expect(button.attributes("disabled")).toBeDefined();
    expect(button.get("svg").classes()).toContain("uiControlLoader");

    await button.trigger("click");
    expect(onClick).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Запустить test и подтвердить RED**

Run:

```powershell
npm test -- src/components/ui/UiIconButton.test.ts
```

Expected: FAIL с module resolution error для отсутствующего `UiIconButton.vue`.

- [ ] **Step 3: Заменить common CSS итоговой версией с tooltip rules**

Replace the complete content of `apps/frontend/src/components/ui/ui-controls.css` with:

```css
.uiControl {
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  height: 36px;
  gap: 8px;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0 12px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background-color 120ms ease,
    border-color 120ms ease,
    color 120ms ease;
}

.uiControlPrimary {
  border-color: #166534;
  background: #166534;
  color: #fff;
}

.uiControlPrimary:hover:not(:disabled) {
  border-color: #14532d;
  background: #14532d;
}

.uiControlSecondary {
  border-color: rgba(15, 23, 42, 0.14);
  background: #fff;
  color: #0f172a;
}

.uiControlSecondary:hover:not(:disabled) {
  border-color: rgba(22, 101, 52, 0.55);
  color: #14532d;
}

.uiControlError {
  border-color: rgba(153, 27, 27, 0.3);
  background: #fff;
  color: #7f1d1d;
}

.uiControlError:hover:not(:disabled) {
  border-color: #991b1b;
  background: #fef2f2;
}

.uiControl:focus-visible {
  outline: 3px solid rgba(37, 99, 235, 0.55);
  outline-offset: 2px;
}

.uiControl:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.uiControl[aria-busy="true"] {
  cursor: wait;
}

.uiControlIcon {
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
}

.uiControlIconOnly {
  width: 36px;
  padding: 0;
}

.uiControlStableContent {
  display: grid;
  place-items: center;
}

.uiControlContent {
  grid-area: 1 / 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
}

.uiControlContent.isHidden {
  visibility: hidden;
}

.uiControlLoader {
  animation: ui-control-spin 900ms linear infinite;
}

.uiIconButtonRoot {
  position: relative;
  display: inline-flex;
  flex: 0 0 auto;
  overflow: visible;
}

.uiControlTooltip {
  position: absolute;
  top: calc(100% + 8px);
  z-index: 30;
  width: max-content;
  max-width: min(240px, calc(100vw - 16px));
  border-radius: 6px;
  padding: 6px 8px;
  background: #0f172a;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.3;
  white-space: normal;
  overflow-wrap: anywhere;
  opacity: 0;
  visibility: hidden;
  pointer-events: auto;
  transition: opacity 120ms ease;
}

.uiControlTooltip::before {
  content: "";
  position: absolute;
  top: -8px;
  right: 0;
  left: 0;
  height: 8px;
}

.uiControlTooltip[data-state="open"] {
  opacity: 1;
  visibility: visible;
}

.uiControlTooltipCenter {
  left: 50%;
  transform: translateX(-50%);
}

.uiControlTooltipEnd {
  right: 0;
}

@keyframes ui-control-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 760px) {
  .uiControl {
    min-height: 44px;
  }

  .uiControlIconOnly {
    width: 44px;
    height: 44px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .uiControl,
  .uiControlTooltip {
    transition: none;
  }

  .uiControlLoader {
    animation: none;
  }
}
```

- [ ] **Step 4: Реализовать tooltip state machine**

Create `apps/frontend/src/components/ui/UiIconButton.vue`:

```vue
<script setup lang="ts">
import { LoaderCircle, type LucideIcon } from "@lucide/vue";
import { computed, onBeforeUnmount, ref, useAttrs, useId } from "vue";

import "@/components/ui/ui-controls.css";

defineOptions({ inheritAttrs: false });

type UiControlVariant = "primary" | "secondary" | "error";
type TooltipAlign = "center" | "end";
type NativeButtonType = "button" | "submit" | "reset";

const props = withDefaults(
  defineProps<{
    icon: LucideIcon;
    label: string;
    tooltip: string;
    tooltipAlign?: TooltipAlign;
    variant?: UiControlVariant;
    loading?: boolean;
    loadingLabel?: string;
    disabled?: boolean;
  }>(),
  {
    tooltipAlign: "center",
    variant: "secondary",
    loading: false,
    loadingLabel: "Выполняется",
    disabled: false,
  },
);

const attrs = useAttrs();
const tooltipId = `ui-tooltip-${useId()}`;
const isTooltipOpen = ref(false);
const hasKeyboardFocus = ref(false);
let hoverTimer: ReturnType<typeof window.setTimeout> | null = null;

const nativeType = computed<NativeButtonType>(() => {
  const candidate = attrs.type;
  return candidate === "submit" || candidate === "reset" || candidate === "button"
    ? candidate
    : "button";
});
const isDisabled = computed(() => props.disabled || props.loading);
const accessibleLabel = computed(() =>
  props.loading ? props.loadingLabel : props.label,
);
const renderedIcon = computed(() => (props.loading ? LoaderCircle : props.icon));

function clearHoverTimer(): void {
  if (hoverTimer !== null) {
    window.clearTimeout(hoverTimer);
    hoverTimer = null;
  }
}

function openTooltipImmediately(): void {
  clearHoverTimer();
  isTooltipOpen.value = true;
}

function scheduleTooltip(): void {
  if (isTooltipOpen.value) {
    return;
  }
  clearHoverTimer();
  hoverTimer = window.setTimeout(() => {
    hoverTimer = null;
    isTooltipOpen.value = true;
  }, 500);
}

function handlePointerLeave(): void {
  clearHoverTimer();
  if (!hasKeyboardFocus.value) {
    isTooltipOpen.value = false;
  }
}

function handleFocus(): void {
  hasKeyboardFocus.value = true;
  openTooltipImmediately();
}

function handleBlur(): void {
  hasKeyboardFocus.value = false;
  clearHoverTimer();
  isTooltipOpen.value = false;
}

function dismissTooltip(): void {
  clearHoverTimer();
  isTooltipOpen.value = false;
}

onBeforeUnmount(clearHoverTimer);
</script>

<template>
  <span
    class="uiIconButtonRoot"
    @mouseenter="scheduleTooltip"
    @mouseleave="handlePointerLeave"
  >
    <button
      v-bind="$attrs"
      class="uiControl uiControlIconOnly"
      :class="{
        uiControlPrimary: props.variant === 'primary',
        uiControlSecondary: props.variant === 'secondary',
        uiControlError: props.variant === 'error',
      }"
      :type="nativeType"
      :disabled="isDisabled"
      :aria-label="accessibleLabel"
      :aria-describedby="tooltipId"
      :aria-busy="props.loading ? 'true' : undefined"
      @focus="handleFocus"
      @blur="handleBlur"
      @keydown.esc="dismissTooltip"
    >
      <component
        :is="renderedIcon"
        class="uiControlIcon"
        :class="{ uiControlLoader: props.loading }"
        :size="18"
        :stroke-width="2"
        aria-hidden="true"
        focusable="false"
      />
    </button>

    <span
      :id="tooltipId"
      class="uiControlTooltip"
      :class="{
        uiControlTooltipCenter: props.tooltipAlign === 'center',
        uiControlTooltipEnd: props.tooltipAlign === 'end',
      }"
      role="tooltip"
      :data-state="isTooltipOpen ? 'open' : 'closed'"
    >
      {{ props.tooltip }}
    </span>
  </span>
</template>
```

- [ ] **Step 5: Запустить tooltip tests и typecheck**

Run:

```powershell
npm test -- src/components/ui/UiButton.test.ts src/components/ui/UiIconButton.test.ts
npm run typecheck
```

Expected: both files PASS; typecheck exit code `0`.

- [ ] **Step 6: Оставить unstaged review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; Task 1–2 files остаются unstaged. Не выполнять Git mutation.

---

### Task 3: Responsive logout controls в `App`

**Files:**

- Modify: `apps/frontend/src/App.test.ts`
- Modify: `apps/frontend/src/App.vue`

**Interfaces:**

- Consumes: `UiButton`, `UiIconButton`, `LogOut`, существующий `auth.logout()`.
- Produces: `data-test="session-logout"`, `data-test="logout-desktop"`, `data-test="logout-mobile"`; `.logoutDesktop` и `.logoutMobile` переключаются на `760 px`.

- [ ] **Step 1: Добавить failing logout regressions**

Append inside `describe("App", ...)` in `apps/frontend/src/App.test.ts`:

```ts
  it("renders desktop and narrow logout controls through one action", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const auth = useAuthStore();
    auth.token = "token-1";
    auth.user = {
      id: "editor-1",
      email: "editor@example.local",
      role: "editor",
    };
    auth.isReady = true;
    auth.logout = vi.fn();

    const { default: App } = await import("@/App.vue");
    const wrapper = mount(App);
    const desktop = wrapper.get('[data-test="logout-desktop"]');
    const mobile = wrapper.get('[data-test="logout-mobile"]');

    expect(desktop.text()).toContain("Выйти");
    expect(desktop.element.closest(".logoutDesktop")).not.toBeNull();
    expect(mobile.attributes("aria-label")).toBe("Выйти");
    expect(mobile.attributes("aria-describedby")).toBeDefined();
    expect(mobile.element.closest(".logoutMobile")).not.toBeNull();

    await desktop.trigger("click");
    await mobile.trigger("click");
    expect(auth.logout).toHaveBeenCalledTimes(2);
  });

  it("keeps session-error logout as icon plus text", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const auth = useAuthStore();
    auth.isReady = true;
    auth.sessionError = {
      summary: "Не удалось восстановить сессию.",
      guidance: "Проверьте соединение и повторите запрос.",
      action: { id: "retry", label: "Повторить" },
      diagnostics: { code: "INTERNAL_ERROR", correlationId: "session-id" },
    };
    auth.logout = vi.fn();

    const { default: App } = await import("@/App.vue");
    const wrapper = mount(App);
    const logout = wrapper.get('[data-test="session-logout"]');
    expect(logout.text()).toContain("Выйти");

    await logout.trigger("click");
    expect(auth.logout).toHaveBeenCalledTimes(1);
  });
```

- [ ] **Step 2: Запустить App test и подтвердить RED**

Run:

```powershell
npm test -- src/App.test.ts
```

Expected: FAIL, потому что новые `data-test` controls ещё отсутствуют.

- [ ] **Step 3: Подключить UI-примитивы и `LogOut`**

Add to `apps/frontend/src/App.vue` script imports:

```ts
import { LogOut } from "@lucide/vue";

import UiButton from "@/components/ui/UiButton.vue";
import UiIconButton from "@/components/ui/UiIconButton.vue";
```

Replace the session-error `<button class="btn btnSecondary">` block with:

```vue
          <UiButton
            :icon="LogOut"
            variant="secondary"
            data-test="session-logout"
            @click="auth.logout"
          >
            Выйти
          </UiButton>
```

Replace the authenticated top-bar logout `<button>` with:

```vue
        <div class="logoutControls">
          <div class="logoutDesktop">
            <UiButton
              :icon="LogOut"
              variant="secondary"
              data-test="logout-desktop"
              @click="auth.logout"
            >
              Выйти
            </UiButton>
          </div>
          <div class="logoutMobile">
            <UiIconButton
              :icon="LogOut"
              label="Выйти"
              tooltip="Выйти из GeoService"
              tooltip-align="end"
              variant="secondary"
              data-test="logout-mobile"
              @click="auth.logout"
            />
          </div>
        </div>
```

- [ ] **Step 4: Заменить локальные `.btn` styles на responsive logout rules**

Remove `.btn` and `.btnSecondary` blocks from `App.vue` and add:

```css
.logoutControls {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
}

.logoutDesktop {
  display: block;
}

.logoutMobile {
  display: none;
}

@media (max-width: 760px) {
  .topBar {
    gap: 12px;
    padding: 10px 12px;
  }

  .logoutDesktop {
    display: none;
  }

  .logoutMobile {
    display: block;
  }
}
```

- [ ] **Step 5: Запустить App и primitive tests**

Run:

```powershell
npm test -- src/App.test.ts src/components/ui/UiButton.test.ts src/components/ui/UiIconButton.test.ts
```

Expected: 3 test files PASS; existing auth/session flows остаются зелёными.

- [ ] **Step 6: Оставить unstaged review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: App changes и UI primitive changes unstaged; no whitespace errors.

---

### Task 4: Icon-only refresh списка нарядов

**Files:**

- Modify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`
- Modify: `apps/frontend/src/components/EditorWorkOrdersView.vue`

**Interfaces:**

- Consumes: `UiIconButton`, `RefreshCw`, `workOrders.loadAssigned()`, `workOrders.isLoading`.
- Produces: `data-test="refresh-work-orders"`, idle `aria-label="Обновить"`, loading `aria-label="Обновление списка нарядов"`.

- [ ] **Step 1: Добавить failing refresh tests**

Add after the existing `announces list loading state politely` test in `EditorWorkOrdersView.test.ts`:

```ts
  it("refreshes assigned work orders through an accessible icon control", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [];
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    await flushPromises();
    loadAssignedMock.mockClear();

    const refresh = wrapper.get('[data-test="refresh-work-orders"]');
    expect(refresh.attributes("aria-label")).toBe("Обновить");
    expect(refresh.attributes("aria-describedby")).toBeDefined();

    await refresh.trigger("click");
    expect(loadAssignedMock).toHaveBeenCalledTimes(1);
  });

  it("exposes refresh loading state and blocks a second request", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.isLoading = true;
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } =
      await import("@/components/EditorWorkOrdersView.vue");
    const wrapper = mount(EditorWorkOrdersView);
    const refresh = wrapper.get('[data-test="refresh-work-orders"]');

    expect(refresh.attributes("disabled")).toBeDefined();
    expect(refresh.attributes("aria-busy")).toBe("true");
    expect(refresh.attributes("aria-label")).toBe(
      "Обновление списка нарядов",
    );
    expect(refresh.get("svg").classes()).toContain("uiControlLoader");

    await refresh.trigger("click");
    expect(loadAssignedMock).toHaveBeenCalledTimes(1);
  });
```

- [ ] **Step 2: Запустить focused test и подтвердить RED**

Run:

```powershell
npm test -- src/components/EditorWorkOrdersView.test.ts
```

Expected: FAIL, потому что `refresh-work-orders` ещё отсутствует.

- [ ] **Step 3: Заменить refresh markup**

Add imports to `EditorWorkOrdersView.vue`:

```ts
import { RefreshCw } from "@lucide/vue";

import UiIconButton from "@/components/ui/UiIconButton.vue";
```

Replace the current `.refreshButton` native button with:

```vue
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
```

Remove the obsolete `.refreshButton` CSS block from `EditorWorkOrdersView.vue`; shared `.uiControl*` styles own the control.

- [ ] **Step 4: Запустить Editor и primitive tests**

Run:

```powershell
npm test -- src/components/EditorWorkOrdersView.test.ts src/components/ui/UiIconButton.test.ts
```

Expected: both files PASS; original list loading, empty, selection, retry and workspace tests remain green.

- [ ] **Step 5: Оставить unstaged review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; Task 4 remains unstaged.

---

### Task 5: Primary `Начать`/`Продолжить` control

**Files:**

- Modify: `apps/frontend/src/components/WorkspaceDetailsPanel.test.ts`
- Modify: `apps/frontend/src/components/WorkspaceDetailsPanel.vue`

**Interfaces:**

- Consumes: `UiButton`, `Play`, props `isOpening` и `isOpenActionDisabled`.
- Produces: `workspace-open-action` остаётся native button; idle layer показывает `Начать` или `Продолжить`, loading layer — `Открываем…`.

- [ ] **Step 1: Обновить tests под explicit idle/loading layers**

Add imports to `WorkspaceDetailsPanel.test.ts`:

```ts
import { Play } from "@lucide/vue";

import UiButton from "@/components/ui/UiButton.vue";
```

Add after `mountPanel`:

```ts
function activeControlText(wrapper: VueWrapper, selector: string): string {
  const button = wrapper.get(selector);
  const loading = button.get('[data-ui-control-state="loading"]');
  return loading.classes().includes("isHidden")
    ? button.get('[data-ui-control-state="idle"]').text()
    : loading.text();
}
```

In `renders assigned preview and emits open`, replace the current exact button text assertion with:

```ts
    expect(
      activeControlText(wrapper, '[data-test="workspace-open-action"]'),
    ).toBe("Начать");
    expect(wrapper.getComponent(UiButton).props("icon")).toBe(Play);
```

In `localizes in-progress preview and exposes loading semantics`, replace the exact text assertion and add button-level busy semantics:

```ts
    expect(
      activeControlText(wrapper, '[data-test="workspace-open-action"]'),
    ).toBe("Открываем…");
    expect(
      wrapper.get('[data-test="workspace-open-action"]').attributes("aria-busy"),
    ).toBe("true");
```

In `shows continue for an in-progress work order in the normal state`, use:

```ts
    expect(
      activeControlText(wrapper, '[data-test="workspace-open-action"]'),
    ).toBe("Продолжить");
```

In `keeps the normal label while another work order is opening`, use:

```ts
    expect(
      activeControlText(wrapper, '[data-test="workspace-open-action"]'),
    ).toBe("Начать");
    expect(
      wrapper.get('[data-test="workspace-open-action"]').attributes("aria-busy"),
    ).toBeUndefined();
```

- [ ] **Step 2: Запустить test и подтвердить RED**

Run:

```powershell
npm test -- src/components/WorkspaceDetailsPanel.test.ts
```

Expected: FAIL, потому что native button не содержит `data-ui-control-state` и не использует `UiButton`/`Play`.

- [ ] **Step 3: Перевести open action на `UiButton`**

Add imports to `WorkspaceDetailsPanel.vue`:

```ts
import { Play } from "@lucide/vue";

import UiButton from "@/components/ui/UiButton.vue";
```

Replace the current loading-aware `actionText` computed with idle-only text:

```ts
const actionText = computed(() =>
  props.workOrder.status === "in_progress" ? "Продолжить" : "Начать",
);
```

Replace the native `.openAction` button with:

```vue
      <UiButton
        v-else
        :icon="Play"
        variant="primary"
        :loading="props.isOpening"
        loading-label="Открываем…"
        :disabled="props.isOpenActionDisabled"
        data-test="workspace-open-action"
        @click="emit('open')"
      >
        {{ actionText }}
      </UiButton>
```

Remove `.openAction` and `.openAction:disabled` CSS blocks. Stable content width, primary color, cursor and loading state now belong to `UiButton`.

- [ ] **Step 4: Синхронизировать integration assertions в `EditorWorkOrdersView.test.ts`**

In `renders selected preview and opens from the right panel`, replace the exact action text assertion with:

```ts
    expect(
      wrapper
        .get('[data-test="workspace-open-action"]')
        .get('[data-ui-control-state="idle"]')
        .text(),
    ).toBe("Начать");
```

In `renders continue for an in-progress preview`, replace the exact action text assertion with:

```ts
    expect(
      wrapper
        .get('[data-test="workspace-open-action"]')
        .get('[data-ui-control-state="idle"]')
        .text(),
    ).toBe("Продолжить");
```

In `does not label a newly selected work order as opening`, replace the existing `action.text()` assertion and keep the disabled assertion as:

```ts
    const action = wrapper.get('[data-test="workspace-open-action"]');
    expect(action.get('[data-ui-control-state="idle"]').text()).toBe(
      "Начать",
    );
    expect(action.attributes("disabled")).toBeDefined();
```

- [ ] **Step 5: Запустить panel/editor/primitive tests**

Run:

```powershell
npm test -- src/components/WorkspaceDetailsPanel.test.ts src/components/EditorWorkOrdersView.test.ts src/components/ui/UiButton.test.ts
```

Expected: 3 files PASS; focus transfer, workspace announcements and map-mode regressions stay green.

- [ ] **Step 6: Оставить unstaged review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; Task 5 files remain unstaged.

---

### Task 6: Icons и clipboard loading в `ActionableError`

**Files:**

- Modify: `apps/frontend/src/components/ActionableError.test.ts`
- Modify: `apps/frontend/src/components/ActionableError.vue`

**Interfaces:**

- Consumes: `UiButton`, `Copy`, `FolderOpen`, `LogIn`, `RefreshCw`, `RotateCcw`, `LucideIcon`, `ErrorActionId`.
- Produces: exhaustive `Record<ErrorActionId, LucideIcon>`; existing emit payload и error copy не меняются; local `isCopying` существует только во время Clipboard promise.

- [ ] **Step 1: Добавить failing icon mapping и pending clipboard tests**

Update imports in `ActionableError.test.ts` to:

```ts
import { flushPromises, mount } from "@vue/test-utils";
import {
  FolderOpen,
  LogIn,
  RefreshCw,
  RotateCcw,
  type LucideIcon,
} from "@lucide/vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ActionableError from "@/components/ActionableError.vue";
import UiButton from "@/components/ui/UiButton.vue";
import type { ErrorActionId, ErrorPresentation } from "@/contracts/api-error";
```

Add inside `describe("ActionableError", ...)`:

```ts
  it.each(
    [
      ["retry", RotateCcw],
      ["refresh", RefreshCw],
      ["reopen", FolderOpen],
      ["sign-in", LogIn],
    ] satisfies [ErrorActionId, LucideIcon][],
  )("maps %s to the agreed Lucide icon", (actionId, expectedIcon) => {
    const actionPresentation: ErrorPresentation = {
      summary: "Ошибка операции",
      guidance: null,
      action: { id: actionId, label: "Выполнить действие" },
      diagnostics: { code: null, correlationId: null },
    };
    const wrapper = mount(ActionableError, {
      props: { presentation: actionPresentation },
    });

    expect(wrapper.getComponent(UiButton).props("icon")).toBe(expectedIcon);
  });

  it("blocks duplicate clipboard writes while copy is pending", async () => {
    let resolveWriteText: (() => void) | undefined;
    const writeText = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveWriteText = resolve;
        }),
    );
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    const wrapper = mount(ActionableError, { props: { presentation } });
    const copyButton = wrapper.get('[data-test="copy-correlation-id"]');

    await copyButton.trigger("click");
    expect(copyButton.attributes("disabled")).toBeDefined();
    expect(copyButton.attributes("aria-busy")).toBe("true");
    expect(copyButton.attributes("aria-label")).toBe(
      "Копируем код обращения",
    );
    expect(
      copyButton.get('[data-ui-control-state="loading"]').classes(),
    ).not.toContain("isHidden");
    expect(
      copyButton.get('[data-ui-control-state="loading"]').text(),
    ).toBe("Копируем…");

    await copyButton.trigger("click");
    expect(writeText).toHaveBeenCalledTimes(1);

    resolveWriteText?.();
    await flushPromises();
    expect(copyButton.attributes("disabled")).toBeUndefined();
    expect(wrapper.get('[data-test="copy-status"]').text()).toBe(
      "Код обращения скопирован",
    );
  });
```

- [ ] **Step 2: Запустить test и подтвердить RED**

Run:

```powershell
npm test -- src/components/ActionableError.test.ts
```

Expected: FAIL, потому что action/copy всё ещё native buttons без `UiButton`, icon props и `isCopying`.

- [ ] **Step 3: Реализовать exhaustive icon mapping и copy state**

Add imports to `ActionableError.vue`:

```ts
import {
  Copy,
  FolderOpen,
  LogIn,
  RefreshCw,
  RotateCcw,
  type LucideIcon,
} from "@lucide/vue";

import UiButton from "@/components/ui/UiButton.vue";
```

Add next to existing refs/computed values:

```ts
const isCopying = ref(false);

const errorActionIcons: Record<ErrorActionId, LucideIcon> = {
  retry: RotateCcw,
  refresh: RefreshCw,
  reopen: FolderOpen,
  "sign-in": LogIn,
};

function errorActionIcon(actionId: ErrorActionId): LucideIcon {
  return errorActionIcons[actionId];
}
```

Replace `copyCorrelationId` with:

```ts
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
```

- [ ] **Step 4: Заменить native action buttons на `UiButton`**

Replace the current error-action native button with:

```vue
    <UiButton
      v-if="props.presentation.action"
      :icon="errorActionIcon(props.presentation.action.id)"
      variant="error"
      data-test="error-action"
      @click="emitAction"
    >
      {{ props.presentation.action.label }}
    </UiButton>
```

Replace the correlation-id copy native button with:

```vue
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
```

Remove `.errorAction, .errorDiagnostics button` CSS block from `ActionableError.vue`; variant styling now belongs to `UiButton`.

- [ ] **Step 5: Запустить ActionableError и consumer tests**

Run:

```powershell
npm test -- src/components/ActionableError.test.ts src/App.test.ts src/components/EditorWorkOrdersView.test.ts src/components/WorkspaceDetailsPanel.test.ts
```

Expected: 4 files PASS; existing retry, sign-in, reopen, diagnostics and clipboard failure behavior remains green.

- [ ] **Step 6: Оставить unstaged review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; all implementation changes unstaged.

---

### Task 7: Полная автоматическая и ручная проверка

**Files:**

- Verify only: все files из Tasks 1–6.
- Modify только при обнаружении конкретной regression: соответствующий source/test из Tasks 1–6.

**Interfaces:**

- Consumes: полный operational control flow.
- Produces: доказательство test/type/lint/format/build и manual accessibility/visual acceptance; Git changes остаются unstaged.

- [ ] **Step 1: Запустить полный targeted regression set**

Run из `apps/frontend`:

```powershell
npm test -- src/components/ui/UiButton.test.ts src/components/ui/UiIconButton.test.ts src/App.test.ts src/components/EditorWorkOrdersView.test.ts src/components/WorkspaceDetailsPanel.test.ts src/components/ActionableError.test.ts
```

Expected: 6 test files PASS; no unhandled promise rejection или Vue warning.

- [ ] **Step 2: Запустить весь frontend test suite**

Run:

```powershell
npm test
```

Expected: all test files PASS, exit code `0`.

- [ ] **Step 3: Запустить static и production checks**

Run:

```powershell
npm run typecheck
npm run lint
npm run format:check
npm run build
```

Expected: каждая команда exit code `0`; Vite production build завершается без unresolved `@lucide/vue` imports.

- [ ] **Step 4: Выполнить desktop visual/keyboard review**

Run из `infra` в отдельном terminal, чтобы поднять backend, seed data и frontend вместе:

```powershell
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up --build
```

Expected: `postgis`, migration/seed chain, `utility_service` и `frontend-dev` healthy; frontend доступен на `http://localhost:5173`.

Open `http://localhost:5173`, login as
`alexey.editor@example.local` / `alexey-editor-password` and verify at viewport
wider than `760 px`:

- top bar показывает `LogOut` + `Выйти`;
- panel header показывает только `RefreshCw`;
- `Начать`/`Продолжить`, error actions и copy остаются icon+text;
- hover tooltip появляется примерно через `500 ms`, не перекрывает trigger, остаётся при pointer над tooltip;
- `Tab` открывает tooltip немедленно, `Escape` закрывает его без потери focus;
- `Enter`/`Space` выполняют button action;
- loading refresh/open/copy не меняет control width и блокирует повторный click;
- focus ring полностью видим.

Stop Compose foreground process через `Ctrl+C` после проверки. Не выполнять
`docker compose down -v`: удаление disposable DB volume не требуется этой задаче.

- [ ] **Step 5: Выполнить narrow и reduced-motion review**

At viewport `760 px` and then `320 px` verify:

- desktop logout hidden, icon-only logout visible и имеет target `44 x 44 px`;
- logout и refresh tooltips с `tooltipAlign="end"` не выходят за правый край;
- все icon+text controls остаются читаемыми без horizontal overflow;
- refresh target равен `44 x 44 px`;
- при emulated `prefers-reduced-motion: reduce` loader не вращается, но loading text/`aria-label`, `aria-busy` и disabled state остаются.

- [ ] **Step 6: Выполнить screen-reader smoke**

Keyboard/screen-reader pass должен озвучить:

- refresh idle: `Обновить`, затем описание `Обновить список назначенных нарядов`;
- refresh loading: `Обновление списка нарядов`, busy/disabled state;
- mobile logout: `Выйти`, затем описание `Выйти из GeoService`;
- Lucide SVG не озвучиваются отдельно;
- loading/open/copy live regions не дублируют бессмысленно один и тот же текст.

- [ ] **Step 7: Проверить final diff и передать пользователю unstaged changes**

Run из repository root:

```powershell
git diff --check
git status --short
git diff --stat
```

Expected: no whitespace errors; только spec/plan и files из Tasks 1–6; ничего не staged. Сообщить пользователю результаты tests/manual review и перечислить files для его review. Не выполнять `git add`, `git commit` или `git push`.

## Memory и knowledge pipeline

Design spec, implementation plan и будущий focused code уже являются каноническими источниками решения. Не создавать agent memory и не запускать `/ingest repository-change` только из-за завершения задачи. После реализации повторно оценить durable knowledge; обновление допустимо только если обнаружится новый устойчивый pattern или non-obvious constraint, которого нет в spec/plan/code.
