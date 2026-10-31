import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { IDBFactory } from "fake-indexeddb";
import { createBrowserSessionCoordinator } from "@/auth/browserSessionCoordinator";
import { createRecoveryStorage } from "./workspaceRecoveryStorage";
import { target, workspaceFixture } from "@/test/workspaceEditFixture";
import { useAuthStore } from "./auth";
import { useWorkOrdersStore } from "./workOrders";
import { useWorkspaceRecoveryStore } from "./workspaceRecovery";

const ports = vi.hoisted(() => ({
  coordinator: null as unknown,
  logout: vi.fn(),
  status: vi.fn(),
  saveFeatureGeometry: vi.fn(),
  fetchWorkspace: vi.fn(),
}));
vi.mock("@/api/workOrders", () => ports);
vi.mock("@/api/auth", () => ({
  logoutSession: ports.logout,
  fetchSessionStatus: ports.status,
}));
vi.mock("@/auth/browserSessionCoordinator", async (original) => ({
  ...(await original<typeof import("@/auth/browserSessionCoordinator")>()),
  getBrowserSessionCoordinator: () => ports.coordinator,
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => (resolve = done));
  return { promise, resolve };
}
const user = { id: "actor", email: "a@local", role: "editor" as const };
let coordinator: ReturnType<typeof createBrowserSessionCoordinator>;
const contexts: ReturnType<typeof createPinia>[] = [];
function setup() {
  const pinia = createPinia();
  contexts.push(pinia);
  setActivePinia(pinia);
  useAuthStore().setAuth("token", user, { sessionId: "sid-a" });
  const store = useWorkOrdersStore();
  store.workspace = workspaceFixture();
  store.selectedWorkOrderId = store.openedWorkOrderId = target.workOrderId;
  store.openedEditVersionId = target.editVersionId;
  store.items = [
    {
      id: target.workOrderId,
      code: "A",
      title: "A",
      description: null,
      status: "in_progress",
    },
  ];
  store.beginLocalEdit(target.featureId, 1);
  store.moveLocalVertex([65.1, 44.2]);
  return store;
}
async function sent(store: ReturnType<typeof useWorkOrdersStore>) {
  ports.saveFeatureGeometry.mockReturnValue(new Promise(() => {}));
  await store.saveLocalDraft();
  expect(ports.saveFeatureGeometry).toHaveBeenCalledOnce();
  return JSON.parse(JSON.stringify(store.pendingCommand));
}
async function leave(store: ReturnType<typeof useWorkOrdersStore>) {
  await store.resolveNavigation(
    store.requestNavigation({ kind: "logout" })!,
    "leave",
  );
}
beforeEach(() => {
  vi.resetAllMocks();
  sessionStorage.clear();
  localStorage.clear();
  Object.defineProperty(globalThis, "indexedDB", {
    value: new IDBFactory(),
    configurable: true,
  });
  coordinator = createBrowserSessionCoordinator({
    storage: localStorage,
    events: new EventTarget(),
    locks: { request: async (_name, _options, action) => action() },
  });
  ports.coordinator = coordinator;
  ports.logout.mockRejectedValue({
    isAxiosError: true,
    response: { status: 503 },
  });
  ports.status.mockImplementation(async (sid: string) => ({
    session_id: sid,
    state: "active",
  }));
});
afterEach(() => {
  for (const pinia of contexts.splice(0)) {
    setActivePinia(pinia);
    useAuthStore().stopBrowserSessionSync();
    useWorkspaceRecoveryStore().stopRuntime();
  }
  coordinator.dispose();
});

it("failed_logout_preserves_workspace_and_pending_identity", async () => {
  const store = setup();
  const command = await sent(store);
  const workspace = store.workspace;
  await leave(store);
  expect(useAuthStore().isAuthenticated).toBe(true);
  expect(store.workspace).toBe(workspace);
  expect(store.pendingCommand).toEqual(command);
  expect(
    useWorkspaceRecoveryStore().getRecord(store.recoveryKey!)?.blocks,
  ).toEqual([]);
  expect(store.workspaceInteractionLocked).toBe(false);
  expect(
    (await createRecoveryStorage().list("actor")).records[0]?.command,
  ).toEqual(command);
});

it("successful_logout_suspends_sent_intent", async () => {
  const store = setup();
  const command = await sent(store);
  const items = store.items;
  const response = deferred<{ ok: boolean; session_id: string }>();
  ports.logout.mockReturnValue(response.promise);
  const leaving = leave(store);
  await vi.waitFor(() => expect(ports.logout).toHaveBeenCalledOnce());
  const pendingWorkspace = store.activeWorkspace;
  const pendingCommand = store.pendingCommand;
  response.resolve({ ok: true, session_id: "sid-a" });
  await leaving;
  expect(pendingWorkspace).not.toBeNull();
  expect(pendingCommand).toEqual(command);
  expect(store.workspace).toBeNull();
  expect(useAuthStore().isAuthenticated).toBe(false);
  await vi.waitFor(async () => {
    expect(
      (await createRecoveryStorage().list("actor")).records[0]?.blocks,
    ).toContain("access");
  });
  const persisted = (await createRecoveryStorage().list("actor")).records[0]!;
  expect(persisted.command).toEqual(command);
  expect(persisted.blocks).toContain("access");
  expect(persisted.requiresAccessConfirmation).toBe(true);
  useAuthStore().setAuth("new", user, { sessionId: "sid-b" });
  store.items = items;
  store.workspace = workspaceFixture();
  store.selectedWorkOrderId = store.openedWorkOrderId = target.workOrderId;
  store.openedEditVersionId = target.editVersionId;
  await store.restorePendingSave();
  expect(store.recoveryRecord).toMatchObject({
    state: "blocked",
    reason: "access",
  });
  expect(ports.saveFeatureGeometry).toHaveBeenCalledOnce();
});

it("recovery_storage_error_prevents_managed_logout", async () => {
  const store = setup();
  await sent(store);
  Object.defineProperty(globalThis, "indexedDB", {
    value: undefined,
    configurable: true,
  });
  await leave(store);
  expect(ports.logout).not.toHaveBeenCalled();
  expect(store.activeWorkspace).not.toBeNull();
  expect(store.navigationError).toBeTruthy();
});

it("explicit_discard_stays_discarded_after_logout_error", async () => {
  const store = setup();
  await store.resolveNavigation(
    store.requestNavigation({ kind: "logout" })!,
    "discard",
  );
  expect(store.localDraft).toBeNull();
  expect(store.activeWorkspace).not.toBeNull();
  expect(useAuthStore().isAuthenticated).toBe(true);
  expect(ports.saveFeatureGeometry).not.toHaveBeenCalled();
});

it("remote_browser_session_logout_does_not_autosave_dirty", async () => {
  const store = setup();
  useAuthStore().startBrowserSessionSync();
  store.requestNavigation({ kind: "logout" });
  await coordinator.runAuthOperation("logout", null, async () => {
    coordinator.writeSessionMarker({
      version: 1,
      revision: 1,
      sessionId: "sid-a",
      state: "ended",
    });
  });
  expect(useAuthStore().isAuthenticated).toBe(false);
  expect(store.workspace).toBeNull();
  expect(store.localDraft).toBeNull();
  expect(store.navigation).toBeNull();
  expect(ports.saveFeatureGeometry).not.toHaveBeenCalled();
  expect((await createRecoveryStorage().list("actor")).records).toEqual([]);
});

it("logout_temporarily_blocks_changes_and_failure_unlocks_the_same_draft", async () => {
  const store = setup();
  const draft = store.localDraft;
  const response = deferred<{ ok: boolean; session_id: string }>();
  ports.logout.mockReturnValue(response.promise);
  const leaving = store.performNavigation({ kind: "logout" });
  const lockedDuringPreparation = store.workspaceInteractionLocked;
  await vi.waitFor(() => expect(ports.logout).toHaveBeenCalledOnce());
  const movedDuringLogout = store.moveLocalVertex([65.2, 44.3]);
  const cancelledDuringLogout = store.cancelLocalEdit();
  await store.saveLocalDraft();
  expect(ports.saveFeatureGeometry).not.toHaveBeenCalled();
  response.resolve({ ok: false, session_id: "sid-a" });
  await leaving;
  expect(lockedDuringPreparation).toBe(true);
  expect(movedDuringLogout).toBe(false);
  expect(cancelledDuringLogout).toBe(false);
  expect(store.localDraft).toBe(draft);
  expect(store.moveLocalVertex([65.2, 44.3])).toBe(true);
});

it("late_confirmed_logout_does_not_clear_replacement_workspace", async () => {
  const store = setup();
  const response = deferred<{ ok: boolean; session_id: string }>();
  ports.logout.mockReturnValue(response.promise);
  const leaving = store.performNavigation({ kind: "logout" });
  await vi.waitFor(() => expect(ports.logout).toHaveBeenCalledOnce());
  useAuthStore().setAuth("new", user, { sessionId: "sid-b" });
  store.workspace = workspaceFixture();
  store.selectedWorkOrderId = store.openedWorkOrderId = target.workOrderId;
  store.openedEditVersionId = target.editVersionId;
  const workspace = store.workspace;
  response.resolve({ ok: true, session_id: "sid-a" });
  await leaving;
  expect(useAuthStore().sessionId).toBe("sid-b");
  expect(store.workspace).toBe(workspace);
  expect(store.workspaceInteractionLocked).toBe(false);
});

it("independent_stores_edit_the_same_work_order_without_a_new_lock", () => {
  const first = setup();
  const firstDraft = first.localDraft;
  const second = setup();
  expect(second.moveLocalVertex([65.2, 44.3])).toBe(true);
  expect(first.localDraft).toBe(firstDraft);
  expect(first.localDraft?.candidateGeometry.coordinates[1]).toEqual([
    65.1, 44.2,
  ]);
  expect(second.localDraft?.candidateGeometry.coordinates[1]).toEqual([
    65.2, 44.3,
  ]);
});

it("save_waiting_for_recovery_initialization_cannot_start_during_logout", async () => {
  const store = setup();
  const recovery = useWorkspaceRecoveryStore();
  const initialization = deferred<void>();
  const original = recovery.initializeActor.bind(recovery);
  const initialize = vi
    .spyOn(recovery, "initializeActor")
    .mockImplementation(async (actorId) => {
      await original(actorId);
      await initialization.promise;
    });
  const saving = store.saveLocalDraft();
  const response = deferred<{ ok: boolean; session_id: string }>();
  ports.logout.mockReturnValue(response.promise);
  const leaving = store.performNavigation({ kind: "logout" });
  await vi.waitFor(() => expect(ports.logout).toHaveBeenCalledOnce());
  initialization.resolve();
  await saving;
  const callsDuringLogout = ports.saveFeatureGeometry.mock.calls.length;
  response.resolve({ ok: false, session_id: "sid-a" });
  await leaving;
  initialize.mockRestore();
  expect(callsDuringLogout).toBe(0);
  expect(store.localDraft).not.toBeNull();
  expect(store.phase).toBe("editing");
});
