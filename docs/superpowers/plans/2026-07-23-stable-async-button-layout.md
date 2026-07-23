# Стабильная геометрия асинхронных кнопок — Implementation Plan

> **Для agentic workers:** REQUIRED SUB-SKILL: используйте `superpowers:subagent-driven-development` (рекомендуется) или `superpowers:executing-plans`, чтобы выполнять этот план task-by-task. Для отслеживания используются checkbox-шаги (`- [ ]`).

**Goal:** Завершить общий контракт асинхронных кнопок так, чтобы idle/loading-переходы не меняли их геометрию, loading labels всегда были предметными, а login использовал тот же `UiButton`.

**Architecture:** `UiButton` резервирует intrinsic width двух одновременно смонтированных CSS-grid слоёв, а `UiIconButton` сохраняет фиксированный квадрат. Маленький shared TypeScript module задаёт union для синхронной и асинхронной формы props и единое runtime-правило непустого `loadingLabel`; caller или store по-прежнему владеет Promise и loading state.

**Tech Stack:** Vue 3.5, TypeScript 5.9, Vite 7, Vitest 3.2, Vue Test Utils 2.4, `@lucide/vue` v1, CSS.

## Global Constraints

- Канонический дизайн: `docs/superpowers/specs/2026-07-23-stable-async-button-layout-design.md`.
- Разные text buttons сохраняют индивидуальную ширину; размеры `sm`, `md`, `lg` и единый `min-width` не добавляются.
- Асинхронная форма control обязана передавать одновременно `loading: boolean` и непустой предметный `loadingLabel`.
- Generic fallback `Выполняется…` удаляется из `UiButton` и `UiIconButton`.
- При invalid loading contract control остаётся `disabled` и `aria-busy="true"`, но безопасно показывает idle icon/label и выдаёт development warning.
- Один control резервирует только idle label и один стабильный `loadingLabel`; multi-phase loading copy не добавляется.
- Desktop control height — ровно `36 px`; при viewport `<=760 px` — ровно `44 px`.
- Desktop icon-only control — `36 x 36 px`; при viewport `<=760 px` — `44 x 44 px`; icon — `18 px`.
- Text label не переносится, а при нехватке места получает ellipsis; полный active label остаётся в DOM.
- `LoginScreen` использует `UiButton`, `LogIn`, `variant="primary"`, `loadingLabel="Выполняем вход…"` и `inline-size: 100%`.
- Не менять backend, API contracts, Pinia stores, domain behavior, error presentation policy и legacy editing toolbar `MapView`.
- Не добавлять Playwright, Cypress, screenshot infrastructure или runtime dependencies.
- Human-readable plan/spec content остаётся на русском; paths, commands, types, identifiers, package names и code не переводятся.
- Реализацию вести TDD: focused failing test, подтверждённый RED, минимальный production code, focused GREEN, затем regression.
- В этом репозитории запрещены `git add`, `git commit` и `git push`. Commit-шаги из общего `writing-plans` workflow намеренно исключены; после каждой task changes остаются unstaged.
- Baseline 2026-07-23: шесть затронутых/regression test files — `44 passed`; `npm run typecheck` — exit code `0`.

## File Structure

- Create `apps/frontend/src/components/ui/ui-control-loading.ts` — shared union `UiControlLoadingProps`, проверка непустой подписи и development diagnostic.
- Create `apps/frontend/src/components/ui/ui-control-loading.typecheck.ts` — positive/negative compile-time fixtures для union contract.
- Modify `apps/frontend/src/components/ui/UiButton.vue` — строгая loading-форма props, безопасный invalid fallback и два стабильных text layers.
- Modify `apps/frontend/src/components/ui/UiButton.test.ts` — reservation, invalid contract и constrained-label hooks.
- Modify `apps/frontend/src/components/ui/UiIconButton.vue` — тот же loading contract без изменения tooltip state machine.
- Modify `apps/frontend/src/components/ui/UiIconButton.test.ts` — safe accessible fallback при invalid loading label.
- Modify `apps/frontend/src/components/ui/ui-controls.css` — intrinsic width reservation, ограничение parent width, ellipsis и точные responsive heights.
- Modify `apps/frontend/src/components/LoginScreen.vue` — заменить native submit на full-width `UiButton`.
- Modify `apps/frontend/src/components/LoginScreen.test.ts` — deferred login test для idle/loading/idle и duplicate-action protection.
- Verify `apps/frontend/src/components/WorkspaceDetailsPanel.test.ts` — существующий open-workspace loading regression.
- Verify `apps/frontend/src/components/ActionableError.test.ts` — существующий clipboard loading regression.
- Verify `apps/frontend/src/components/EditorWorkOrdersView.test.ts` — существующий refresh loading regression.

