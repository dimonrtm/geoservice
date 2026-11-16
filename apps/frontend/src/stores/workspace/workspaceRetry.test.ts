import { afterEach, expect, it, vi } from "vitest";
import { AUTO_RETRY_DELAYS_MS, waitForRetry } from "./workspaceRetry";
afterEach(() => vi.useRealTimers());
it("uses the agreed delays and cancels waits without a dangling timer", async () => {
  vi.useFakeTimers();
  expect(AUTO_RETRY_DELAYS_MS).toEqual([0, 2000, 5000, 10000, 20000]);
  const abort = new AbortController();
  const waiting = waitForRetry(5000, abort.signal);
  abort.abort();
  expect(await waiting).toBe(false);
  expect(vi.getTimerCount()).toBe(0);
  const result = waitForRetry(2000, new AbortController().signal);
  await vi.advanceTimersByTimeAsync(2000);
  expect(await result).toBe(true);
});
