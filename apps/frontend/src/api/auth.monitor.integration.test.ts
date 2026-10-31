import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { fetchSessionStatus } from "./auth";
import { createSessionMonitor } from "@/auth/browserSessionMonitor";
import { createBrowserSessionCoordinator } from "@/auth/browserSessionCoordinator";
import type { BrowserSessionStatus } from "@/auth/browserSessionTypes";

const post = vi.hoisted(() => vi.fn());
vi.mock("@/api/http", () => ({ http: { post } }));

let stop: ReturnType<ReturnType<typeof createSessionMonitor>> | undefined;
let coordinator: ReturnType<typeof createBrowserSessionCoordinator> | undefined;
const pending: ((state: BrowserSessionStatus["state"]) => void)[] = [];

beforeEach(() => {
  vi.useFakeTimers();
  localStorage.clear();
  post.mockReset();
});
afterEach(async () => {
  stop?.();
  for (const resolve of pending.splice(0)) resolve("ended");
  await vi.advanceTimersByTimeAsync(0);
  coordinator?.dispose();
  vi.useRealTimers();
});

it("resume_gate_never_adopts_pre_resume_logout_reconciliation_response", async () => {
  const events = new EventTarget();
  const visibility = Object.assign(new EventTarget(), {
    visibilityState: "visible" as DocumentVisibilityState,
  });
  coordinator = createBrowserSessionCoordinator({
    storage: localStorage,
    events,
  });
  let inFlight = 0;
  let maximumInFlight = 0;
  post.mockImplementation((_url, body, options) => {
    expect(options.timeout).toBe(1500);
    inFlight++;
    maximumInFlight = Math.max(maximumInFlight, inFlight);
    return new Promise((resolve) => {
      pending.push((state) => {
        inFlight--;
        resolve({ data: { session_id: body.session_id, state } });
      });
    });
  });
  const ended: string[] = [];
  stop = createSessionMonitor({
    coordinator,
    events,
    visibility,
    fetchStatus: fetchSessionStatus,
  })(
    () => ({ sessionId: "sid-a", accessToken: "access-a" }),
    (sid) => ended.push(sid),
  );
  await vi.advanceTimersByTimeAsync(0);
  pending[0]!("active");
  await vi.advanceTimersByTimeAsync(0);
  expect(stop.isChecking()).toBe(false);

  // Monitor ждёт poll, но logout reconciliation уже отправил status до resume.
  const reconciliation = fetchSessionStatus("sid-a", "access-a");
  await vi.advanceTimersByTimeAsync(0);
  expect(post).toHaveBeenCalledTimes(2);
  events.dispatchEvent(new Event("pageshow"));
  let admitted: boolean | undefined;
  const gate = stop.checkNow().then((value) => {
    admitted = value;
    return value;
  });
  await vi.advanceTimersByTimeAsync(0);
  expect(post).toHaveBeenCalledTimes(2);
  pending[1]!("active");
  await reconciliation;
  await vi.advanceTimersByTimeAsync(0);
  expect(admitted).toBeUndefined();
  expect(post).toHaveBeenCalledTimes(3);
  pending[2]!("ended");
  expect(await gate).toBe(false);
  expect(ended).toEqual(["sid-a"]);
  expect(maximumInFlight).toBe(1);
});