---

### Task 1: Строгий loading contract для `UiButton`

**Files:**

- Create: `apps/frontend/src/components/ui/ui-control-loading.ts`
- Create: `apps/frontend/src/components/ui/ui-control-loading.typecheck.ts`
- Modify: `apps/frontend/src/components/ui/UiButton.vue:1-92`
- Modify: `apps/frontend/src/components/ui/UiButton.test.ts:1-60`

**Interfaces:**

- Consumes: `LucideIcon` и `LoaderCircle` из `@lucide/vue`.
- Produces: `UiControlLoadingProps`, допускающий только `{}` или `{ loading: boolean; loadingLabel: string }`.
- Produces: `hasNonEmptyLoadingLabel(value: string | undefined): value is string`.
- Produces: `warnInvalidLoadingLabel(componentName, loading, loadingLabel): void`.
- Produces: `UiButton`, который при valid loading показывает loader/label, а при invalid loading остаётся busy/disabled с idle content.

- [ ] **Step 1: Добавить failing tests reservation и invalid loading label**

В `apps/frontend/src/components/ui/UiButton.test.ts` расширить import из Vitest:

```ts
import { afterEach, describe, expect, it, vi } from "vitest";
```

Сразу после imports добавить cleanup:

```ts
afterEach(() => {
  vi.restoreAllMocks();
});
```

Внутрь `describe("UiButton", ...)` добавить два tests:

```ts
it("mounts the declared loading layer before loading starts", () => {
  const wrapper = mount(UiButton, {
    props: {
      icon: Play,
      loading: false,
      loadingLabel: "Открываем…",
    },
    slots: { default: "Продолжить" },
  });

  const button = wrapper.get("button");
  const idle = button.get('[data-ui-control-state="idle"]');
  const loading = button.get('[data-ui-control-state="loading"]');

  expect(idle.classes()).not.toContain("isHidden");
  expect(idle.attributes("aria-hidden")).toBeUndefined();
  expect(loading.classes()).toContain("isHidden");
  expect(loading.attributes("aria-hidden")).toBe("true");
  expect(loading.text()).toBe("Открываем…");
});

it("keeps idle content visible and warns for an empty loading label", () => {
  const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
  const wrapper = mount(UiButton, {
    props: {
      icon: Play,
      loading: true,
      loadingLabel: "   ",
    },
    slots: { default: "Продолжить" },
  });

  const button = wrapper.get("button");
  expect(warn).toHaveBeenCalledWith(expect.stringContaining("loadingLabel"));
  expect(button.attributes("disabled")).toBeDefined();
  expect(button.attributes("aria-busy")).toBe("true");
  expect(
    button.get('[data-ui-control-state="idle"]').classes(),
  ).not.toContain("isHidden");
  expect(button.find('[data-ui-control-state="loading"]').exists()).toBe(false);
  expect(wrapper.findComponent(LoaderCircle).exists()).toBe(false);
});
```

- [ ] **Step 2: Запустить focused test и подтвердить RED**

Run из `apps/frontend`:

```powershell
npm test -- src/components/ui/UiButton.test.ts
```

Expected: exit code `1`; test `keeps idle content visible and warns for an empty loading label` падает, потому что warning отсутствует, idle layer скрыт и `LoaderCircle` показан.

- [ ] **Step 3: Создать shared loading contract**

Создать `apps/frontend/src/components/ui/ui-control-loading.ts`:

```ts
export type UiControlLoadingProps =
  | {
      loading?: undefined;
      loadingLabel?: undefined;
    }
  | {
      loading: boolean;
      loadingLabel: string;
    };

export function hasNonEmptyLoadingLabel(
  loadingLabel: string | undefined,
): loadingLabel is string {
  return (
    typeof loadingLabel === "string" && loadingLabel.trim().length > 0
  );
}

export function warnInvalidLoadingLabel(
  componentName: string,
  loading: boolean | undefined,
  loadingLabel: string | undefined,
): void {
  if (
    !import.meta.env.DEV ||
    loading !== true ||
    hasNonEmptyLoadingLabel(loadingLabel)
  ) {
    return;
  }

  console.warn(
    `[${componentName}] loadingLabel должен быть непустой строкой при loading=true.`,
  );
}
```

- [ ] **Step 4: Зафиксировать positive/negative compile-time fixtures**

Создать `apps/frontend/src/components/ui/ui-control-loading.typecheck.ts`:

```ts
import type { UiControlLoadingProps } from "@/components/ui/ui-control-loading";

const synchronousState: UiControlLoadingProps = {};
const asyncIdleState: UiControlLoadingProps = {
  loading: false,
  loadingLabel: "Открываем…",
};
const asyncBusyState: UiControlLoadingProps = {
  loading: true,
  loadingLabel: "Открываем…",
};

// @ts-expect-error loading=true requires loadingLabel
const missingLoadingLabel: UiControlLoadingProps = { loading: true };

// @ts-expect-error loadingLabel cannot be passed without loading
const labelWithoutLoading: UiControlLoadingProps = {
  loadingLabel: "Открываем…",
};

void [
  synchronousState,
  asyncIdleState,
  asyncBusyState,
  missingLoadingLabel,
  labelWithoutLoading,
];
```

- [ ] **Step 5: Перевести `UiButton` на union и safe loading state**

В `apps/frontend/src/components/ui/UiButton.vue` заменить весь
`<script setup>` и `<template>` следующим содержимым:

```vue
<script setup lang="ts">
import { LoaderCircle, type LucideIcon } from "@lucide/vue";
import { computed, useAttrs, watchEffect } from "vue";

import {
  hasNonEmptyLoadingLabel,
  type UiControlLoadingProps,
  warnInvalidLoadingLabel,
} from "@/components/ui/ui-control-loading";
import "@/components/ui/ui-controls.css";

defineOptions({ inheritAttrs: false });

type UiControlVariant = "primary" | "secondary" | "error";
type NativeButtonType = "button" | "submit" | "reset";
type UiButtonBaseProps = {
  icon: LucideIcon;
  variant?: UiControlVariant;
  disabled?: boolean;
};

const props = defineProps<UiButtonBaseProps & UiControlLoadingProps>();

const attrs = useAttrs();
const nativeType = computed<NativeButtonType>(() => {
  const candidate = attrs.type;
  return candidate === "submit" ||
    candidate === "reset" ||
    candidate === "button"
    ? candidate
    : "button";
});
const resolvedVariant = computed(() => props.variant ?? "secondary");
const isLoadingRequested = computed(() => props.loading === true);
const hasLoadingLayer = computed(() =>
  hasNonEmptyLoadingLabel(props.loadingLabel),
);
const isLoadingVisible = computed(
  () => isLoadingRequested.value && hasLoadingLayer.value,
);
const isDisabled = computed(
  () => props.disabled === true || isLoadingRequested.value,
);

watchEffect(() => {
  warnInvalidLoadingLabel(
    "UiButton",
    props.loading,
    props.loadingLabel,
  );
});
</script>

<template>
  <button
    v-bind="$attrs"
    class="uiControl"
    :class="{
      uiControlPrimary: resolvedVariant === 'primary',
      uiControlSecondary: resolvedVariant === 'secondary',
      uiControlError: resolvedVariant === 'error',
    }"
    :type="nativeType"
    :disabled="isDisabled"
    :aria-busy="isLoadingRequested ? 'true' : undefined"
  >
    <span class="uiControlStableContent">
      <span
        class="uiControlContent"
        :class="{ isHidden: isLoadingVisible }"
        data-ui-control-state="idle"
        :aria-hidden="isLoadingVisible ? 'true' : undefined"
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
        v-if="hasLoadingLayer"
        class="uiControlContent"
        :class="{ isHidden: !isLoadingVisible }"
        data-ui-control-state="loading"
        :aria-hidden="isLoadingVisible ? undefined : 'true'"
      >
        <LoaderCircle
          class="uiControlIcon uiControlLoader"
          :size="18"
          :stroke-width="2"
          aria-hidden="true"
          focusable="false"
        />
        <span>{{ props.loadingLabel }}</span>
      </span>
    </span>
  </button>
</template>
```

