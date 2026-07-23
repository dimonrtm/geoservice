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
