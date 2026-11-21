import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  commandContext,
  createRecoveryRecord,
  recoveryKey,
  type RecoveryHost,
  type RecoveryRecordV2,
  type RecoverySession,
} from "@/contracts/workspace/workspace-recovery";
import {
  candidate,
  commandId,
  geometry,
  successFixture,
  target,
  workspaceFixture,
} from "@/test/workspaceEditFixture";
import type { RecoveryIO } from "./workspaceRecoveryIO";
import {
  createRecoveryExecutor,
  createRecoveryState,
} from "./createRecoveryExecutor";

const command = {
  actorId: "alex",
  target,
  request: { commandId, draftVersionToken: "a", geometry: candidate },
};
const source = { geometry, vertexIndex: 1 };
const key = recoveryKey(commandContext(command));
const success = { kind: "succeeded" as const, result: successFixture() };
const snapshot = {
  kind: "succeeded" as const,
  workspace: workspaceFixture(true),
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}

function setup() {
  const state = createRecoveryState();
  const durable = new Map<string, RecoveryRecordV2>();
  const steps: string[] = [];
  const saveRecord = async (record: RecoveryRecordV2) => {
    durable.set(record.key, structuredClone(record));
  };
  const io = {
    loadActor: vi.fn<RecoveryIO["loadActor"]>(async (actorId) => ({
      records: structuredClone(
        [...durable.values()].filter(
          (record) => record.command.actorId === actorId,
        ),
      ),
      invalid: [],
    })),
    insert: vi.fn<RecoveryIO["insert"]>(async (record) => {
      steps.push("insert");
      await saveRecord(record);
    }),
    replace: vi.fn<RecoveryIO["replace"]>(async (record) => {
      steps.push("replace");
      await saveRecord(record);
    }),
    remove: vi.fn<RecoveryIO["remove"]>(async (k) => {
      steps.push("remove");
      durable.delete(k);
    }),
    send: vi.fn<RecoveryIO["send"]>(async () => {
      steps.push("send");
      return success;
    }),
    read: vi.fn<RecoveryIO["read"]>(async () => {
      steps.push("read");
      return snapshot;
    }),
    waitForRetry: vi.fn<RecoveryIO["waitForRetry"]>().mockResolvedValue(true),
    scheduler: {
      run: <T>(_key: string, _signal: AbortSignal, fetch: () => Promise<T>) =>
        fetch(),
    },
  };
  const session: RecoverySession = {
    actorId: command.actorId,
    epoch: 1,
    canEdit: true,
  };
  const host = {
    session: () => session,
    canAccess: vi.fn(() => true),
    reserveRead: vi.fn(() => ({
      key,
      sessionEpoch: session.epoch,
      generation: 1,
    })),
    isReadCurrent: vi.fn(() => true),
    applyRead: vi.fn<RecoveryHost["applyRead"]>(() => {
      steps.push("applyRead");
      return "applied";
    }),
    complete: vi.fn(() => {
      steps.push("complete");
    }),
    interrupted: vi.fn(),
  };
  const executor = createRecoveryExecutor(state, io);
  executor.bindHost(host);
  return { state, durable, steps, io, session, host, executor };
}

beforeEach(() => {
  vi.stubGlobal("indexedDB", undefined);
  vi.stubGlobal("sessionStorage", undefined);
});
afterEach(() => vi.unstubAllGlobals());

it("persists the command before PUT and completes only after readback and removal", async () => {
  const { executor, io, steps, host, state } = setup();
  const inserted = deferred<void>();
  io.insert.mockImplementationOnce(() => {
    steps.push("insert");
    return inserted.promise;
  });
  await executor.initializeActor("alex");
  const submitting = executor.submit(command, source);
  expect(io.send).not.toHaveBeenCalled();
  inserted.resolve();
  expect(await submitting).toBe("started");
  await vi.waitFor(() => expect(host.complete).toHaveBeenCalledOnce());
  expect(steps).toEqual([
    "insert",
    "send",
    "replace",
    "read",
    "applyRead",
    "remove",
    "complete",
  ]);
  expect(state.records[key]).toBeUndefined();
});

