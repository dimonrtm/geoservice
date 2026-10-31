import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  AuthCoordinationError,
  AuthOperationSupersededError,
  createBrowserSessionCoordinator,
  type CoordinatorPorts,
} from "./browserSessionCoordinator";

function deferred<T = void>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

function sharedBrowser() {
  let tail = Promise.resolve();
  const data = new Map<string, string>();
  const locks: NonNullable<CoordinatorPorts["locks"]> = {
    async request(_name, options, action) {
      const previous = tail;
      const released = deferred();
      tail = previous.then(() => released.promise);
      try {
        await Promise.race([
          previous,
          new Promise<never>((_resolve, reject) => {
            options.signal.addEventListener(
              "abort",
              () => reject(options.signal.reason),
              { once: true },
            );
          }),
        ]);
        options.signal.throwIfAborted();
        return await action();
      } finally {
        released.resolve();
      }
    },
  };
  const storage = {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => {
      data.set(key, value);
    },
    removeItem: (key: string) => {
      data.delete(key);
    },
  };
  return {
    data,
    locks,
    storage,
    client: () =>
      createBrowserSessionCoordinator({
        locks,
        storage,
        events: new EventTarget(),
      }),
  };
}

describe("browser session coordinator", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("serializes_cookie_mutations_across_clients", async () => {
    const browser = sharedBrowser();
    const a = browser.client();
    const b = browser.client();
    const release = deferred();
    const observed: string[] = [];
    const first = a.runAuthOperation("refresh", null, async () => {
      observed.push("first");
      await release.promise;
    });
    const second = b.runAuthOperation("refresh", null, async () => {
      observed.push("second");
    });
    await vi.advanceTimersByTimeAsync(0);
    expect(observed).toEqual(["first"]);
    release.resolve();
    await Promise.all([first, second]);
    expect(observed).toEqual(["first", "second"]);
  });

  it("queued_restore_is_skipped_after_logout", async () => {
    const browser = sharedBrowser();
    const a = browser.client();
    const b = browser.client();
    const release = deferred();
    const logout = a.runAuthOperation("logout", null, async () => {
      await release.promise;
      a.writeSessionMarker({
        version: 1,
        revision: 1,
        sessionId: "sid-a",
        state: "ended",
      });
    });
    let sent = false;
    const restore = b.runAuthOperation("refresh", null, async () => {
      sent = true;
    });
    const rejection = expect(restore).rejects.toBeInstanceOf(
      AuthOperationSupersededError,
    );
    release.resolve();
    await logout;
    await rejection;
    expect(sent).toBe(false);
  });

  it("lock_timeout_never_steals", async () => {
    const browser = sharedBrowser();
    const a = browser.client();
    const b = browser.client();
    const release = deferred();
    const first = a.runAuthOperation("login", null, () => release.promise);
    let sent = false;
    const queued = b.runAuthOperation("refresh", null, async () => {
      sent = true;
    });
    const outcome = queued.then(
      () => null,
      (error: unknown) => error,
    );
    await vi.advanceTimersByTimeAsync(30000);
    expect(await outcome).toBeInstanceOf(AuthCoordinationError);
    expect(sent).toBe(false);
    release.resolve();
    await first;
    await vi.advanceTimersByTimeAsync(0);
    expect(sent).toBe(false);
  });

  it("marker_contains_no_secrets", async () => {
    const browser = sharedBrowser();
    const a = browser.client();
    const input = {
      version: 1 as const,
      revision: 1,
      sessionId: "sid-a",
      state: "active" as const,
      accessToken: "secret",
      refreshToken: "cookie-secret",
    };
    await a.runAuthOperation("login", null, async () =>
      a.writeSessionMarker(input),
    );
    expect(browser.data.get("geoservice.auth.session.v1")).toBe(
      '{"version":1,"revision":1,"sessionId":"sid-a","state":"active"}',
    );
    expect(() => a.writeSessionMarker(input)).toThrow(AuthCoordinationError);
  });

  it.each([
    undefined,
    "garbage",
    '{"version":2,"revision":1,"sessionId":"s","state":"active"}',
    '{"version":1,"revision":-1,"sessionId":"s","state":"active"}',
  ])("rejects_corrupt_marker_%s", (value) => {
    const browser = sharedBrowser();
    if (value) browser.data.set("geoservice.auth.session.v1", value);
    expect(browser.client().readSessionMarker()).toBeNull();
  });

  it("requires_locks_and_available_storage_before_http", async () => {
    let sent = false;
    const action = async () => {
      sent = true;
    };
    const missing = createBrowserSessionCoordinator({
      events: new EventTarget(),
      storage: localStorage,
    });
    await expect(
      missing.runAuthOperation("refresh", null, action),
    ).rejects.toBeInstanceOf(AuthCoordinationError);
    const browser = sharedBrowser();
    const denied = createBrowserSessionCoordinator({
      locks: browser.locks,
      events: new EventTarget(),
      storage: {
        getItem() {
          throw new Error("denied");
        },
        setItem() {
          throw new Error("denied");
        },
        removeItem() {},
      },
    });
    await expect(
      denied.runAuthOperation("login", null, action),
    ).rejects.toBeInstanceOf(AuthCoordinationError);
    expect(sent).toBe(false);
  });

  it("startup_revision_change_exposes_current_sid_for_explicit_retry", async () => {
    const browser = sharedBrowser();
    const first = browser.client();
    const queued = browser.client();
    const publish = first.runAuthOperation("refresh", null, async () => {
      first.writeSessionMarker({
        version: 1,
        revision: 1,
        sessionId: "restored-sid",
        state: "active",
      });
    });
    const outcome = queued
      .runAuthOperation("refresh", null, async () => "unexpected")
      .catch((error: unknown) => error);
    await publish;
    const error = await outcome;
    expect(error).toBeInstanceOf(AuthOperationSupersededError);
    expect((error as AuthOperationSupersededError).currentMarker).toEqual({
      version: 1,
      revision: 1,
      sessionId: "restored-sid",
      state: "active",
    });
    expect(
      await queued.runAuthOperation("refresh", 1, async () => "fresh-access"),
    ).toBe("fresh-access");
  });

  it("write_denial_prevents_cookie_mutation", async () => {
    const browser = sharedBrowser();
    const coordinator = createBrowserSessionCoordinator({
      locks: browser.locks,
      storage: {
        getItem: () => null,
        setItem: () => {
          throw new Error("quota");
        },
        removeItem() {},
      },
      events: new EventTarget(),
    });
    let sent = false;
    await expect(
      coordinator.runAuthOperation("refresh", null, async () => {
        sent = true;
      }),
    ).rejects.toBeInstanceOf(AuthCoordinationError);
    expect(sent).toBe(false);
  });

  it("delayed_events_read_current_marker_and_disposal_removes_listeners", async () => {
    const browser = sharedBrowser();
    const events = new EventTarget();
    const channel = Object.assign(new EventTarget(), {
      postMessage() {},
      close: vi.fn(),
    });
    const coordinator = createBrowserSessionCoordinator({
      locks: browser.locks,
      storage: browser.storage,
      events,
      createChannel: () => channel,
    });
    const observed: string[] = [];
    coordinator.subscribe((marker) => {
      observed.push(`${marker.sessionId}:${marker.state}`);
    });
    browser.data.set(
      "geoservice.auth.session.v1",
      '{"version":1,"revision":4,"sessionId":"new-sid","state":"active"}',
    );
    channel.dispatchEvent(
      new MessageEvent("message", {
        data: { version: 1, revision: 2, sessionId: "old-sid", state: "ended" },
      }),
    );
    events.dispatchEvent(
      new StorageEvent("storage", {
        key: "geoservice.auth.session.v1",
        newValue:
          '{"version":1,"revision":2,"sessionId":"old-sid","state":"ended"}',
      }),
    );
    expect(observed).toEqual(["new-sid:active", "new-sid:active"]);
    coordinator.dispose();
    channel.dispatchEvent(new MessageEvent("message"));
    events.dispatchEvent(
      new StorageEvent("storage", { key: "geoservice.auth.session.v1" }),
    );
    expect(observed).toHaveLength(2);
    expect(channel.close).toHaveBeenCalledOnce();
  });

  it("ended_marker_cannot_be_reactivated_and_revision_cannot_move_back", async () => {
    const browser = sharedBrowser();
    const coordinator = browser.client();
    await coordinator.runAuthOperation("logout", null, async () => {
      coordinator.writeSessionMarker({
        version: 1,
        revision: 2,
        sessionId: "sid-a",
        state: "ended",
      });
      expect(() =>
        coordinator.writeSessionMarker({
          version: 1,
          revision: 1,
          sessionId: "sid-b",
          state: "active",
        }),
      ).toThrow(AuthCoordinationError);
      expect(() =>
        coordinator.writeSessionMarker({
          version: 1,
          revision: 3,
          sessionId: "sid-a",
          state: "active",
        }),
      ).toThrow(AuthCoordinationError);
    });
  });
});
