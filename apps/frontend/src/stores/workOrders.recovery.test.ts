import { useWorkspaceRecoveryStore } from "./workspaceRecovery";
import {
  settle,
  until,
  readPersisted as readRecoveryRecord,
  stopRecovery,
} from "@/test/recoveryIntegration";
import { IDBObjectStore } from "fake-indexeddb";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import {
  candidate,
  commandId,
  target,
  successFixture,
  workspaceFixture,
} from "@/test/workspaceEditFixture";
const api = vi.hoisted(() => ({
  fetchAssignedWorkOrders: vi.fn(),
  fetchWorkspace: vi.fn(),
  openEditVersion: vi.fn(),
  saveFeatureGeometry: vi.fn(),
}));
vi.mock("@/api/workOrders", () => api);
import { useWorkOrdersStore } from "./workOrders";
import { useAuthStore } from "./auth";
import { writeRecoveryRecord } from "./workspaceRecoveryStorage";
const command = {
  actorId: "actor",
  target,
  request: { commandId, draftVersionToken: "revision-a", geometry: candidate },
};
function setup(edit = false) {
  const auth = useAuthStore();
  auth.token = "test";
  auth.user = { id: "actor", email: "editor@example.local", role: "editor" };
  const store = useWorkOrdersStore();
  store.workspace = workspaceFixture();
  store.openedWorkOrderId = store.selectedWorkOrderId = target.workOrderId;
  store.openedEditVersionId = target.editVersionId;
  store.items = [
    {
      id: target.workOrderId,
      code: "WO",
      title: "Работа",
      description: null,
      status: "in_progress",
    },
  ];
  if (edit) {
    store.beginLocalEdit(target.featureId, 1);
    store.moveLocalVertex([65.1, 44.2]);
  }
  return store;
}
function deferred<T>() {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}
describe("Save recovery", () => {
  it("restored success has no source evidence and never resends PUT", async () => {
    writeRecoveryRecord({
      schemaVersion: 1,
      command,
      state: "succeeded",
      result: successFixture(),
    });
    const store = setup();
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.restorePendingSave();
    await settle(store);
    expect(store.didSaveChangeGeometry).toBeNull();
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.workspace?.workOrder.editVersion.draftVersionToken).toBe(
      "revision-b",
    );
  });
  it("late success cannot classify or replace another context", async () => {
    const store = setup(true);
    const response = deferred<ReturnType<typeof successFixture>>();
    api.saveFeatureGeometry.mockReturnValue(response.promise);
    const saving = store.saveLocalDraft();
    await vi.waitFor(() => expect(store.pendingCommand).not.toBeNull());
    const id = store.pendingCommand!.request.commandId;
    store.clearOpenedWorkspace({ force: true });
    response.resolve(successFixture(id));
    await saving;
    expect(store.didSaveChangeGeometry).toBeNull();
    expect(store.submittedSourceGeometry).toBeNull();
    expect(store.workspace).toBeNull();
    expect(api.fetchWorkspace).not.toHaveBeenCalled();
  });
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetAllMocks();
    setActivePinia(createPinia());
    sessionStorage.clear();
  });
  afterEach(() => {
    stopRecovery();
    vi.useRealTimers();
  });
  it("initial has five additional attempts, manual starts a new five-attempt series", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const store = setup(true);
    api.saveFeatureGeometry.mockRejectedValue({
      isAxiosError: true,
      code: "ETIMEDOUT",
    });
    const save = store.saveLocalDraft();
    await vi.advanceTimersByTimeAsync(0);
    await until(() => api.saveFeatureGeometry.mock.calls.length === 2);
    for (const [ms, count] of [
      [2000, 3],
      [5000, 4],
      [10000, 5],
      [20000, 6],
    ]) {
      await vi.advanceTimersByTimeAsync(ms! - 1);
      expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(count! - 1);
      await vi.advanceTimersByTimeAsync(1);
      expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(count!);
    }
    await save;
    expect(store.phase).toBe("unknown");
    for (const args of api.saveFeatureGeometry.mock.calls)
      expect(args[1]).toEqual(api.saveFeatureGeometry.mock.calls[0]?.[1]);
    const retry = store.retryPendingSave();
    const duplicate = store.retryPendingSave();
    await vi.runAllTimersAsync();
    await Promise.all([retry, duplicate]);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(11);
    const again = store.retryPendingSave();
    await vi.runAllTimersAsync();
    await again;
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(16);
    for (const args of api.saveFeatureGeometry.mock.calls)
      expect(args).toEqual(api.saveFeatureGeometry.mock.calls[0]);
    expect((await readRecoveryRecord("actor")).kind).toBe("record");
  });
  it("manual read is single flight and sends no PUT after known success", async () => {
    writeRecoveryRecord({
      schemaVersion: 1,
      command,
      state: "succeeded",
      result: successFixture(),
    });
    const store = setup();
    api.fetchWorkspace.mockRejectedValueOnce(new Error("offline"));
    await store.restorePendingSave();
    await settle(store);
    expect(store.canRetryCurrentRead).toBe(true);
    const read = deferred<ReturnType<typeof workspaceFixture>>();
    api.fetchWorkspace.mockReturnValue(read.promise);
    const first = store.refreshCurrentWorkspace();
    const second = store.refreshCurrentWorkspace();
    await vi.waitFor(() => expect(api.fetchWorkspace).toHaveBeenCalledTimes(2));
    expect(store.canRetryCurrentRead).toBe(false);
    read.resolve(workspaceFixture(true));
    await Promise.all([first, second]);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.phase).toBe("idle");
  });
  it("stale discard requires successful readback and clears the rejected attempt without HTTP", async () => {
    const store = setup(true);
    api.saveFeatureGeometry.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: { code: "DRAFT_VERSION_STALE", message: "stale" },
      },
    });
    api.fetchWorkspace.mockRejectedValue(new Error("offline"));
    await store.saveLocalDraft();
    await settle(store);
    expect(store.discardRejectedAttempt()).toBe(false);
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.refreshCurrentWorkspace();
    expect(store.canDiscardRejectedAttempt).toBe(true);
    const calls = api.fetchWorkspace.mock.calls.length;
    expect(store.discardRejectedAttempt()).toBe(true);
    expect(store.localDraft).toBeNull();
    expect(store.saveError).toBeNull();
    expect(api.fetchWorkspace).toHaveBeenCalledTimes(calls);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    expect(store.beginLocalEdit(target.featureId, 1)).toBe(true);
    expect(store.localDraft?.sourceToken).toBe("revision-b");
  });
  it("restore has five total attempts with original token", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    const store = setup();
    store.workspace = workspaceFixture(true);
    api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
    const restoring = store.restorePendingSave();
    await restoring;
    await vi.runAllTimersAsync();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(5);
    expect(api.saveFeatureGeometry.mock.calls[0]?.[1]).toEqual(command.request);
  });
  it("unknown Revert retries the same command without another confirmation and refresh uses stored command", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const store = setup();
    store.workspace = workspaceFixture(true);
    api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
    store.beginRevert();
    const sending = store.confirmRevert(
      store.revertConfirmation!.confirmationId,
    );
    await sending;
    await vi.runAllTimersAsync();
    const original = JSON.parse(JSON.stringify(store.pendingCommand));
    expect(original.request.geometry).toEqual(
      workspaceFixture(true).workOrder.editVersion.changeSet!.baselineGeometry,
    );
    expect(store.revertConfirmation).toBeNull();
    const retry = store.retryPendingSave();
    await vi.runAllTimersAsync();
    await retry;
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(11);
    setActivePinia(createPinia());
    const restored = setup();
    api.saveFeatureGeometry.mockResolvedValue({
      ...successFixture(original.request.commandId),
      operation: "unchanged",
      hasPersistedChangeSet: false,
      basicValidation: null,
      updatedFeature: {
        id: target.featureId,
        geometry: original.request.geometry,
      },
    });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture());
    await restored.restorePendingSave();
    await settle(restored);
    expect(api.saveFeatureGeometry).toHaveBeenLastCalledWith(
      original.target,
      original.request,
    );
    expect(restored.phase).toBe("idle");
    expect(restored.localDraft).toBeNull();
  });
  it("stale Revert needs new consent and new ID without a new local edit", async () => {
    const store = setup();
    store.workspace = workspaceFixture(true);
    api.saveFeatureGeometry.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: { code: "DRAFT_VERSION_STALE", message: "stale" },
      },
    });
    const newer = workspaceFixture(true);
    newer.workOrder.editVersion.draftVersionToken = "revision-c";
    api.fetchWorkspace.mockResolvedValue(newer);
    store.beginRevert();
    await store.confirmRevert(store.revertConfirmation!.confirmationId);
    await settle(store);
    const original = api.saveFeatureGeometry.mock.calls[0]![1];
    expect(store.beginRevert()).toBe("blocked");
    expect(store.discardRejectedAttempt()).toBe(true);
    expect(store.localDraft).toBeNull();
    expect(store.beginRevert()).toBe("confirm");
    await store.confirmRevert(store.revertConfirmation!.confirmationId);
    await settle(store);
    const next = api.saveFeatureGeometry.mock.calls[1]![1];
    expect(next.commandId).not.toBe(original.commandId);
    expect(next.draftVersionToken).toBe("revision-c");
    expect(next.geometry).toEqual(original.geometry);
    store.discardRejectedAttempt();
    store.workspace = workspaceFixture();
    expect(store.beginRevert()).toBe("blocked");
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(2);
  });
  it("refresh after completed stale readback does not restore the rejected draft", async () => {
    const store = setup(true);
    api.saveFeatureGeometry.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: { code: "DRAFT_VERSION_STALE", message: "stale" },
      },
    });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.saveLocalDraft();
    await settle(store);
    expect((await readRecoveryRecord("actor")).kind).toBe("empty");
    setActivePinia(createPinia());
    const restored = setup();
    restored.workspace = workspaceFixture(true);
    await restored.restorePendingSave();
    await settle(restored);
    expect(restored.phase).toBe("idle");
    expect(restored.localDraft).toBeNull();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
  it.each(["success", "rejection", "block"])(
    "manual series stops on terminal %s",
    async (terminal) => {
      vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
      writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
      const store = setup();
      api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
      const restoring = store.restorePendingSave();
      await vi.runAllTimersAsync();
      await restoring;
      api.saveFeatureGeometry.mockClear();
      if (terminal === "success")
        api.saveFeatureGeometry.mockResolvedValue(successFixture());
      if (terminal === "rejection")
        api.saveFeatureGeometry.mockRejectedValue({
          isAxiosError: true,
          response: {
            status: 409,
            data: { code: "DRAFT_VERSION_STALE", message: "stale" },
          },
        });
      if (terminal === "block")
        api.saveFeatureGeometry.mockResolvedValue({ malformed: true });
      api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
      const retry = store.retryPendingSave();
      await vi.runAllTimersAsync();
      await retry;
      expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
      expect(store.canRetryPendingCommand).toBe(false);
    },
  );
  it("refresh before first PUT restores same intent and old replay never replaces current", async () => {
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    const store = setup();
    api.saveFeatureGeometry.mockResolvedValue({
      ...successFixture(),
      draftVersionToken: "old-receipt",
    });
    const newer = workspaceFixture(true);
    newer.workOrder.editVersion.draftVersionToken = "new-current";
    api.fetchWorkspace.mockResolvedValue(newer);
    await store.restorePendingSave();
    await settle(store);
    expect(store.commandResult?.draftVersionToken).toBe("old-receipt");
    expect(store.workspace?.workOrder.editVersion.draftVersionToken).toBe(
      "new-current",
    );
    expect(api.saveFeatureGeometry).toHaveBeenCalledExactlyOnceWith(
      target,
      command.request,
    );
  });
  it("confirmed success refresh uses GET only", async () => {
    writeRecoveryRecord({
      schemaVersion: 1,
      command,
      state: "succeeded",
      result: successFixture(),
    });
    const store = setup();
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.restorePendingSave();
    await settle(store);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.phase).toBe("idle");
  });
  it("does not overlap client requests or continue after terminal success", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const store = setup(true);
    const slow = deferred<ReturnType<typeof successFixture>>();
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      slow.promise.then((v) => ({ ...v, commandId: r.commandId })),
    );
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    const save = store.saveLocalDraft();
    await vi.advanceTimersByTimeAsync(100000);
    await store.saveLocalDraft();
    await until(() => api.saveFeatureGeometry.mock.calls.length === 1);
    await store.retryPendingSave();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    slow.resolve(successFixture());
    await save;
    await vi.runAllTimersAsync();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
  it("dirty navigation is blocked and Cancel allows it", () => {
    const store = setup(true);
    store.selectWorkOrder("other");
    expect(store.selectedWorkOrderId).toBe(target.workOrderId);
    store.clearOpenedWorkspace();
    expect(store.workspace).not.toBeNull();
    store.cancelNavigation(store.navigation!.id);
    store.cancelLocalEdit();
    store.selectWorkOrder("other");
    expect(store.selectedWorkOrderId).toBe("other");
  });
  it("interceptor reset before Save catch preserves blocked record and hides private state", async () => {
    const store = setup(true);
    api.saveFeatureGeometry.mockImplementation(() => {
      const error = {
        isAxiosError: true,
        response: {
          status: 401,
          data: {
            code: "AUTH_REQUIRED",
            message: "Войдите",
            correlationId: "c",
          },
        },
      };
      useAuthStore().handleUnauthorizedResponse(error);
      return Promise.reject(error);
    });
    await store.saveLocalDraft();
    await settle(store);
    expect(store.workspace).toBeNull();
    expect(store.pendingCommand).toBeNull();
    expect(await readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { state: "blocked", reason: "access" },
    });
  });
  it("reset during retry delay stops timers and old actor sends nothing", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const store = setup(true);
    api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
    const saving = store.saveLocalDraft();
    await vi.advanceTimersByTimeAsync(0);
    await until(() => api.saveFeatureGeometry.mock.calls.length === 2);
    useAuthStore().clearLocalSession();
    useAuthStore().setAuth(
      "new",
      {
        id: "other",
        email: "other@example.local",
        role: "editor",
      },
      { sessionId: "sid-new" },
    );
    await vi.runAllTimersAsync();
    await saving;
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(2);
    expect(store.localDraft).toBeNull();
  });
  it("assignment loss hides workspace but retains recovery", async () => {
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    const store = setup();
    api.fetchAssignedWorkOrders.mockResolvedValue({ workOrders: [] });
    await store.loadAssigned();
    expect(store.workspace).toBeNull();
    expect(await readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { state: "blocked" },
    });
  });
  it("restores pending through existing workspace restore entry point", async () => {
    const store = setup();
    store.workspace = null;
    store.openedWorkOrderId = null;
    store.openedEditVersionId = null;
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({
        workOrderId: target.workOrderId,
        editVersionId: target.editVersionId,
      }),
    );
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    api.saveFeatureGeometry.mockResolvedValue(successFixture());
    await store.restoreOpenedWorkspace();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
  it("old GET cannot overwrite post-Save readback", async () => {
    const store = setup();
    store.workspace = null;
    store.openedWorkOrderId = null;
    store.openedEditVersionId = null;
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({
        workOrderId: target.workOrderId,
        editVersionId: target.editVersionId,
      }),
    );
    const old = deferred<ReturnType<typeof workspaceFixture>>();
    api.fetchWorkspace.mockReturnValueOnce(old.promise);
    const restoring = store.restoreOpenedWorkspace();
    store.workspace = workspaceFixture();
    store.openedWorkOrderId = target.workOrderId;
    store.openedEditVersionId = target.editVersionId;
    store.beginLocalEdit(target.featureId, 1);
    store.moveLocalVertex([65.1, 44.2]);
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.saveLocalDraft();
    await settle(store);
    old.resolve(workspaceFixture());
    await restoring;
    expect(store.workspace?.workOrder.editVersion.draftVersionToken).toBe(
      "revision-b",
    );
  });
  it("keeps pending immutable during uncertain outcome", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const store = setup(true);
    api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
    const save = store.saveLocalDraft();
    await save;
    expect(
      Object.isFrozen(store.pendingCommand?.request.geometry.coordinates),
    ).toBe(true);
    expect(store.moveLocalVertex([65.1, 44.4])).toBe(false);
    await vi.runAllTimersAsync();
    await save;
  });
  it("workspace access failure prevents auto replay after access returns", async () => {
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    const store = setup();
    store.workspace = null;
    store.openedWorkOrderId = null;
    store.openedEditVersionId = null;
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({
        workOrderId: target.workOrderId,
        editVersionId: target.editVersionId,
      }),
    );
    api.fetchWorkspace.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 403,
        data: {
          code: "ROLE_NOT_ALLOWED",
          message: "Отказ",
          correlationId: "c",
        },
      },
    });
    await store.restoreOpenedWorkspace();
    expect(await readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { state: "blocked", reason: "access" },
    });
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
  it("retains stale candidate for comparison and never automatically reapplies", async () => {
    const store = setup(true);
    api.saveFeatureGeometry.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: {
          code: "DRAFT_VERSION_STALE",
          message: "Устарело",
          correlationId: "c",
        },
      },
    });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.saveLocalDraft();
    await settle(store);
    expect(store.phase).toBe("stale");
    expect(store.localDraft?.sourceToken).toBe("revision-a");
    expect(store.moveLocalVertex([65.1, 44.4])).toBe(false);
    await store.saveLocalDraft();
    await settle(store);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    expect(store.cancelLocalEdit()).toBe(true);
    expect(store.activeComparison).toBeNull();
    expect(store.comparisonPreview).toBeNull();
    expect(store.beginLocalEdit(target.featureId, 1)).toBe(true);
    expect(store.localDraft?.sourceToken).toBe("revision-b");
  });
  it("malformed response blocks instead of retrying or claiming success", async () => {
    const store = setup(true);
    api.saveFeatureGeometry.mockResolvedValue({ commandId: "wrong" });
    await store.saveLocalDraft();
    await settle(store);
    expect(store.phase).toBe("blocked");
    expect(store.commandResult).toBeNull();
    expect(api.fetchWorkspace).not.toHaveBeenCalled();
  });
  it("cleanup failure retains success and direct read cannot bypass storage block", async () => {
    const store = setup(true);
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    const remove = vi
      .spyOn(IDBObjectStore.prototype, "delete")
      .mockImplementation(() => {
        throw new Error("storage");
      });
    await store.saveLocalDraft();
    await settle(store);
    expect(store.storageError).not.toBeNull();
    expect(store.beginLocalEdit(target.featureId, 1)).toBe(false);
    remove.mockRestore();
    await store.refreshCurrentWorkspace();
    expect(store.storageError).not.toBeNull();
    expect(store.recoveryRecord).toMatchObject({
      state: "blocked",
      result: { commandState: "succeeded" },
    });
    expect(api.fetchWorkspace).toHaveBeenCalledTimes(1);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
  it("direct read cannot bypass loss of editor role or blocked phase", async () => {
    writeRecoveryRecord({
      schemaVersion: 1,
      command,
      state: "succeeded",
      result: successFixture(),
    });
    const store = setup();
    api.fetchWorkspace.mockRejectedValue(new Error("offline"));
    await store.restorePendingSave();
    await settle(store);
    useAuthStore().user!.role = "reviewer";
    await store.refreshCurrentWorkspace();
    expect(api.fetchWorkspace).toHaveBeenCalledTimes(1);
    useAuthStore().user!.role = "editor";
    await useWorkspaceRecoveryStore().suspend(store.recoveryKey!);
    await store.refreshCurrentWorkspace();
    expect(api.fetchWorkspace).toHaveBeenCalledTimes(1);
  });
  it("no-op consumes a terminal result without requiring token change", async () => {
    const store = setup(true);
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve({
        ...successFixture(r.commandId),
        draftVersionToken: "revision-a",
        hasPersistedChangeSet: false,
        operation: "unchanged",
        basicValidation: null,
      }),
    );
    api.fetchWorkspace.mockResolvedValue(workspaceFixture());
    await store.saveLocalDraft();
    await settle(store);
    expect(store.phase).toBe("idle");
    expect(store.commandResult?.draftVersionToken).toBe("revision-a");
  });
  it("preserves access suspension through reset when storage writes fail", async () => {
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    const store = setup();
    const writes = vi
      .spyOn(Storage.prototype, "setItem")
      .mockImplementation(() => {
        throw new Error("denied");
      });
    useAuthStore().clearLocalSession();
    useAuthStore().setAuth(
      "test",
      {
        id: "actor",
        email: "editor@example.local",
        role: "editor",
      },
      { sessionId: "sid-test" },
    );
    writes.mockRestore();
    store.workspace = workspaceFixture();
    store.selectedWorkOrderId = store.openedWorkOrderId = target.workOrderId;
    store.openedEditVersionId = target.editVersionId;
    api.saveFeatureGeometry.mockResolvedValue(successFixture());
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await store.restorePendingSave();
    await settle(store);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.activeWorkspace).toBeNull();
    expect(await readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { state: "blocked", reason: "access" },
    });
  });
  it.each(["put", "readback", "list"])(
    "%s access failure hides private workspace and retains command",
    async (where) => {
      const store = setup(true);
      const error = {
        isAxiosError: true,
        response: {
          status: 403,
          data: {
            code: "ROLE_NOT_ALLOWED",
            message: "Отказ",
            correlationId: "c",
          },
        },
      };
      if (where === "put") api.saveFeatureGeometry.mockRejectedValue(error);
      if (where === "readback") {
        api.saveFeatureGeometry.mockImplementation((_t, r) =>
          Promise.resolve(successFixture(r.commandId)),
        );
        api.fetchWorkspace.mockRejectedValue(error);
      }
      if (where === "list") {
        vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
        api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
        const saving = store.saveLocalDraft();
        await saving;
        await until(() => api.saveFeatureGeometry.mock.calls.length >= 1);
        api.fetchAssignedWorkOrders.mockRejectedValue(error);
        await store.loadAssigned();
        const calls = api.saveFeatureGeometry.mock.calls.length;
        await vi.runAllTimersAsync();
        await saving;
        expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(calls);
      } else await store.saveLocalDraft();
      await settle(store);
      expect(store.activeWorkspace).toBeNull();
      expect(store.localDraft).toBeNull();
      expect(store.commandResult).toBeNull();
      expect(await readRecoveryRecord("actor")).toMatchObject({
        kind: "record",
        record: { state: "blocked", reason: "access" },
      });
      if (where === "readback")
        expect(await readRecoveryRecord("actor")).toMatchObject({
          kind: "record",
          record: { result: { commandState: "succeeded" } },
        });
    },
  );
  it("reselecting a vertex retains candidate and switching dirty target is blocked", () => {
    const store = setup(true);
    expect(store.beginLocalEdit(target.featureId, 1)).toBe(true);
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([
      65.1, 44.2,
    ]);
    store.workspace!.workOrder.editVersion.features.features.push({
      ...store.workspace!.workOrder.editVersion.features.features[0]!,
      id: "other-line",
    });
    expect(store.beginLocalEdit("other-line", 1)).toBe(false);
    expect(store.localDraft?.featureId).toBe(target.featureId);
  });
});
