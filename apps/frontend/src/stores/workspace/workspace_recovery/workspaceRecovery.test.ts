import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { nextTick, watchEffect } from "vue";
import { IDBFactory, IDBObjectStore } from "fake-indexeddb";
import {
  candidate,
  commandId,
  geometry,
  successFixture,
  target,
  workspaceFixture,
} from "@/test/workspaceEditFixture";
import {
  commandContext,
  recoveryKey,
  type RecoveryHost,
  type RecoverySession,
} from "@/contracts/workspace/workspace-recovery";
const api = vi.hoisted(() => ({
  saveFeatureGeometry: vi.fn(),
  readEditVersionSnapshot: vi.fn(),
}));
vi.mock("@/api/edit_version/editVersions", () => api);
vi.mock("@/composables/edit_version/useEditVersionEditor", () => api);
import { useWorkspaceRecoveryStore } from "./workspaceRecovery";
import * as maps from "@/api/edit_version/editVersionMap";
import * as changes from "@/api/edit_version/editVersionChangeSet";
import * as baselines from "@/api/edit_version/featureBaseline";
import { readEditVersionSnapshot } from "@/composables/edit_version/readEditVersionSnapshot";
let session: RecoverySession | null;
const completed: string[] = [];
const host: RecoveryHost = {
  isReadCurrent: () => true,
  session: () => session,
  canAccess: () => true,
  reserveRead: (context) => ({
    key: recoveryKey(context),
    sessionEpoch: session!.epoch,
    generation: 1,
  }),
  applyRead: () => "applied",
  complete: ({ record }) => {
    completed.push(record.command.target.workOrderId);
  },
  interrupted: () => {},
};
function command(suffix = "") {
  return {
    actorId: "actor",
    target: { ...target, workOrderId: "wo-1" + suffix },
    request: {
      commandId,
      draftVersionToken: "revision-a",
      geometry: structuredClone(candidate),
    },
  };
}
beforeEach(() => {
  setActivePinia(createPinia());
  Object.defineProperty(globalThis, "indexedDB", {
    value: new IDBFactory(),
    configurable: true,
  });
  sessionStorage.clear();
  api.saveFeatureGeometry.mockReset();
  api.readEditVersionSnapshot.mockReset();
  completed.length = 0;
  session = { actorId: "actor", epoch: 1, canEdit: true };
});
afterEach(() => {
  useWorkspaceRecoveryStore().stopRuntime();
  vi.useRealTimers();
});
it("publishes additions, phases, removal and collection replacement to Vue readers", async () => {
  const store = useWorkspaceRecoveryStore();
  store.bindHost(host);
  await store.initializeActor("actor");
  const pending = command();
  const key = recoveryKey(commandContext(pending));
  const observed = vi.fn();
  const stop = watchEffect(() =>
    observed(
      store.records,
      store.records[key]?.command.request.commandId,
      store.phases[key],
    ),
  );
  try {
    let release!: (result: ReturnType<typeof successFixture>) => void;
    api.saveFeatureGeometry.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          release = resolve;
        }),
    );
    api.readEditVersionSnapshot.mockResolvedValueOnce(workspaceFixture(true));
    const collection = store.records;
    await store.submit(pending, { geometry, vertexIndex: 1 });
    await nextTick();
    expect(observed).toHaveBeenCalledWith(collection, commandId, "sending");
    release(successFixture());
    await vi.waitFor(() => expect(completed).toContain(target.workOrderId));
    await nextTick();
    expect(observed).toHaveBeenLastCalledWith(collection, undefined, undefined);
    session = { actorId: "other", epoch: 2, canEdit: true };
    await store.initializeActor("other");
    await nextTick();
    expect(store.records).not.toBe(collection);
    expect(observed.mock.lastCall?.[0]).toBe(store.records);
  } finally {
    stop();
  }
});