- [ ] **Step 6: Запустить focused GREEN и compile-time contract**

Run из `apps/frontend`:

```powershell
npm test -- src/components/ui/UiButton.test.ts
npm run typecheck
```

Expected: обе команды завершаются с exit code `0`; `UiButton.test.ts` содержит `4 passed`; `vue-tsc --noEmit` не сообщает ошибок union props.

- [ ] **Step 7: Оставить read-only review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: `git diff --check` не печатает ошибок; новый helper и изменения `UiButton`/test остаются unstaged. Не выполнять `git add`, `git commit` или `git push`.

---

### Task 2: Тот же contract для `UiIconButton`

**Files:**

- Modify: `apps/frontend/src/components/ui/UiIconButton.vue:1-151`
- Modify: `apps/frontend/src/components/ui/UiIconButton.test.ts:1-113`

**Interfaces:**

- Consumes: `UiControlLoadingProps`, `hasNonEmptyLoadingLabel` и `warnInvalidLoadingLabel` из Task 1.
- Preserves: props `icon`, `label`, `tooltip`, `tooltipAlign`, `variant`, `disabled` и существующую tooltip state machine.
- Produces: valid loading доступен через `isLoadingVisible`; invalid loading сохраняет idle icon и `label`, но оставляет button busy/disabled.

- [ ] **Step 1: Добавить failing safe-fallback test**

В существующий `afterEach` добавить restore mocks:

```ts
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});
```

Внутрь `describe("UiIconButton", ...)` добавить:

```ts
it("keeps the idle accessible state for an empty loading label", () => {
  const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
  const wrapper = mount(UiIconButton, {
    props: {
      icon: RefreshCw,
      label: "Обновить",
      tooltip: "Обновить список назначенных нарядов",
      loading: true,
      loadingLabel: " ",
    },
  });

  const button = wrapper.get("button");
  expect(warn).toHaveBeenCalledWith(expect.stringContaining("loadingLabel"));
  expect(button.attributes("disabled")).toBeDefined();
  expect(button.attributes("aria-busy")).toBe("true");
  expect(button.attributes("aria-label")).toBe("Обновить");
  expect(button.get("svg").classes()).not.toContain("uiControlLoader");
});
```

- [ ] **Step 2: Запустить focused test и подтвердить RED**

Run из `apps/frontend`:

```powershell
npm test -- src/components/ui/UiIconButton.test.ts
```

Expected: exit code `1`; новый test падает, потому что текущий component показывает loader и использует whitespace как accessible name без warning.

- [ ] **Step 3: Заменить `<script setup>` `UiIconButton`**

В `apps/frontend/src/components/ui/UiIconButton.vue` заменить весь
`<script setup>`:

```vue
<script setup lang="ts">
import { LoaderCircle, type LucideIcon } from "@lucide/vue";
import {
  computed,
  onBeforeUnmount,
  ref,
  useAttrs,
  useId,
  watchEffect,
} from "vue";

import {
  hasNonEmptyLoadingLabel,
  type UiControlLoadingProps,
  warnInvalidLoadingLabel,
} from "@/components/ui/ui-control-loading";
import "@/components/ui/ui-controls.css";

defineOptions({ inheritAttrs: false });

type UiControlVariant = "primary" | "secondary" | "error";
type TooltipAlign = "center" | "end";
type NativeButtonType = "button" | "submit" | "reset";
type UiIconButtonBaseProps = {
  icon: LucideIcon;
  label: string;
  tooltip: string;
  tooltipAlign?: TooltipAlign;
  variant?: UiControlVariant;
  disabled?: boolean;
};

const props = defineProps<UiIconButtonBaseProps & UiControlLoadingProps>();

const attrs = useAttrs();
const tooltipId = `ui-tooltip-${useId()}`;
const isTooltipOpen = ref(false);
const hasKeyboardFocus = ref(false);
let hoverTimer: number | null = null;

const nativeType = computed<NativeButtonType>(() => {
  const candidate = attrs.type;
  return candidate === "submit" ||
    candidate === "reset" ||
    candidate === "button"
    ? candidate
    : "button";
});
const resolvedTooltipAlign = computed(
  () => props.tooltipAlign ?? "center",
);
const resolvedVariant = computed(() => props.variant ?? "secondary");
const isLoadingRequested = computed(() => props.loading === true);
const isLoadingVisible = computed(
  () =>
    isLoadingRequested.value &&
    hasNonEmptyLoadingLabel(props.loadingLabel),
);
const isDisabled = computed(
  () => props.disabled === true || isLoadingRequested.value,
);
const accessibleLabel = computed(() =>
  isLoadingVisible.value ? props.loadingLabel : props.label,
);
const renderedIcon = computed(() =>
  isLoadingVisible.value ? LoaderCircle : props.icon,
);

watchEffect(() => {
  warnInvalidLoadingLabel(
    "UiIconButton",
    props.loading,
    props.loadingLabel,
  );
});

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
```

- [ ] **Step 4: Переключить template только на validated loading state**

В button variant bindings использовать resolved values:

```vue
:class="{
  uiControlPrimary: resolvedVariant === 'primary',
  uiControlSecondary: resolvedVariant === 'secondary',
  uiControlError: resolvedVariant === 'error',
}"
```

Заменить state attributes button:

```vue
:disabled="isDisabled"
:aria-label="accessibleLabel"
:aria-describedby="tooltipId"
:aria-busy="isLoadingRequested ? 'true' : undefined"
```

Заменить loader class:

```vue
:class="{ uiControlLoader: isLoadingVisible }"
```

В tooltip alignment bindings использовать:

```vue
:class="{
  uiControlTooltipCenter: resolvedTooltipAlign === 'center',
  uiControlTooltipEnd: resolvedTooltipAlign === 'end',
}"
```

- [ ] **Step 5: Запустить focused GREEN, combined regression и typecheck**

Run из `apps/frontend`:

```powershell
npm test -- src/components/ui/UiButton.test.ts src/components/ui/UiIconButton.test.ts
npm run typecheck
```

Expected: exit code `0`; два files и `9 tests` проходят; `vue-tsc --noEmit` не сообщает ошибок.

- [ ] **Step 6: Оставить read-only review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: нет whitespace errors; changes остаются unstaged.

---

### Task 3: Constrained intrinsic width и ellipsis

**Files:**

- Modify: `apps/frontend/src/components/ui/UiButton.vue:44-92`
- Modify: `apps/frontend/src/components/ui/UiButton.test.ts`
- Modify: `apps/frontend/src/components/ui/ui-controls.css:1-181`

**Interfaces:**

- Consumes: stable idle/loading DOM из Task 1.
- Produces: root class `.uiControlText` только для text button.
- Produces: `.uiControlLabel` на обеих подписях.
- Produces: CSS max-content reservation, parent cap и exact `36 px`/`44 px` heights.

- [ ] **Step 1: Добавить failing DOM-hook test**

В `UiButton.test.ts` добавить:

```ts
it("exposes constrained text hooks for both stable labels", () => {
  const wrapper = mount(UiButton, {
    props: {
      icon: Play,
      loading: false,
      loadingLabel: "Предметная длинная loading-подпись",
    },
    slots: { default: "Короткое действие" },
  });

  const button = wrapper.get("button");
  const labels = button.findAll(".uiControlLabel");

  expect(button.classes()).toContain("uiControlText");
  expect(labels).toHaveLength(2);
  expect(labels[0]?.text()).toBe("Короткое действие");
  expect(labels[1]?.text()).toBe(
    "Предметная длинная loading-подпись",
  );
});
```

