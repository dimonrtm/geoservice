import { editorTestContext } from "@/test/editorTestContext";
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
  readMap: vi.fn(),
  openEditVersion: vi.fn(),
  saveFeatureGeometry: vi.fn(),
}));
vi.mock("@/api/workOrders", () => api);
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
  const store = editorTestContext();
  store.seed(workspaceFixture());
  store.editorSession.openedWorkOrderId = store.workOrders.selectedWorkOrderId =
    target.workOrderId;
  store.editorSession.openedEditVersionId = target.editVersionId;
  store.workOrders.items = [
    {
      id: target.workOrderId,
      code: "WO",
      title: "Работа",
      description: null,
      status: "in_progress",
    },
  ];
  if (edit) {
    store.editVersionDraft.beginLocalEdit(target.featureId, 1);
    store.editVersionDraft.moveLocalVertex([65.1, 44.2]);
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
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.restorePendingSave();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.didSaveChangeGeometry).toBeNull();
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.editor.snapshot?.workOrder.editVersion.draftVersionToken).toBe(
      "revision-b",
    );
  });
  it("late success cannot classify or replace another context", async () => {
    const store = setup(true);
    const response = deferred<ReturnType<typeof successFixture>>();
    api.saveFeatureGeometry.mockReturnValue(response.promise);
    const saving = store.editVersionCommands.saveLocalDraft();
    await vi.waitFor(() =>
      expect(store.editVersionCommands.pendingCommand).not.toBeNull(),
    );
    const id = store.editVersionCommands.pendingCommand!.request.commandId;
    store.editorSession.clearOpenedWorkspace({ force: true });
    response.resolve(successFixture(id));
    await saving;
    expect(store.editVersionCommands.didSaveChangeGeometry).toBeNull();
    expect(store.editVersionCommands.submittedSourceGeometry).toBeNull();
    expect(store.editor.snapshot).toBeNull();
    expect(api.readMap).not.toHaveBeenCalled();
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
    const save = store.editVersionCommands.saveLocalDraft();
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
    expect(store.editVersionCommands.phase).toBe("unknown");
    for (const args of api.saveFeatureGeometry.mock.calls)
      expect(args[1]).toEqual(api.saveFeatureGeometry.mock.calls[0]?.[1]);
    const retry = store.editVersionCommands.retryPendingSave();
    const duplicate = store.editVersionCommands.retryPendingSave();
    await vi.runAllTimersAsync();
    await Promise.all([retry, duplicate]);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(11);
    const again = store.editVersionCommands.retryPendingSave();
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
    api.readMap.mockRejectedValueOnce(new Error("offline"));
    await store.editVersionCommands.restorePendingSave();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.canRetryCurrentRead).toBe(true);
    const read = deferred<ReturnType<typeof workspaceFixture>>();
    api.readMap.mockReturnValue(read.promise);
    const first = store.editVersionCommands.refreshCurrentWorkspace();
    const second = store.editVersionCommands.refreshCurrentWorkspace();
    await vi.waitFor(() => expect(api.readMap).toHaveBeenCalledTimes(2));
    expect(store.editVersionCommands.canRetryCurrentRead).toBe(false);
    read.resolve(workspaceFixture(true));
    await Promise.all([first, second]);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.editVersionCommands.phase).toBe("idle");
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
    api.readMap.mockRejectedValue(new Error("offline"));
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.discardRejectedAttempt()).toBe(false);
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.refreshCurrentWorkspace();
    expect(store.editVersionCommands.canDiscardRejectedAttempt).toBe(true);
    const calls = api.readMap.mock.calls.length;
    expect(store.editVersionCommands.discardRejectedAttempt()).toBe(true);
    expect(store.editVersionDraft.localDraft).toBeNull();
    expect(store.editVersionCommands.saveError).toBeNull();
    expect(api.readMap).toHaveBeenCalledTimes(calls);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    expect(store.editVersionDraft.beginLocalEdit(target.featureId, 1)).toBe(
      true,
    );
    expect(store.editVersionDraft.localDraft?.sourceToken).toBe("revision-b");
  });
  it("restore has five total attempts with original token", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    const store = setup();
    store.seed(workspaceFixture(true));
    api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
    const restoring = store.editVersionCommands.restorePendingSave();
    await restoring;
    await vi.runAllTimersAsync();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(5);
    expect(api.saveFeatureGeometry.mock.calls[0]?.[1]).toEqual(command.request);
  });
  it("unknown Revert retries the same command without another confirmation and refresh uses stored command", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const store = setup();
    store.seed(workspaceFixture(true));
    api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
    store.editVersionCommands.beginRevert();
    const sending = store.editVersionCommands.confirmRevert(
      store.editVersionCommands.revertConfirmation!.confirmationId,
    );
    await sending;
    await vi.runAllTimersAsync();
    const original = JSON.parse(
      JSON.stringify(store.editVersionCommands.pendingCommand),
    );
    expect(original.request.geometry).toEqual(
      workspaceFixture(true).workOrder.editVersion.changeSet!.baselineGeometry,
    );
    expect(store.editVersionCommands.revertConfirmation).toBeNull();
    const retry = store.editVersionCommands.retryPendingSave();
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
    api.readMap.mockResolvedValue(workspaceFixture());
    await restored.editVersionCommands.restorePendingSave();
    await settle(restored.editVersionCommands);
    expect(api.saveFeatureGeometry).toHaveBeenLastCalledWith(
      original.target,
      original.request,
    );
    expect(restored.editVersionCommands.phase).toBe("idle");
    expect(restored.editVersionDraft.localDraft).toBeNull();
  });
  it("stale Revert needs new consent and new ID without a new local edit", async () => {
    const store = setup();
    store.seed(workspaceFixture(true));
    api.saveFeatureGeometry.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: { code: "DRAFT_VERSION_STALE", message: "stale" },
      },
    });
    const newer = workspaceFixture(true);
    newer.workOrder.editVersion.draftVersionToken = "revision-c";
    api.readMap.mockResolvedValue(newer);
    store.editVersionCommands.beginRevert();
    await store.editVersionCommands.confirmRevert(
      store.editVersionCommands.revertConfirmation!.confirmationId,
    );
    await settle(store.editVersionCommands);
    const original = api.saveFeatureGeometry.mock.calls[0]![1];
    expect(store.editVersionCommands.beginRevert()).toBe("blocked");
    expect(store.editVersionCommands.discardRejectedAttempt()).toBe(true);
    expect(store.editVersionDraft.localDraft).toBeNull();
    expect(store.editVersionCommands.beginRevert()).toBe("confirm");
    await store.editVersionCommands.confirmRevert(
      store.editVersionCommands.revertConfirmation!.confirmationId,
    );
    await settle(store.editVersionCommands);
    const next = api.saveFeatureGeometry.mock.calls[1]![1];
    expect(next.commandId).not.toBe(original.commandId);
    expect(next.draftVersionToken).toBe("revision-c");
    expect(next.geometry).toEqual(original.geometry);
    store.editVersionCommands.discardRejectedAttempt();
    store.seed(workspaceFixture());
    expect(store.editVersionCommands.beginRevert()).toBe("blocked");
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
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect((await readRecoveryRecord("actor")).kind).toBe("empty");
    setActivePinia(createPinia());
    const restored = setup();
    restored.seed(workspaceFixture(true));
    await restored.editVersionCommands.restorePendingSave();
    await settle(restored.editVersionCommands);
    expect(restored.editVersionCommands.phase).toBe("idle");
    expect(restored.editVersionDraft.localDraft).toBeNull();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
  it.each(["success", "rejection", "block"])(
    "manual series stops on terminal %s",
    async (terminal) => {
      vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
      writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
      const store = setup();
      api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
      const restoring = store.editVersionCommands.restorePendingSave();
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
      api.readMap.mockResolvedValue(workspaceFixture(true));
      const retry = store.editVersionCommands.retryPendingSave();
      await vi.runAllTimersAsync();
      await retry;
      expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
      expect(store.editVersionCommands.canRetryPendingCommand).toBe(false);
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
    api.readMap.mockResolvedValue(newer);
    await store.editVersionCommands.restorePendingSave();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.commandResult?.draftVersionToken).toBe(
      "old-receipt",
    );
    expect(store.editor.snapshot?.workOrder.editVersion.draftVersionToken).toBe(
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
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.restorePendingSave();
    await settle(store.editVersionCommands);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.editVersionCommands.phase).toBe("idle");
  });
  it("does not overlap client requests or continue after terminal success", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const store = setup(true);
    const slow = deferred<ReturnType<typeof successFixture>>();
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      slow.promise.then((v) => ({ ...v, commandId: r.commandId })),
    );
    api.readMap.mockResolvedValue(workspaceFixture(true));
    const save = store.editVersionCommands.saveLocalDraft();
    await vi.advanceTimersByTimeAsync(100000);
    await store.editVersionCommands.saveLocalDraft();
    await until(() => api.saveFeatureGeometry.mock.calls.length === 1);
    await store.editVersionCommands.retryPendingSave();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    slow.resolve(successFixture());
    await save;
    await vi.runAllTimersAsync();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
  it("dirty navigation is blocked and Cancel allows it", () => {
    const store = setup(true);
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "other",
    });
    expect(store.workOrders.selectedWorkOrderId).toBe(target.workOrderId);
    store.editorSession.clearOpenedWorkspace();
    expect(store.editor.snapshot).not.toBeNull();
    store.editorNavigation.cancelNavigation(
      store.editorNavigation.navigation!.id,
    );
    store.editVersionDraft.cancelLocalEdit();
    store.editorNavigation.requestNavigation({
      kind: "work-order",
      workOrderId: "other",
    });
    expect(store.workOrders.selectedWorkOrderId).toBe("other");
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
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editor.snapshot).toBeNull();
    expect(store.editVersionCommands.pendingCommand).toBeNull();
    expect(await readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { state: "blocked", reason: "access" },
    });
  });
  it("reset during retry delay stops timers and old actor sends nothing", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const store = setup(true);
    api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
    const saving = store.editVersionCommands.saveLocalDraft();
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
    expect(store.editVersionDraft.localDraft).toBeNull();
  });
  it("assignment loss hides workspace but retains recovery", async () => {
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    const store = setup();
    api.fetchAssignedWorkOrders.mockResolvedValue({ workOrders: [] });
    await store.workOrders.loadAssigned();
    await store.editorSession.reconcileAssignments();
    expect(store.editor.snapshot).toBeNull();
    expect(await readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { state: "blocked" },
    });
  });
  it("restores pending through existing workspace restore entry point", async () => {
    const store = setup();
    store.seed(null);
    store.editorSession.openedWorkOrderId = null;
    store.editorSession.openedEditVersionId = null;
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({
        workOrderId: target.workOrderId,
        editVersionId: target.editVersionId,
      }),
    );
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    api.readMap.mockResolvedValue(workspaceFixture(true));
    api.saveFeatureGeometry.mockResolvedValue(successFixture());
    await store.editorSession.restoreOpenedWorkspace();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  });
  it("old GET cannot overwrite post-Save readback", async () => {
    const store = setup();
    store.seed(null);
    store.editorSession.openedWorkOrderId = null;
    store.editorSession.openedEditVersionId = null;
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({
        workOrderId: target.workOrderId,
        editVersionId: target.editVersionId,
      }),
    );
    const old = deferred<ReturnType<typeof workspaceFixture>>();
    api.readMap.mockReturnValueOnce(old.promise);
    const restoring = store.editorSession.restoreOpenedWorkspace();
    store.seed(workspaceFixture());
    store.editorSession.openedWorkOrderId = target.workOrderId;
    store.editorSession.openedEditVersionId = target.editVersionId;
    store.editVersionDraft.beginLocalEdit(target.featureId, 1);
    store.editVersionDraft.moveLocalVertex([65.1, 44.2]);
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    old.resolve(workspaceFixture());
    await restoring;
    expect(store.editor.snapshot?.workOrder.editVersion.draftVersionToken).toBe(
      "revision-b",
    );
  });
  it("keeps pending immutable during uncertain outcome", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const store = setup(true);
    api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
    const save = store.editVersionCommands.saveLocalDraft();
    await save;
    expect(
      Object.isFrozen(
        store.editVersionCommands.pendingCommand?.request.geometry.coordinates,
      ),
    ).toBe(true);
    expect(store.editVersionDraft.moveLocalVertex([65.1, 44.4])).toBe(false);
    await vi.runAllTimersAsync();
    await save;
  });
  it("workspace access failure prevents auto replay after access returns", async () => {
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    const store = setup();
    store.seed(null);
    store.editorSession.openedWorkOrderId = null;
    store.editorSession.openedEditVersionId = null;
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({
        workOrderId: target.workOrderId,
        editVersionId: target.editVersionId,
      }),
    );
    api.readMap.mockRejectedValue({
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
    await store.editorSession.restoreOpenedWorkspace();
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
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.phase).toBe("stale");
    expect(store.editVersionDraft.localDraft?.sourceToken).toBe("revision-a");
    expect(store.editVersionDraft.moveLocalVertex([65.1, 44.4])).toBe(false);
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    expect(store.editVersionDraft.cancelLocalEdit()).toBe(true);
    expect(store.editVersionCommands.activeComparison).toBeNull();
    expect(store.editVersionCommands.comparisonPreview).toBeNull();
    expect(store.editVersionDraft.beginLocalEdit(target.featureId, 1)).toBe(
      true,
    );
    expect(store.editVersionDraft.localDraft?.sourceToken).toBe("revision-b");
  });
  it("malformed response blocks instead of retrying or claiming success", async () => {
    const store = setup(true);
    api.saveFeatureGeometry.mockResolvedValue({ commandId: "wrong" });
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.phase).toBe("blocked");
    expect(store.editVersionCommands.commandResult).toBeNull();
    expect(api.readMap).not.toHaveBeenCalled();
  });
  it("cleanup failure retains success and direct read cannot bypass storage block", async () => {
    const store = setup(true);
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.readMap.mockResolvedValue(workspaceFixture(true));
    const remove = vi
      .spyOn(IDBObjectStore.prototype, "delete")
      .mockImplementation(() => {
        throw new Error("storage");
      });
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.storageError).not.toBeNull();
    expect(store.editVersionDraft.beginLocalEdit(target.featureId, 1)).toBe(
      false,
    );
    remove.mockRestore();
    await store.editVersionCommands.refreshCurrentWorkspace();
    expect(store.editVersionCommands.storageError).not.toBeNull();
    expect(store.editVersionCommands.recoveryRecord).toMatchObject({
      state: "blocked",
      result: { commandState: "succeeded" },
    });
    expect(api.readMap).toHaveBeenCalledTimes(1);
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
    api.readMap.mockRejectedValue(new Error("offline"));
    await store.editVersionCommands.restorePendingSave();
    await settle(store.editVersionCommands);
    useAuthStore().user!.role = "reviewer";
    await store.editVersionCommands.refreshCurrentWorkspace();
    expect(api.readMap).toHaveBeenCalledTimes(1);
    useAuthStore().user!.role = "editor";
    await useWorkspaceRecoveryStore().suspend(
      store.editVersionCommands.recoveryKey!,
    );
    await store.editVersionCommands.refreshCurrentWorkspace();
    expect(api.readMap).toHaveBeenCalledTimes(1);
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
    api.readMap.mockResolvedValue(workspaceFixture());
    await store.editVersionCommands.saveLocalDraft();
    await settle(store.editVersionCommands);
    expect(store.editVersionCommands.phase).toBe("idle");
    expect(store.editVersionCommands.commandResult?.draftVersionToken).toBe(
      "revision-a",
    );
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
    store.seed(workspaceFixture());
    store.workOrders.selectedWorkOrderId =
      store.editorSession.openedWorkOrderId = target.workOrderId;
    store.editorSession.openedEditVersionId = target.editVersionId;
    api.saveFeatureGeometry.mockResolvedValue(successFixture());
    api.readMap.mockResolvedValue(workspaceFixture(true));
    await store.editVersionCommands.restorePendingSave();
    await settle(store.editVersionCommands);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(store.editorSession.activeWorkspace).toBeNull();
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
        api.readMap.mockRejectedValue(error);
      }
      if (where === "list") {
        vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
        api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
        const saving = store.editVersionCommands.saveLocalDraft();
        await saving;
        await until(() => api.saveFeatureGeometry.mock.calls.length >= 1);
        api.fetchAssignedWorkOrders.mockRejectedValue(error);
        await store.workOrders.loadAssigned();
        await store.editorSession.reconcileAssignments();
        const calls = api.saveFeatureGeometry.mock.calls.length;
        await vi.runAllTimersAsync();
        await saving;
        expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(calls);
      } else await store.editVersionCommands.saveLocalDraft();
      await settle(store.editVersionCommands);
      expect(store.editorSession.activeWorkspace).toBeNull();
      expect(store.editVersionDraft.localDraft).toBeNull();
      expect(store.editVersionCommands.commandResult).toBeNull();
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
    expect(store.editVersionDraft.beginLocalEdit(target.featureId, 1)).toBe(
      true,
    );
    expect(
      store.editVersionDraft.localDraft?.candidateGeometry.coordinates[1],
    ).toEqual([65.1, 44.2]);
    store.editor.snapshot!.workOrder.editVersion.features.features.push({
      ...store.editor.snapshot!.workOrder.editVersion.features.features[0]!,
      id: "other-line",
    });
    expect(store.editVersionDraft.beginLocalEdit("other-line", 1)).toBe(false);
    expect(store.editVersionDraft.localDraft?.featureId).toBe(target.featureId);
  });
});

vi.mock("@/api/editVersions", () => api);
vi.mock("@/api/editVersionMap", async () => {
  const { fixtureMap } = await import("@/test/editorReadFixtures");
  return {
    fetchEditVersionMap: (workOrderId: string, versionId: string) =>
      fixtureMap(api.readMap, workOrderId, versionId),
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