it("detaches only its own host while a second Pinia finishes its pending command", async () => {
  const first = useWorkspaceRecoveryStore(createPinia());
  const second = useWorkspaceRecoveryStore(createPinia());
  const doneFirst = vi.fn(),
    doneSecond = vi.fn();
  const detach = first.bindHost({ ...host, complete: doneFirst });
  const detachSecond = second.bindHost({ ...host, complete: doneSecond });
  try {
    await first.initializeActor("actor");
    await second.initializeActor("actor");
    const a = command("a"),
      b = command("b");
    let finishA!: (result: ReturnType<typeof successFixture>) => void;
    let finishB!: (result: ReturnType<typeof successFixture>) => void;
    api.saveFeatureGeometry
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            finishA = resolve;
          }),
      )
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            finishB = resolve;
          }),
      );
    api.readEditVersionSnapshot.mockImplementation(async (wo) => {
      const workspace = workspaceFixture(true);
      workspace.workOrder.id = wo;
      return workspace;
    });
    await first.submit(a, { geometry, vertexIndex: 1 });
    await second.submit(b, { geometry, vertexIndex: 1 });
    detach();
    finishA(successFixture());
    finishB(successFixture());
    await vi.waitFor(() => expect(doneSecond).toHaveBeenCalledOnce());
    expect(doneFirst).not.toHaveBeenCalled();
    expect(first.getRecord(recoveryKey(commandContext(a)))?.outcome.kind).toBe(
      "unknown",
    );
    expect(second.getRecord(recoveryKey(commandContext(b)))).toBeNull();
  } finally {
    detach();
    detachSecond();
  }
});

it("unknown A does not block saving independent B and repeats only frozen A", async () => {
  const store = useWorkspaceRecoveryStore();
  store.bindHost(host);
  await store.initializeActor("actor");
  api.saveFeatureGeometry.mockImplementation(async (t) => {
    if (t.workOrderId === "wo-1") throw { isAxiosError: true, request: {} };
    return successFixture();
  });
  api.readEditVersionSnapshot.mockImplementation(async (wo) => {
    const w = workspaceFixture(true);
    w.workOrder.id = wo;
    return w;
  });
  const a = command(),
    b = command("b"),
    key = recoveryKey(commandContext(a));
  expect(await store.submit(a, { geometry, vertexIndex: 1 })).toBe("started");
  expect(await store.submit(b, { geometry, vertexIndex: 1 })).toBe("started");
  await vi.waitFor(() => expect(completed).toContain("wo-1b"));
  expect(store.getRecord(key)?.command.request).toEqual(a.request);
  expect(await store.submit(a, { geometry, vertexIndex: 1 })).toBe("blocked");
});
it("known success survives access loss and confirmation runs only GET", async () => {
  const store = useWorkspaceRecoveryStore();
  store.bindHost(host);
  await store.initializeActor("actor");
  api.saveFeatureGeometry.mockResolvedValue(successFixture());
  api.readEditVersionSnapshot.mockRejectedValue(new Error("network"));
  const a = command(),
    key = recoveryKey(commandContext(a));
  await store.submit(a, { geometry, vertexIndex: 1 });
  await vi.waitFor(() => expect(store.readbackErrors[key]).toBeTruthy());
  await store.suspendActor("actor");
  expect(store.getRecord(key)?.outcome.kind).toBe("succeeded");
  api.saveFeatureGeometry.mockClear();
  api.readEditVersionSnapshot.mockResolvedValue(workspaceFixture(true));
  await store.resumeAfterAccess(key, commandId, 1);
  await vi.waitFor(() => expect(completed).toContain("wo-1"));
  expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
});
it("discards a failed baseline checkpoint superseded by a later version read", async () => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  const store = useWorkspaceRecoveryStore();
  let generation = 0;
  const applied: string[] = [];
  store.bindHost({
    ...host,
    reserveRead: (context) => ({
      ...host.reserveRead(context),
      generation: ++generation,
    }),
    isReadCurrent: (ticket) => ticket.generation === generation,
    applyRead: (_ticket, snapshot) => {
      applied.push(snapshot.workOrder.editVersion.draftVersionToken);
      return "applied";
    },
  });
  const saved = workspaceFixture(true);
  const reverted = workspaceFixture();
  reverted.workOrder.editVersion.draftVersionToken = "revision-c";
  const map = vi
    .spyOn(maps, "fetchEditVersionMap")
    .mockResolvedValueOnce(saved)
    .mockResolvedValue(reverted);
  const change = vi
    .spyOn(changes, "fetchEditVersionChangeSet")
    .mockResolvedValueOnce(saved.workOrder.editVersion)
    .mockResolvedValue(reverted.workOrder.editVersion);
  const baseline = vi
    .spyOn(baselines, "fetchFeatureBaseline")
    .mockRejectedValue(new Error("offline"));
  try {
    api.readEditVersionSnapshot.mockImplementation(readEditVersionSnapshot);
    api.saveFeatureGeometry.mockResolvedValue(successFixture());
    await store.initializeActor("actor");
    const a = command();
    const key = recoveryKey(commandContext(a));
    await store.submit(a, { geometry, vertexIndex: 1 });
    await vi.waitFor(() => expect(baseline).toHaveBeenCalledTimes(1));
    await vi.advanceTimersByTimeAsync(37000);
    expect(store.readbackErrors[key]).toContain("исходную геометрию");
    generation++;
    await store.retryRead(key);
    expect(applied).toEqual(["revision-c"]);
    expect(map).toHaveBeenCalledTimes(2);
    expect(change).toHaveBeenCalledTimes(2);
    expect(baseline).toHaveBeenCalledTimes(5);
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
  } finally {
    vi.restoreAllMocks();
  }
});
it("actor change while preparing storage cannot send with the new session", async () => {
  const store = useWorkspaceRecoveryStore();
  store.bindHost(host);
  await store.initializeActor("actor");
  const pending = store.submit(command(), { geometry, vertexIndex: 1 });
  session = { actorId: "other", epoch: 2, canEdit: true };
  expect(await pending).toBe("blocked");
  expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
});

