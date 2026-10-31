import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createSessionMonitor } from "./browserSessionMonitor";
import {
  createBrowserSessionCoordinator,
  type CoordinatorPorts,
} from "./browserSessionCoordinator";
import type {
  BrowserSessionCredentials,
  BrowserSessionStatus,
  SessionStatusOptions,
} from "./browserSessionTypes";

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

function setup(
  fetchStatus: (
    sid: string,
    token?: string,
    options?: SessionStatusOptions,
  ) => Promise<BrowserSessionStatus>,
  locks?: CoordinatorPorts["locks"],
) {
  const events = new EventTarget();
  const visibility = Object.assign(new EventTarget(), {
    visibilityState: "visible" as DocumentVisibilityState,
  });
  const coordinator = createBrowserSessionCoordinator({
    events,
    storage: localStorage,
    locks,
  });
  const start = createSessionMonitor({
    events,
    visibility,
    coordinator,
    fetchStatus,
  });
  let currentSessionCredentials: BrowserSessionCredentials | null = {
    sessionId: "sid-a",
    accessToken: "access-a",
  };
  const ended: string[] = [];
  const stop = start(
    () => currentSessionCredentials,
    (sid) => {
      ended.push(sid);
      currentSessionCredentials = null;
    },
  );
  return {
    events,
    visibility,
    stop,
    ended,
    coordinator,
    setCurrentSessionCredentials: (next: BrowserSessionCredentials | null) => {
      currentSessionCredentials = next;
    },
  };
}

