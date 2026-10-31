import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { createPinia } from "pinia";
import { createApp } from "vue";
import { flushPromises } from "@vue/test-utils";
import {
  AuthCoordinationError,
  createBrowserSessionCoordinator,
} from "@/auth/browserSessionCoordinator";
import { useAuthStore } from "./auth";

const ports = vi.hoisted(() => ({
  coordinator: null as unknown,
  login: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
  status: vi.fn(),
  reset: vi.fn(),
  suspendWorkspaceRecoveryForAccessLoss: vi.fn(),
  hideActor: vi.fn(),
  suspendActor: vi.fn(),
}));
vi.mock("@/auth/browserSessionCoordinator", async (original) => ({
  ...(await original<typeof import("@/auth/browserSessionCoordinator")>()),
  getBrowserSessionCoordinator: () => ports.coordinator,
}));
vi.mock("@/api/auth", () => ({
  login: ports.login,
  refreshSession: ports.refresh,
  logoutSession: ports.logout,
  fetchSessionStatus: ports.status,
}));
vi.mock("@/stores/workOrders", () => ({ useWorkOrdersStore: () => ports }));
vi.mock("@/stores/workspaceRecovery", () => ({
  useWorkspaceRecoveryStore: () => ports,
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
const user = {
  id: "actor",
  email: "actor@example.local",
  role: "editor" as const,
};
const payload = (sid = "sid-a") => ({
  access_token: `access-${sid}`,
  token_type: "bearer",
  session_id: sid,
  user,
});
let coordinator: ReturnType<typeof createBrowserSessionCoordinator>;
const stores: ReturnType<typeof useAuthStore>[] = [];
it("shares_session_runtime_across_devtools_action_proxies", async () => {
  vi.stubEnv("NODE_ENV", "development");
  const pinia = createPinia();
  createApp({}).use(pinia);
  const auth = useAuthStore(pinia);
  stores.push(auth);
  auth.setAuth("access-sid-a", user, { sessionId: "sid-a" });
  ports.status.mockResolvedValue({ session_id: "sid-a", state: "active" });

  auth.startBrowserSessionSync();

  expect(await auth.ensureSessionReady()).toBe(true);
  auth.stopBrowserSessionSync();
});

function store(sid?: string) {
  const auth = useAuthStore(createPinia());
  stores.push(auth);
  if (sid) auth.setAuth(`access-${sid}`, user, { sessionId: sid });
  return auth;
}
beforeEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
  let tail = Promise.resolve();
  coordinator = createBrowserSessionCoordinator({
    storage: localStorage,
    events: new EventTarget(),
    locks: {
      async request(_name, options, action) {
        const prior = tail;
        const release = deferred<void>();
        tail = prior.then(() => release.promise);
        await prior;
        try {
          options.signal.throwIfAborted();
          return await action();
        } finally {
          release.resolve();
        }
      },
    },
  });
  ports.coordinator = coordinator;
  ports.refresh.mockImplementation(async (sid?: string) => payload(sid));
  ports.login.mockResolvedValue(payload("sid-b"));
  ports.logout.mockResolvedValue({ ok: true, session_id: "sid-a" });
  ports.status.mockImplementation(async (sid: string) => ({
    session_id: sid,
    state: "active",
  }));
});
afterEach(() => {
  vi.unstubAllEnvs();
  for (const auth of stores.splice(0)) auth.stopBrowserSessionSync?.();
  coordinator.dispose();
});

it("same_user_new_sid_invalidates_old_requests", () => {
  const auth = store("sid-a");
  const epoch = auth.sessionEpoch;
  ports.reset.mockClear();
  auth.setAuth("new", user, { sessionId: "sid-b" });
  auth.handleUnauthorizedResponse({ response: { status: 401 } }, epoch);
  expect(auth.sessionEpoch).toBeGreaterThan(epoch);
  expect(auth.sessionId).toBe("sid-b");
  expect(auth.user).toEqual(user);
  expect(ports.reset).toHaveBeenCalledOnce();
  expect(ports.suspendWorkspaceRecoveryForAccessLoss).toHaveBeenCalledWith(
    "actor",
  );
});
it("same_sid_refresh_preserves_workspace", async () => {
  const auth = store("sid-a");
  const epoch = auth.sessionEpoch;
  ports.reset.mockClear();
  await auth.restoreSession();
  expect(auth.sessionEpoch).toBe(epoch);
  expect(ports.reset).not.toHaveBeenCalled();
});
it("two_restores_do_not_clear_each_other", async () => {
  const first = store();
  const second = store();
  await Promise.all([first.restoreSession(), second.restoreSession()]);
  expect(first.isAuthenticated).toBe(true);
  expect(second.isAuthenticated).toBe(true);
  expect(second.sessionId).toBe("sid-a");
  expect(ports.refresh.mock.calls).toEqual([[undefined], ["sid-a"]]);
  expect(coordinator.readSessionMarker()?.revision).toBe(1);
});
it("restore_rechecks_marker_after_lock_before_installing_actor", async () => {
  const auth = store();
  let replacement: Promise<void> | undefined;
  const unsubscribe = coordinator.subscribe((marker) => {
    if (marker.sessionId !== "sid-a" || marker.state !== "active") return;
    replacement = coordinator.runAuthOperation(
      "login",
      marker.revision,
      async () => {
        coordinator.writeSessionMarker({
          version: 1,
          revision: 2,
          sessionId: "sid-b",
          state: "active",
        });
      },
    );
  });
  await auth.restoreSession();
  await replacement;
  unsubscribe();
  expect(auth.sessionId).toBe("sid-b");
});
it("failed_logout_keeps_auth", async () => {
  const auth = store("sid-a");
  ports.logout.mockRejectedValue({
    isAxiosError: true,
    response: { status: 503 },
  });
  expect(await auth.logout()).toBe(false);
  expect(auth.isAuthenticated).toBe(true);
  expect(auth.logoutError?.summary).toBe(
    "Не удалось выйти, попробуйте ещё раз",
  );
  expect(coordinator.readSessionMarker()?.state).not.toBe("ended");
});
it("unknown_logout_reconciles_exact_sid_without_retrying_logout", async () => {
  const auth = store("sid-a");
  ports.logout.mockRejectedValue({ isAxiosError: true, code: "ECONNABORTED" });
  ports.status.mockRejectedValue(new Error("offline"));
  expect(await auth.logout()).toBe(false);
  expect(auth.isAuthenticated).toBe(true);
  expect(auth.logoutError?.summary).toBe("Не удалось подтвердить выход");
  expect(ports.status).toHaveBeenCalledWith("sid-a", "access-sid-a");
  expect(ports.logout).toHaveBeenCalledOnce();
});
it("coordination_failure_before_logout_dispatch_is_known_undelivered", async () => {
  coordinator.dispose();
  coordinator = createBrowserSessionCoordinator({
    storage: localStorage,
    events: new EventTarget(),
  });
  ports.coordinator = coordinator;
  const auth = store("sid-a");

  expect(await auth.logout()).toBe(false);

  expect(auth.isAuthenticated).toBe(true);
  expect(auth.logoutError?.summary).toBe(
    "Не удалось выйти, попробуйте ещё раз",
  );
  expect(ports.logout).not.toHaveBeenCalled();
  expect(ports.status).not.toHaveBeenCalled();
  expect(coordinator.readSessionMarker()).toBeNull();
});
it("coordination_error_after_logout_dispatch_still_reconciles_uncertain_outcome", async () => {
  const auth = store("sid-a");
  ports.logout.mockRejectedValue(new AuthCoordinationError("transport failed"));

  expect(await auth.logout()).toBe(false);

  expect(auth.isAuthenticated).toBe(true);
  expect(auth.logoutError?.summary).toBe("Не удалось подтвердить выход");
  expect(ports.status).toHaveBeenCalledWith("sid-a", "access-sid-a");
  expect(ports.logout).toHaveBeenCalledOnce();
});
it("late_old_logout_never_clears_new_login", async () => {
  const auth = store("sid-a");
  const pending = deferred<unknown>();
  ports.logout.mockReturnValue(pending.promise);
  const logout = auth.logout();
  await flushPromises();
  auth.setAuth("new", user, { sessionId: "sid-b" });
  pending.resolve({ ok: true, session_id: "sid-a" });
  expect(await logout).toBe(true);
  expect(auth.sessionId).toBe("sid-b");
  expect(auth.token).toBe("new");
});
it("expired_access_401_is_not_global_logout", () => {
  const auth = store("sid-a");
  auth.handleUnauthorizedResponse({
    isAxiosError: true,
    response: { status: 401 },
  });
  expect(coordinator.readSessionMarker()?.state).not.toBe("ended");
  expect(ports.logout).not.toHaveBeenCalled();
});
it("status_of_old_sid_cannot_mutate_current_actor", async () => {
  const auth = store("sid-a");
  const old = deferred<{ session_id: string; state: string }>();
  ports.status.mockReturnValueOnce(old.promise);
  auth.startBrowserSessionSync();
  await flushPromises();
  auth.setAuth("new", user, { sessionId: "sid-b" });
  old.resolve({ session_id: "sid-a", state: "ended" });
  await flushPromises();
  expect(auth.sessionId).toBe("sid-b");
  expect(auth.isAuthenticated).toBe(true);
});
it("confirmed_ended_clears_ui_without_waiting_for_auth_lock", async () => {
  const auth = store("sid-a");
  const release = deferred<void>();
  const lock = coordinator.runAuthOperation(
    "refresh",
    null,
    () => release.promise,
  );
  await flushPromises();
  ports.status.mockResolvedValue({ session_id: "sid-a", state: "ended" });
  auth.startBrowserSessionSync();
  await flushPromises();
  expect(auth.isAuthenticated).toBe(false);
  release.resolve();
  await lock;
});
it("shared_replacement_restores_new_sid_for_same_actor", async () => {
  const auth = store("sid-a");
  auth.startBrowserSessionSync();
  await flushPromises();
  await coordinator.runAuthOperation("login", null, async () => {
    coordinator.writeSessionMarker({
      version: 1,
      revision: 1,
      sessionId: "sid-b",
      state: "active",
    });
  });
  await flushPromises();
  expect(auth.sessionId).toBe("sid-b");
  expect(auth.token).toBe("access-sid-b");
});
it("startup_ended_marker_does_not_refresh_revoked_cookie", async () => {
  await coordinator.runAuthOperation("logout", null, async () => {
    coordinator.writeSessionMarker({
      version: 1,
      revision: 1,
      sessionId: "sid-a",
      state: "ended",
    });
  });
  const auth = store();
  await auth.restoreSession();
  expect(auth.isAuthenticated).toBe(false);
  expect(ports.refresh).not.toHaveBeenCalled();
});
it("resume_waits_for_fresh_status_before_allowing_actions", async () => {
  const auth = store("sid-a");
  const old = deferred<{ session_id: string; state: string }>();
  const fresh = deferred<{ session_id: string; state: string }>();
  ports.status
    .mockReturnValueOnce(old.promise)
    .mockReturnValueOnce(fresh.promise);
  auth.startBrowserSessionSync();
  await flushPromises();
  window.dispatchEvent(new Event("pageshow"));
  let admitted = false;
  const ready = auth.ensureSessionReady().then((value) => {
    admitted = value;
    return value;
  });
  old.resolve({ session_id: "sid-a", state: "active" });
  await flushPromises();
  expect(admitted).toBe(false);
  fresh.resolve({ session_id: "sid-a", state: "active" });
  expect(await ready).toBe(true);
});