- [ ] **Step 2: Запустить focused test и подтвердить RED**

Run из `apps/frontend`:

```powershell
npm test -- src/components/ui/UiButton.test.ts
```

Expected: exit code `1`; новый test не находит `.uiControlText` и `.uiControlLabel`.

- [ ] **Step 3: Добавить text-specific classes в `UiButton`**

В root button заменить class:

```vue
class="uiControl uiControlText"
```

Idle slot wrapper заменить на:

```vue
<span class="uiControlLabel"><slot /></span>
```

Loading label wrapper заменить на:

```vue
<span class="uiControlLabel">{{ props.loadingLabel }}</span>
```

- [ ] **Step 4: Уточнить CSS geometry**

В `apps/frontend/src/components/ui/ui-controls.css` после `.uiControlIconOnly`
добавить:

```css
.uiControlText {
  min-inline-size: 0;
  max-inline-size: 100%;
}
```

Заменить blocks stable content и control content:

```css
.uiControlStableContent {
  display: grid;
  place-items: center;
  min-inline-size: 0;
  inline-size: max-content;
  max-inline-size: 100%;
}

.uiControlContent {
  grid-area: 1 / 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-inline-size: 0;
  max-inline-size: 100%;
  overflow: hidden;
  white-space: nowrap;
}

.uiControlLabel {
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

В media query заменить text-control minimum на точную height:

```css
@media (max-width: 760px) {
  .uiControl {
    height: 44px;
  }

  .uiControlIconOnly {
    width: 44px;
    height: 44px;
  }
}
```

Desktop `.uiControl { height: 36px; }` и `.uiControlIconOnly { width: 36px; }`
оставить без изменений. Не добавлять max-width к `.uiControlIconOnly`, чтобы
его touch target не сжимался.

- [ ] **Step 5: Запустить focused GREEN и style gates**

Run из `apps/frontend`:

```powershell
npm test -- src/components/ui/UiButton.test.ts
npm run typecheck
npm run lint
npm run format:check
```

Expected: все команды завершаются с exit code `0`; `UiButton.test.ts` содержит `5 passed`.

- [ ] **Step 6: Оставить read-only review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: нет whitespace errors; CSS, component и tests остаются unstaged.

---

### Task 4: Миграция login submit на `UiButton`

**Files:**

- Modify: `apps/frontend/src/components/LoginScreen.vue:1-166`
- Modify: `apps/frontend/src/components/LoginScreen.test.ts:1-75`

**Interfaces:**

- Consumes: `UiButton` из Task 1 и constrained styles из Task 3.
- Preserves: `onSubmit`, `isSubmitting`, `ErrorPresentation` и
  `auth.loginWithPassword(email, password)`.
- Produces: `data-test="login-submit"`, full-width primary button, idle
  `Войти`, loading `Выполняем вход…`, icon `LogIn`.

- [ ] **Step 1: Добавить deferred helper и failing pending-state test**

В `LoginScreen.test.ts` добавить import:

```ts
import { nextTick } from "vue";
```

Перед `describe("LoginScreen", ...)` добавить:

```ts
function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}
```

Внутрь `describe` добавить:

```ts
it("keeps stable button layers while login is pending", async () => {
  const loginDeferred = createDeferred<void>();
  loginWithPasswordMock.mockReturnValue(loginDeferred.promise);

  const { default: LoginScreen } =
    await import("@/components/LoginScreen.vue");
  const wrapper = mount(LoginScreen);

  await wrapper
    .get('input[type="email"]')
    .setValue("editor@example.local");
  await wrapper
    .get('input[type="password"]')
    .setValue("editor-password");

  const button = wrapper.get('[data-test="login-submit"]');
  const idle = button.get('[data-ui-control-state="idle"]');
  const loading = button.get('[data-ui-control-state="loading"]');

  expect(button.classes()).toContain("submitButton");
  expect(idle.text()).toBe("Войти");
  expect(idle.classes()).not.toContain("isHidden");
  expect(loading.text()).toBe("Выполняем вход…");
  expect(loading.classes()).toContain("isHidden");

  await wrapper.get("form").trigger("submit");
  await nextTick();

  expect(loginWithPasswordMock).toHaveBeenCalledTimes(1);
  expect(button.attributes("disabled")).toBeDefined();
  expect(button.attributes("aria-busy")).toBe("true");
  expect(idle.classes()).toContain("isHidden");
  expect(loading.classes()).not.toContain("isHidden");

  await button.trigger("click");
  expect(loginWithPasswordMock).toHaveBeenCalledTimes(1);

  loginDeferred.resolve();
  await flushPromises();

  expect(button.attributes("disabled")).toBeUndefined();
  expect(button.attributes("aria-busy")).toBeUndefined();
  expect(idle.classes()).not.toContain("isHidden");
  expect(loading.classes()).toContain("isHidden");
});
```

- [ ] **Step 2: Запустить focused test и подтвердить RED**

Run из `apps/frontend`:

```powershell
npm test -- src/components/LoginScreen.test.ts
```

Expected: exit code `1`; новый test не находит `[data-test="login-submit"]` и stable layers у текущего native button.

- [ ] **Step 3: Заменить native submit template**

В `LoginScreen.vue` заменить native `<button>`:

```vue
<UiButton
  class="submitButton"
  :icon="LogIn"
  variant="primary"
  type="submit"
  :loading="isSubmitting"
  loading-label="Выполняем вход…"
  data-test="login-submit"