it("retries the same unknown command and reads only after known success", async () => {
  const { executor, io, host, state } = setup();
  io.send.mockResolvedValueOnce({ kind: "retryableUnknown" });
  io.read.mockResolvedValueOnce({ kind: "failed", message: "read failed" });
  await executor.initializeActor("alex");
  await executor.submit(command, source);
  await vi.waitFor(() => expect(state.readbackErrors[key]).toBe("read failed"));
  expect(io.send.mock.calls).toEqual([
    [command, false],
    [command, true],
  ]);
  expect(io.waitForRetry).toHaveBeenCalledWith(0, expect.any(AbortSignal));
  io.remove.mockRejectedValueOnce(new Error("cleanup"));
  await executor.retryRead(key);
  expect(io.send).toHaveBeenCalledTimes(2);
  expect(state.records[key]?.outcome).toEqual(success);
  expect(state.records[key]?.blocks).toContain("storage");
  expect(host.complete).not.toHaveBeenCalled();
});

it.each(["stale", "domainRejected"] as const)(
  "finishes %s with its required reads",
  async (kind) => {
    const { executor, io, host } = setup();
    io.send.mockResolvedValueOnce({
      kind,
      error: { code: kind, message: kind, status: 409, correlationId: null },
    });
    await executor.initializeActor("alex");
    await executor.submit(command, source);
    await vi.waitFor(() => expect(host.complete).toHaveBeenCalledOnce());
    expect(io.read).toHaveBeenCalledTimes(kind === "stale" ? 1 : 0);
  },
);

it.each(["unknown", "succeeded", "blocked"] as const)(
  "restores a %s record",
  async (kind) => {
    const { executor, durable, io, host } = setup();
    const record = createRecoveryRecord(command, source);
    if (kind === "succeeded") record.outcome = success;
    if (kind === "blocked") record.requiresAccessConfirmation = true;
    durable.set(key, record);
    await executor.initializeActor("alex");
    if (kind !== "blocked")
      await vi.waitFor(() => expect(host.complete).toHaveBeenCalledOnce());
    expect(io.send).toHaveBeenCalledTimes(kind === "unknown" ? 1 : 0);
    if (kind === "unknown") expect(io.send).toHaveBeenCalledWith(command, true);
    expect(io.read).toHaveBeenCalledTimes(kind === "blocked" ? 0 : 1);
  },
);

it.each([key, null])(
  "isolates corruption by its identifiable key (%s)",
  async (invalidKey) => {
    const { executor, io, state } = setup();
    io.loadActor.mockResolvedValueOnce({
      records: [],
      invalid: [{ key: invalidKey, reason: "invalid" }],
    });
    await executor.initializeActor("alex");
    if (invalidKey) {
      expect(state.contextErrors[key]).toBeTruthy();
      expect(state.storageError).toBeNull();
    } else expect(state.storageError).toBeTruthy();
    expect(await executor.submit(command, source)).toBe("blocked");
    expect(io.send).not.toHaveBeenCalled();
  },
);

it("retains the receipt for another GET if the editor cannot apply a valid snapshot", async () => {
  const { executor, io, state, host } = setup();
  io.read.mockResolvedValueOnce({ kind: "failed", message: "offline" });
  await executor.initializeActor("alex");
  await executor.submit(command, source);
  await vi.waitFor(() => expect(state.readbackErrors[key]).toBe("offline"));
  host.applyRead.mockImplementationOnce(() => {
    throw new Error("workspace unavailable");
  });
  await executor.retryRead(key);
  expect(state.readbackErrors[key]).toBeTruthy();
  expect(state.records[key]?.outcome).toEqual(success);
  expect(host.complete).not.toHaveBeenCalled();
  await executor.retryRead(key);
  expect(host.complete).toHaveBeenCalledOnce();
  expect(io.send).toHaveBeenCalledOnce();
});

