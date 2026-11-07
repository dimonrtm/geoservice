import { editorTestContext } from "@/test/editorTestContext";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { IDBFactory } from "fake-indexeddb";
import { createBrowserSessionCoordinator } from "@/auth/browserSessionCoordinator";
import { createRecoveryStorage } from "./workspaceRecoveryStorage";
import { target, workspaceFixture } from "@/test/workspaceEditFixture";
import { useAuthStore } from "./auth";
import { useWorkspaceRecoveryStore } from "./workspaceRecovery";

const ports = vi.hoisted(() => ({
  coordinator: null as unknown,
  logout: vi.fn(),
  status: vi.fn(),
  saveFeatureGeometry: vi.fn(),
  readMap: vi.fn(),
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
  const store = editorTestContext();
  store.seed(workspaceFixture());
  store.workOrders.selectedWorkOrderId = store.editorSession.openedWorkOrderId =
    target.workOrderId;
  store.editorSession.openedEditVersionId = target.editVersionId;
  store.workOrders.items = [
    {
      id: target.workOrderId,
      code: "A",
      title: "A",
      description: null,
      status: "in_progress",
    },
  ];
  store.editVersionDraft.beginLocalEdit(target.featureId, 1);
  store.editVersionDraft.moveLocalVertex([65.1, 44.2]);
  return store;
}
async function sent(store: ReturnType<typeof editorTestContext>) {
  ports.saveFeatureGeometry.mockReturnValue(new Promise(() => {}));
  await store.editVersionCommands.saveLocalDraft();
  expect(ports.saveFeatureGeometry).toHaveBeenCalledOnce();
  return JSON.parse(JSON.stringify(store.editVersionCommands.pendingCommand));
}
async function leave(store: ReturnType<typeof editorTestContext>) {
  await store.editorNavigation.resolveNavigation(
    store.editorNavigation.requestNavigation({ kind: "logout" })!,
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
  const workspace = store.editor.snapshot;
  await leave(store);
  expect(useAuthStore().isAuthenticated).toBe(true);
  expect(store.editor.snapshot).toBe(workspace);
  expect(store.editVersionCommands.pendingCommand).toEqual(command);
  expect(
    useWorkspaceRecoveryStore().getRecord(
      store.editVersionCommands.recoveryKey!,
    )?.blocks,
  ).toEqual([]);
  expect(store.editorNavigation.workspaceInteractionLocked).toBe(false);
  expect(
    (await createRecoveryStorage().list("actor")).records[0]?.command,
  ).toEqual(command);
});

it("successful_logout_suspends_sent_intent", async () => {
  const store = setup();
  const command = await sent(store);
  const items = store.workOrders.items;
  const response = deferred<{ ok: boolean; session_id: string }>();
  ports.logout.mockReturnValue(response.promise);
  const leaving = leave(store);
  await vi.waitFor(() => expect(ports.logout).toHaveBeenCalledOnce());
  const pendingWorkspace = store.editorSession.activeWorkspace;
  const pendingCommand = store.editVersionCommands.pendingCommand;
  response.resolve({ ok: true, session_id: "sid-a" });
  await leaving;
  expect(pendingWorkspace).not.toBeNull();
  expect(pendingCommand).toEqual(command);
  expect(store.editor.snapshot).toBeNull();
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
  store.workOrders.items = items;
  store.seed(workspaceFixture());
  store.workOrders.selectedWorkOrderId = store.editorSession.openedWorkOrderId =
    target.workOrderId;
  store.editorSession.openedEditVersionId = target.editVersionId;
  await store.editVersionCommands.restorePendingSave();
  expect(store.editVersionCommands.recoveryRecord).toMatchObject({
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
  expect(store.editorSession.activeWorkspace).not.toBeNull();
  expect(store.editorNavigation.navigationError).toBeTruthy();
});

it("explicit_discard_stays_discarded_after_logout_error", async () => {
  const store = setup();
  await store.editorNavigation.resolveNavigation(
    store.editorNavigation.requestNavigation({ kind: "logout" })!,
    "discard",
  );
  expect(store.editVersionDraft.localDraft).toBeNull();
  expect(store.editorSession.activeWorkspace).not.toBeNull();
  expect(useAuthStore().isAuthenticated).toBe(true);
  expect(ports.saveFeatureGeometry).not.toHaveBeenCalled();
});

it("remote_browser_session_logout_does_not_autosave_dirty", async () => {
  const store = setup();
  useAuthStore().startBrowserSessionSync();
  store.editorNavigation.requestNavigation({ kind: "logout" });
  await coordinator.runAuthOperation("logout", null, async () => {
    coordinator.writeSessionMarker({
      version: 1,
      revision: 1,
      sessionId: "sid-a",
      state: "ended",
    });
  });
  expect(useAuthStore().isAuthenticated).toBe(false);
  expect(store.editor.snapshot).toBeNull();
  expect(store.editVersionDraft.localDraft).toBeNull();
  expect(store.editorNavigation.navigation).toBeNull();
  expect(ports.saveFeatureGeometry).not.toHaveBeenCalled();
  expect((await createRecoveryStorage().list("actor")).records).toEqual([]);
});

it("logout_temporarily_blocks_changes_and_failure_unlocks_the_same_draft", async () => {
  const store = setup();
  const draft = store.editVersionDraft.localDraft;
  const response = deferred<{ ok: boolean; session_id: string }>();
  ports.logout.mockReturnValue(response.promise);
  const leaving = store.editorNavigation.performNavigation({ kind: "logout" });
  const lockedDuringPreparation =
    store.editorNavigation.workspaceInteractionLocked;
  await vi.waitFor(() => expect(ports.logout).toHaveBeenCalledOnce());
  const movedDuringLogout = store.editVersionDraft.moveLocalVertex([
    65.2, 44.3,
  ]);
  const cancelledDuringLogout = store.editVersionDraft.cancelLocalEdit();
  await store.editVersionCommands.saveLocalDraft();
  expect(ports.saveFeatureGeometry).not.toHaveBeenCalled();
  response.resolve({ ok: false, session_id: "sid-a" });
  await leaving;
  expect(lockedDuringPreparation).toBe(true);
  expect(movedDuringLogout).toBe(false);
  expect(cancelledDuringLogout).toBe(false);
  expect(store.editVersionDraft.localDraft).toBe(draft);
  expect(store.editVersionDraft.moveLocalVertex([65.2, 44.3])).toBe(true);
});

it("late_confirmed_logout_does_not_clear_replacement_workspace", async () => {
  const store = setup();
  const response = deferred<{ ok: boolean; session_id: string }>();
  ports.logout.mockReturnValue(response.promise);
  const leaving = store.editorNavigation.performNavigation({ kind: "logout" });
  await vi.waitFor(() => expect(ports.logout).toHaveBeenCalledOnce());
  useAuthStore().setAuth("new", user, { sessionId: "sid-b" });
  store.seed(workspaceFixture());
  store.workOrders.selectedWorkOrderId = store.editorSession.openedWorkOrderId =
    target.workOrderId;
  store.editorSession.openedEditVersionId = target.editVersionId;
  const workspace = store.editor.snapshot;
  response.resolve({ ok: true, session_id: "sid-a" });
  await leaving;
  expect(useAuthStore().sessionId).toBe("sid-b");
  expect(store.editor.snapshot).toBe(workspace);
  expect(store.editorNavigation.workspaceInteractionLocked).toBe(false);
});

it("independent_stores_edit_the_same_work_order_without_a_new_lock", () => {
  const first = setup();
  const firstDraft = first.editVersionDraft.localDraft;
  const second = setup();
  expect(second.editVersionDraft.moveLocalVertex([65.2, 44.3])).toBe(true);
  expect(first.editVersionDraft.localDraft).toBe(firstDraft);
  expect(
    first.editVersionDraft.localDraft?.candidateGeometry.coordinates[1],
  ).toEqual([65.1, 44.2]);
  expect(
    second.editVersionDraft.localDraft?.candidateGeometry.coordinates[1],
  ).toEqual([65.2, 44.3]);
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
  const saving = store.editVersionCommands.saveLocalDraft();
  const response = deferred<{ ok: boolean; session_id: string }>();
  ports.logout.mockReturnValue(response.promise);
  const leaving = store.editorNavigation.performNavigation({ kind: "logout" });
  await vi.waitFor(() => expect(ports.logout).toHaveBeenCalledOnce());
  initialization.resolve();
  await saving;
  const callsDuringLogout = ports.saveFeatureGeometry.mock.calls.length;
  response.resolve({ ok: false, session_id: "sid-a" });
  await leaving;
  initialize.mockRestore();
  expect(callsDuringLogout).toBe(0);
  expect(store.editVersionDraft.localDraft).not.toBeNull();
  expect(store.editVersionCommands.phase).toBe("editing");
});

vi.mock("@/api/editVersions", () => ports);
vi.mock("@/api/editVersionMap", async () => {
  const { fixtureMap } = await import("@/test/editorReadFixtures");
  return {
    fetchEditVersionMap: (workOrderId: string, versionId: string) =>
      fixtureMap(ports.readMap, workOrderId, versionId),
  };
});
vi.mock("@/api/editVersionChangeSet", async () => ({
  fetchEditVersionChangeSet: (await import("@/test/editorReadFixtures"))
    .fixtureChangeSet,
}));
vi.mock("@/api/featureBaseline", async () => ({
  fetchFeatureBaseline: (await import("@/test/editorReadFixtures"))
    .fixtureBaseline,
}));