>
  Войти
</UiButton>
```

- [ ] **Step 4: Добавить imports `LogIn` и `UiButton`**

В начало `<script setup>` добавить:

```ts
import { LogIn } from "@lucide/vue";
```

Рядом с `ActionableError` добавить:

```ts
import UiButton from "@/components/ui/UiButton.vue";
```

Остальные imports и `onSubmit` не менять.

- [ ] **Step 5: Оставить локальному style только full-width responsibility**

Заменить `.submitButton` и удалить `.submitButton:disabled`:

```css
.submitButton {
  inline-size: 100%;
}
```

Height, padding, border, color, cursor и disabled/loading styles теперь
принадлежат shared `UiButton`.

- [ ] **Step 6: Запустить focused GREEN и существующие error regressions**

Run из `apps/frontend`:

```powershell
npm test -- src/components/LoginScreen.test.ts src/components/ActionableError.test.ts
npm run typecheck
```

Expected: exit code `0`; `LoginScreen.test.ts` содержит `3 passed`,
`ActionableError.test.ts` содержит `10 passed`, typecheck не сообщает ошибок.

- [ ] **Step 7: Оставить read-only review checkpoint**

Run из repository root:

```powershell
git diff --check
git status --short
```

Expected: нет whitespace errors; login/component/test changes остаются unstaged.

---

### Task 5: Полная regression и ручная geometry acceptance

**Files:**

- Verify: `apps/frontend/src/components/ui/UiButton.test.ts`
- Verify: `apps/frontend/src/components/ui/UiIconButton.test.ts`
- Verify: `apps/frontend/src/components/LoginScreen.test.ts`
- Verify: `apps/frontend/src/components/WorkspaceDetailsPanel.test.ts`
- Verify: `apps/frontend/src/components/ActionableError.test.ts`
- Verify: `apps/frontend/src/components/EditorWorkOrdersView.test.ts`
- Verify: `docs/superpowers/specs/2026-07-23-stable-async-button-layout-design.md`

**Interfaces:**

- Consumes: completed Tasks 1-4.
- Produces: automated evidence for component/regression contracts and manual evidence for real browser geometry.
- Produces no new test runner, screenshot framework, backend code or permanent debug fixture.

- [ ] **Step 1: Запустить focused regression set**

Run из `apps/frontend`:

```powershell
npm test -- src/components/ui/UiButton.test.ts src/components/ui/UiIconButton.test.ts src/components/LoginScreen.test.ts src/components/WorkspaceDetailsPanel.test.ts src/components/ActionableError.test.ts src/components/EditorWorkOrdersView.test.ts
```

Expected: exit code `0`; `6 passed` test files и `49 passed` tests.

- [ ] **Step 2: Запустить полный frontend test suite**

Run из `apps/frontend`:

```powershell
npm test
```

Expected: exit code `0`; все frontend test files проходят без unhandled errors.

- [ ] **Step 3: Запустить static и production-build gates**

Run из `apps/frontend`:

```powershell
npm run typecheck
npm run lint
npm run format:check
npm run build
```

Expected: каждая команда завершается с exit code `0`; Vite создаёт production build без TypeScript, ESLint или formatting errors.

- [ ] **Step 4: Запустить локальный demo stack для ручной проверки**

Run из repository root в отдельном terminal:

```powershell
.\scripts\dev.cmd
```

Expected: Docker Compose запускает `postgis`, migrations/seed chain, backend на
`http://localhost:8000` и frontend на `http://localhost:5173`. Для входа
использовать `alexey.editor@example.local` / `alexey-editor-password`.

