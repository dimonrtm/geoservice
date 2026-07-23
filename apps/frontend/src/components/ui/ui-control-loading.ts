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
  return typeof loadingLabel === "string" && loadingLabel.trim().length > 0;
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
