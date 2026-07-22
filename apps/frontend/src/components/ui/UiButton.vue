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
    loadingLabel: undefined,
    disabled: false,
  },
);

const attrs = useAttrs();
const nativeType = computed<NativeButtonType>(() => {
  const candidate = attrs.type;
  return candidate === "submit" ||
    candidate === "reset" ||
    candidate === "button"
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
