export const AUTO_RETRY_DELAYS_MS = [0, 2000, 5000, 10000, 20000] as const;
export function waitForRetry(
  delayMs: number,
  signal: AbortSignal,
): Promise<boolean> {
  if (signal.aborted) return Promise.resolve(false);
  if (delayMs === 0) return Promise.resolve(true);
  return new Promise((resolve) => {
    const finish = (value: boolean) => {
      clearTimeout(timer);
      signal.removeEventListener("abort", cancel);
      resolve(value);
    };
    const cancel = () => finish(false);
    const timer = setTimeout(() => finish(true), delayMs);
    signal.addEventListener("abort", cancel, { once: true });
  });
}
