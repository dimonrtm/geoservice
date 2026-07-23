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
const resolvedTooltipAlign = computed(() => props.tooltipAlign ?? "center");
const resolvedVariant = computed(() => props.variant ?? "secondary");
const isLoadingRequested = computed(() => props.loading === true);
const isLoadingVisible = computed(
  () => isLoadingRequested.value && hasNonEmptyLoadingLabel(props.loadingLabel),
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
  warnInvalidLoadingLabel("UiIconButton", props.loading, props.loadingLabel);
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
        uiControlPrimary: resolvedVariant === 'primary',
        uiControlSecondary: resolvedVariant === 'secondary',
        uiControlError: resolvedVariant === 'error',
      }"
      :type="nativeType"
      :disabled="isDisabled"
      :aria-label="accessibleLabel"
      :aria-describedby="tooltipId"
      :aria-busy="isLoadingRequested ? 'true' : undefined"
      @focus="handleFocus"
      @blur="handleBlur"
      @keydown.esc="dismissTooltip"
    >
      <component
        :is="renderedIcon"
        class="uiControlIcon"
        :class="{ uiControlLoader: isLoadingVisible }"
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
        uiControlTooltipCenter: resolvedTooltipAlign === 'center',
        uiControlTooltipEnd: resolvedTooltipAlign === 'end',
      }"
      role="tooltip"
      :data-state="isTooltipOpen ? 'open' : 'closed'"
    >
      {{ props.tooltip }}
    </span>
  </span>
</template>
