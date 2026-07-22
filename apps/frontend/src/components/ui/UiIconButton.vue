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
let hoverTimer: number | null = null;

const nativeType = computed<NativeButtonType>(() => {
  const candidate = attrs.type;
  return candidate === "submit" ||
    candidate === "reset" ||
    candidate === "button"
    ? candidate
    : "button";
});
const isDisabled = computed(() => props.disabled || props.loading);
const accessibleLabel = computed(() =>
  props.loading ? props.loadingLabel : props.label,
);
const renderedIcon = computed(() =>
  props.loading ? LoaderCircle : props.icon,
);

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