describe("browser session monitor", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    localStorage.clear();
  });
  afterEach(() => vi.useRealTimers());

  it("missing_broadcast_uses_status", async () => {
    const monitor = setup(async (session_id) => ({
      session_id,
      state: "ended",
    }));
    await vi.advanceTimersByTimeAsync(0);
    expect(monitor.ended).toEqual(["sid-a"]);
    monitor.stop();
  });

  it("stale_status_cannot_end_new_session", async () => {
    const pending = deferred<BrowserSessionStatus>();
    const monitor = setup(() => pending.promise);
    await vi.advanceTimersByTimeAsync(0);
    monitor.setCurrentSessionCredentials({
      sessionId: "sid-b",
      accessToken: "access-b",
    });
    pending.resolve({ session_id: "sid-a", state: "ended" });
    await vi.advanceTimersByTimeAsync(0);
    expect(monitor.ended).toEqual([]);
    monitor.stop();
  });

  it("old_active_response_does_not_break_five_second_logout", async () => {
    let calls = 0;
    const monitor = setup(
      (session_id) =>
        new Promise((resolve) => {
          const state = calls++ === 0 ? "active" : "ended";
          setTimeout(() => resolve({ session_id, state }), 1500);
        }),
    );
    await vi.advanceTimersByTimeAsync(3999);
    expect(monitor.ended).toEqual([]);
    await vi.advanceTimersByTimeAsync(1);
    expect(monitor.ended).toEqual(["sid-a"]);
    await vi.advanceTimersByTimeAsync(10000);
    expect(calls).toBe(2);
    monitor.stop();
  });

  it("hidden_running_tab_detects_logout_without_marker_events_within_five_seconds", async () => {
    let calls = 0;
    const monitor = setup(
      (session_id) =>
        new Promise((resolve) => {
          const state = calls++ === 0 ? "active" : "ended";
          setTimeout(() => resolve({ session_id, state }), 1500);
        }),
    );
    monitor.visibility.visibilityState = "hidden";
    // Никаких storage/channel/visibility/pageshow событий: вкладка продолжает
    // выполнять код, а старый active приходит после server-side logout.
    await vi.advanceTimersByTimeAsync(3999);
    expect(monitor.ended).toEqual([]);
    await vi.advanceTimersByTimeAsync(1);
    expect(monitor.ended).toEqual(["sid-a"]);
    await vi.advanceTimersByTimeAsync(10000);
    expect(calls).toBe(2);
    monitor.stop();
  });

  it("single_inflight_and_dispose_suppresses_callbacks", async () => {
    const pending = deferred<BrowserSessionStatus>();
    let calls = 0;
    const monitor = setup(() => {
      calls++;
      return pending.promise;
    });
    monitor.events.dispatchEvent(new Event("pageshow"));
    monitor.visibility.dispatchEvent(new Event("visibilitychange"));
    await vi.advanceTimersByTimeAsync(5000);
    expect(calls).toBe(1);
    expect(monitor.stop.isChecking()).toBe(true);
    monitor.stop();
    pending.resolve({ session_id: "sid-a", state: "ended" });
    await vi.advanceTimersByTimeAsync(10000);
    monitor.events.dispatchEvent(new Event("pageshow"));
    expect(monitor.ended).toEqual([]);
    expect(calls).toBe(1);
  });

  it("unavailable_status_does_not_end_and_resume_checks_immediately", async () => {
    let calls = 0;
    const monitor = setup(async () => {
      calls++;
      throw new Error("offline");
    });
    await vi.advanceTimersByTimeAsync(0);
    expect(monitor.ended).toEqual([]);
    monitor.events.dispatchEvent(new Event("pageshow"));
    await vi.advanceTimersByTimeAsync(0);
    expect(calls).toBe(2);
    monitor.stop();
  });

  it("known_ended_is_not_undone_by_old_active_response", async () => {
    const pending = deferred<BrowserSessionStatus>();
    const monitor = setup(() => pending.promise);
    await vi.advanceTimersByTimeAsync(0);
    localStorage.setItem(
      "geoservice.auth.session.v1",
      '{"version":1,"revision":2,"sessionId":"sid-a","state":"ended"}',
    );
    monitor.events.dispatchEvent(
      new StorageEvent("storage", { key: "geoservice.auth.session.v1" }),
    );
    expect(monitor.ended).toEqual(["sid-a"]);
    pending.resolve({ session_id: "sid-a", state: "active" });
    await vi.advanceTimersByTimeAsync(5000);
    expect(monitor.ended).toEqual(["sid-a"]);
    monitor.stop();
  });

  it("ended_clears_ui_before_busy_lock_and_disposal_prevents_late_publication", async () => {
    const release = deferred<void>();
    const locks: CoordinatorPorts["locks"] = {
      async request(_name, _options, action) {
        await release.promise;
        return action();
      },
    };
    const monitor = setup(
      async (session_id) => ({ session_id, state: "ended" }),
      locks,
    );
    await vi.advanceTimersByTimeAsync(0);
    expect(monitor.ended).toEqual(["sid-a"]);
    expect(localStorage.getItem("geoservice.auth.session.v1")).toBeNull();
    monitor.stop();
    release.resolve();
    await vi.advanceTimersByTimeAsync(0);
    expect(localStorage.getItem("geoservice.auth.session.v1")).toBeNull();
  });

  it("late_ended_publication_preserves_replacement_session", async () => {
    const release = deferred<void>();
    const locks: CoordinatorPorts["locks"] = {
      async request(_name, _options, action) {
        await release.promise;
        return action();
      },
    };
    const monitor = setup(
      async (session_id) => ({ session_id, state: "ended" }),
      locks,
    );
    await vi.advanceTimersByTimeAsync(0);
    localStorage.setItem(
      "geoservice.auth.session.v1",
      '{"version":1,"revision":3,"sessionId":"sid-b","state":"active"}',
    );
    release.resolve();
    await vi.advanceTimersByTimeAsync(0);
    expect(monitor.coordinator.readSessionMarker()).toEqual({
      version: 1,
      revision: 3,
      sessionId: "sid-b",
      state: "active",
    });
    monitor.stop();
  });

  it("resume_during_old_request_requires_a_fresh_status_before_actions", async () => {
    const pending = deferred<BrowserSessionStatus>();
    let calls = 0;
    const monitor = setup((session_id) => {
      calls++;
      return calls === 1
        ? pending.promise
        : Promise.resolve({ session_id, state: "active" });
    });
    await vi.advanceTimersByTimeAsync(0);
    const oldGate = monitor.stop.checkNow();
    monitor.events.dispatchEvent(new Event("pageshow"));
    pending.resolve({ session_id: "sid-a", state: "active" });
    expect(await oldGate).toBe(false);
    await vi.advanceTimersByTimeAsync(0);
    expect(calls).toBe(2);
    expect(await monitor.stop.checkNow()).toBe(true);
    monitor.stop();
  });

  it("idle_monitor_resume_requires_fresh_transport_request", async () => {
    const observed: (SessionStatusOptions | undefined)[] = [];
    const monitor = setup(async (session_id, _token, options) => {
      observed.push(options);
      return { session_id, state: "active" };
    });
    await vi.advanceTimersByTimeAsync(0);
    expect(monitor.stop.isChecking()).toBe(false);
    monitor.events.dispatchEvent(new Event("pageshow"));
    await vi.advanceTimersByTimeAsync(0);
    expect(observed).toEqual([undefined, { requireFreshRequest: true }]);
    monitor.stop();
  });

  it("failed_resume_check_keeps_freshness_requirement_for_next_gate", async () => {
    const observed: (SessionStatusOptions | undefined)[] = [];
    const monitor = setup(async (session_id, _token, options) => {
      observed.push(options);
      if (observed.length === 2) throw new Error("offline");
      return { session_id, state: "active" };
    });
    await vi.advanceTimersByTimeAsync(0);
    monitor.events.dispatchEvent(new Event("pageshow"));
    await vi.advanceTimersByTimeAsync(0);
    expect(await monitor.stop.checkNow()).toBe(true);
    expect(observed).toEqual([
      undefined,
      { requireFreshRequest: true },
      { requireFreshRequest: true },
    ]);
    monitor.stop();
  });
});