it.each(["ROLE_NOT_ALLOWED", "USER_INACTIVE"])(
  "global %s stops every context but preserves terminal results",
  async (code) => {
    const store = useWorkspaceRecoveryStore();
    store.bindHost(host);
    await store.initializeActor("actor");
    api.saveFeatureGeometry.mockResolvedValue(successFixture());
    api.readEditVersionSnapshot.mockRejectedValue(new Error("offline"));
    const a = command(),
      b = command("b");
    await store.submit(a, { geometry, vertexIndex: 1 });
    const keyA = recoveryKey(commandContext(a));
    await vi.waitFor(() => expect(store.readbackErrors[keyA]).toBeTruthy());
    api.saveFeatureGeometry.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 403,
        data: { code, message: "denied", correlationId: null },
      },
    });
    await store.submit(b, { geometry, vertexIndex: 1 });
    await vi.waitFor(() =>
      expect(
        Object.values(store.records).every((r) => r.requiresAccessConfirmation),
      ).toBe(true),
    );
    expect(store.getRecord(keyA)?.outcome.kind).toBe("succeeded");
    expect(Object.keys(store.records)).toHaveLength(2);
  },
);
it("context access loss stops only its own work order", async () => {
  const store = useWorkspaceRecoveryStore();
  store.bindHost(host);
  await store.initializeActor("actor");
  api.saveFeatureGeometry.mockImplementation(async (t) => {
    if (t.workOrderId === "wo-1")
      throw {
        isAxiosError: true,
        response: {
          status: 404,
          data: {
            code: "EDIT_VERSION_NOT_FOUND",
            message: "closed",
            correlationId: null,
          },
        },
      };
    return successFixture();
  });
  api.readEditVersionSnapshot.mockImplementation(async (wo) => {
    const w = workspaceFixture(true);
    w.workOrder.id = wo;
    return w;
  });
  await store.submit(command(), { geometry, vertexIndex: 1 });
  await store.submit(command("b"), { geometry, vertexIndex: 1 });
  await vi.waitFor(() => expect(completed).toContain("wo-1b"));
  expect(
    store.getRecord(recoveryKey(commandContext(command())))
      ?.requiresAccessConfirmation,
  ).toBe(true);
});

it("prepareActorLogout verifies durable sent intent without suspending or hiding it", async () => {
  const store = useWorkspaceRecoveryStore();
  store.bindHost(host);
  await store.initializeActor("actor");
  api.saveFeatureGeometry.mockReturnValue(new Promise(() => {}));
  const pending = command();
  await store.submit(pending, { geometry, vertexIndex: 1 });
  const key = recoveryKey(commandContext(pending));
  expect(await store.prepareActorLogout("actor")).toBe(true);
  expect(store.initializedActor).toBe("actor");
  expect(store.isRunning(key)).toBe(true);
  expect(store.getRecord(key)?.blocks).toEqual([]);
  expect(store.getRecord(key)?.requiresAccessConfirmation).toBe(false);
});

it("prepareActorLogout waits for a pending insert and refuses its failed durability", async () => {
  const store = useWorkspaceRecoveryStore();
  store.bindHost(host);
  await store.initializeActor("actor");
  const insert = vi
    .spyOn(IDBObjectStore.prototype, "add")
    .mockImplementation(() => {
      throw new Error("storage");
    });
  const submitting = store.submit(command(), { geometry, vertexIndex: 1 });
  const preparation = store.prepareActorLogout("actor");
  expect(await submitting).toBe("blocked");
  insert.mockRestore();
  expect(await preparation).toBe(false);
  expect(store.initializedActor).toBe("actor");
  expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
});