- [ ] **Step 5: Проверить desktop login geometry**

В browser DevTools включить Network throttling `Slow 3G`, открыть
`http://localhost:5173`, затем до submit выполнить:

```js
window.__idleLoginRect = document
  .querySelector('[data-test="login-submit"]')
  .getBoundingClientRect()
  .toJSON();
```

Ввести demo credentials, нажать `Войти` и пока виден `Выполняем вход…`
выполнить:

```js
window.__loadingLoginRect = document
  .querySelector('[data-test="login-submit"]')
  .getBoundingClientRect()
  .toJSON();
({
  sameWidth:
    window.__idleLoginRect.width === window.__loadingLoginRect.width,
  sameHeight:
    window.__idleLoginRect.height === window.__loadingLoginRect.height,
  idle: window.__idleLoginRect,
  loading: window.__loadingLoginRect,
});
```

Expected: `sameWidth === true`, `sameHeight === true`, desktop height равна
`36`; соседние form elements не смещаются по горизонтали.

- [ ] **Step 6: Проверить mobile height и ellipsis**

Установить viewport width `390 px`, перезагрузить login screen и в DevTools
временно добавить `.loginCard { width: 170px !important; }`. Повторить
throttled submit.

Expected:

- button height до и во время loading равна `44 px`;
- button остаётся в пределах card и имеет одинаковую width в обоих states;
- `Выполняем вход…` обрезается ellipsis без второй строки;
- полный текст `Выполняем вход…` остаётся в loading DOM node и виден в
  Accessibility pane как active accessible name;
- после ошибки или завершения запроса возвращается `Войти` с той же geometry.

- [ ] **Step 7: Проверить active workspace и icon-only controls**

Вернуть обычную ширину, войти как editor, выбрать `WO-001`. С `Slow 3G`
сравнить geometry `[data-test="workspace-open-action"]` до и во время
`Открываем…`. Затем проверить `[data-test="refresh-work-orders"]` при refresh
на desktop и mobile.

Expected:

- `Начать`/`Открываем…` имеют одинаковые width/height;
- refresh остаётся `36 x 36 px` на desktop и `44 x 44 px` при `390 px`;
- loader не сдвигает heading `Мои наряды`;
- controls disabled и имеют `aria-busy="true"` во время pending request;
- focus ring не обрезается.

- [ ] **Step 8: Выполнить финальный unstaged review**

Run из repository root:

```powershell
git diff --check
git status --short
git diff -- apps/frontend/src/components/ui apps/frontend/src/components/LoginScreen.vue apps/frontend/src/components/LoginScreen.test.ts
```

Expected:

- `git diff --check` не печатает ошибок;
- status показывает только согласованные docs/frontend changes и сохраняет их unstaged;
- diff не содержит изменений backend, stores, API contracts или `MapView`;
- generic fallback `Выполняется…` отсутствует в обоих UI-примитивах;
- `loadingLabel` всех текущих async call sites является явным и предметным.

Не выполнять `git add`, `git commit` или `git push`; передать unstaged diff пользователю для review.
