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
  warnInvalidLoadingLabel("UiButton", props.loading, props.loadingLabel);
});
</script>

<template>
  <button
    v-bind="$attrs"
    class="uiControl uiControlText"
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
        <span class="uiControlLabel"><slot /></span>
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
        <span class="uiControlLabel">{{ props.loadingLabel }}</span>
      </span>
    </span>
  </button>
</template>