it("suspends unloaded actor records and checks consent before reading known success", async () => {
  const { executor, durable, io, state, host } = setup();
  durable.set(key, {
    ...createRecoveryRecord(command, source),
    outcome: success,
  });
  await executor.suspendActor("alex");
  await executor.initializeActor("alex");
  expect(state.records[key]?.requiresAccessConfirmation).toBe(true);
  await executor.resumeAfterAccess(key, commandId, 0);
  await executor.resumeAfterAccess(key, "different", 1);
  expect(io.read).not.toHaveBeenCalled();
  await executor.resumeAfterAccess(key, commandId, 1);
  expect(io.send).not.toHaveBeenCalled();
  expect(host.complete).toHaveBeenCalledOnce();
});

it("drops an obsolete ticket before a queued GET can start", async () => {
  const { executor, durable, io, host } = setup();
  durable.set(key, {
    ...createRecoveryRecord(command, source),
    outcome: success,
  });
  const fetch = vi.fn().mockResolvedValue(snapshot);
  const gate = deferred<void>();
  io.read.mockImplementationOnce(
    async (_context, _signal, _checkpoint, schedule) => {
      await gate.promise;
      try {
        return await schedule(fetch);
      } catch {
        return { kind: "failed", message: "superseded" };
      }
    },
  );
  await executor.initializeActor("alex");
  host.isReadCurrent.mockReturnValue(false);
  gate.resolve();
  await vi.waitFor(() => expect(io.read).toHaveBeenCalledTimes(2));
  expect(fetch).not.toHaveBeenCalled();
  expect(host.applyRead).toHaveBeenCalledTimes(1);
});

it("ignores an obsolete load error after the next actor is ready to save", async () => {
  const { executor, state, durable, session, io } = setup();
  const started = deferred<void>();
  const pending = deferred<Awaited<ReturnType<RecoveryIO["loadActor"]>>>();
  io.loadActor.mockImplementationOnce(() => {
    started.resolve();
    return pending.promise;
  });
  const oldLoad = executor.initializeActor("alex");
  await started.promise;
  session.actorId = "maria";
  session.epoch++;
  const mariaCommand = { ...command, actorId: "maria" };
  const held = createRecoveryRecord(
    { ...mariaCommand, target: { ...target, editVersionId: "held" } },
    source,
  );
  held.requiresAccessConfirmation = true;
  durable.set(held.key, held);
  await executor.initializeActor("maria");
  pending.reject(new Error("old storage read"));
  await oldLoad;
  expect(state.initializedActor).toBe("maria");
  expect(state.records[held.key]?.command.actorId).toBe("maria");
  expect(state.storageError).toBeNull();
  expect(await executor.submit(mariaCommand, source)).toBe("started");
});

it("blocks Save on the current actor's own load error", async () => {
  const { executor, state, session, io } = setup();
  session.actorId = "maria";
  io.loadActor.mockRejectedValueOnce(new Error("unavailable"));
  await executor.initializeActor("maria");
  expect(state.storageError).toBe(
    "Хранилище восстановления недоступно или повреждено",
  );
  expect(await executor.submit({ ...command, actorId: "maria" }, source)).toBe(
    "blocked",
  );
  expect(io.send).not.toHaveBeenCalled();
});

it("waits for a pending insert and refuses logout if it failed", async () => {
  const { executor, io } = setup();
  await executor.initializeActor("alex");
  const inserted = deferred<void>();
  io.insert.mockReturnValueOnce(inserted.promise);
  const submitting = executor.submit(command, source);
  const preparation = executor.prepareActorLogout("alex");
  await Promise.resolve();
  expect(io.loadActor).toHaveBeenCalledTimes(1);
  inserted.reject(new Error("disk"));
  expect(await submitting).toBe("blocked");
  expect(await preparation).toBe(false);
  expect(io.send).not.toHaveBeenCalled();
});

it("permits logout with a durable pending command without stopping the attempt", async () => {
  const { executor, io, state } = setup();
  io.send.mockReturnValueOnce(deferred<typeof success>().promise);
  await executor.initializeActor("alex");
  await executor.submit(command, source);
  expect(await executor.prepareActorLogout("alex")).toBe(true);
  expect(executor.isRunning(key)).toBe(true);
  expect(state.records[key]?.blocks).toEqual([]);
  executor.stopRuntime();
});
