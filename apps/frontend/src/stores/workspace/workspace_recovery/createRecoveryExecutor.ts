import type { SnapshotCheckpoint } from "@/composables/edit_version/readEditVersionSnapshot";
import {
  freezePendingCommand,
  type PendingGeometryCommand,
} from "@/contracts/workspace/workspace-edit";
import {
  commandContext,
  createRecoveryRecord,
  recoveryKey,
  type RecoveryHost,
  type RecoveryApplyResult,
  type RecoveryKey,
  type RecoveryRecordV2,
  type RecoverySource,
  type RecoveryStartResult,
  type ReadTicket,
} from "@/contracts/workspace/workspace-recovery";
import {
  isSessionAccessError,
  type RecoverySendResult,
  type RecoveryIO,
} from "./workspaceRecoveryIO";
import { AUTO_RETRY_DELAYS_MS } from "../workspaceRetry";

type Phase =
  | "sending"
  | "retry-wait"
  | "unknown"
  | "reading-current"
  | "blocked";
type Run = { controller: AbortController; epoch: number; actorId: string };
export type RecoveryState = {
  records: Record<RecoveryKey, RecoveryRecordV2>;
  phases: Record<RecoveryKey, Phase>;
  readbackErrors: Record<RecoveryKey, string>;
  contextErrors: Record<RecoveryKey, string>;
  storageError: string | null;
  initializedActor: string | null;
};

export function createRecoveryState(): RecoveryState {
  return {
    records: {},
    phases: {},
    readbackErrors: {},
    contextErrors: {},
    storageError: null,
    initializedActor: null,
  };
}

export function createRecoveryExecutor(state: RecoveryState, io: RecoveryIO) {
  let host: RecoveryHost | null = null,
    initialization = 0;
  const runs = new Map<RecoveryKey, Run>(),
    preparing = new Set<RecoveryKey>();
  const writes = new Map<RecoveryKey, Promise<unknown>>();
  const readbacks = new Map<
    RecoveryKey,
    {
      commandId: string;
      ticket: ReadTicket;
      checkpoint: SnapshotCheckpoint;
    }
  >();
  const preparationWrites = new Map<RecoveryKey, Promise<void>>();
  const storageFailures = new Set<RecoveryKey>();
  const suspensions = new Map<string, Promise<void>>();
  const suspensionErrors = new Set<string>();
  function getRecord(key: RecoveryKey) {
    return state.records[key] ?? null;
  }
  function active(key: RecoveryKey, run: Run): boolean {
    const session = host?.session();
    return (
      runs.get(key) === run &&
      !run.controller.signal.aborted &&
      session?.actorId === run.actorId &&
      session.epoch === run.epoch &&
      session.canEdit
    );
  }
  function failStorage(key: RecoveryKey) {
    storageFailures.add(key);
    host?.interrupted(key, "blocked");
    state.phases[key] = "blocked";
    state.contextErrors[key] = "Не удалось сохранить контекст восстановления";
    const current = getRecord(key);
    if (current && !current.blocks.includes("storage"))
      current.blocks.push("storage");
  }
  async function update(
    key: RecoveryKey,
    change: (r: RecoveryRecordV2) => RecoveryRecordV2,
  ): Promise<boolean> {
    const previousWrite = writes.get(key) ?? Promise.resolve();
    const write = previousWrite
      .catch(() => {})
      .then(async () => {
        const previous = getRecord(key);
        if (!previous) return false;
        const next = change(
          JSON.parse(JSON.stringify(previous)) as RecoveryRecordV2,
        );
        next.revision = previous.revision + 1;
        next.command = freezePendingCommand(next.command);
        try {
          await io.replace(next, previous.revision);
        } catch (error) {
          if (
            getRecord(key)?.command.request.commandId ===
            next.command.request.commandId
          )
            state.records[key] = { ...next, revision: previous.revision };
          throw error;
        }
        if (
          getRecord(key)?.command.request.commandId ===
          next.command.request.commandId
        )
          state.records[key] = next;
        return true;
      });
    writes.set(key, write);
    try {
      return await write;
    } catch {
      failStorage(key);
      return false;
    } finally {
      if (writes.get(key) === write) writes.delete(key);
    }
  }
  function stopRuntime() {
    initialization++;
    for (const run of runs.values()) run.controller.abort();
    runs.clear();
    readbacks.clear();
  }
  function bindHost(value: RecoveryHost): () => void {
    host = value;
    return () => {
      if (host === value) {
        stopRuntime();
        host = null;
      }
    };
  }
  async function finish(key: RecoveryKey, run: Run) {
    if (!active(key, run)) return;
    const current = getRecord(key);
    if (!current || current.blocks.length) return;
    try {
      await io.remove(key, current.command.request.commandId, current.revision);
      if (!active(key, run)) return;
      delete state.records[key];
      delete state.phases[key];
      delete state.contextErrors[key];
      delete state.readbackErrors[key];
      host?.complete({ record: current, sessionEpoch: run.epoch });
    } catch {
      failStorage(key);
    }
  }
  async function read(key: RecoveryKey, run: Run, retrySuperseded = true) {
    const current = getRecord(key);
    if (!current || current.blocks.length || !active(key, run)) return;
    if (current.outcome.kind === "rejected" && !current.readbackRequired) {
      await finish(key, run);
      return;
    }
    state.phases[key] = "reading-current";
    delete state.readbackErrors[key];
    const context = commandContext(current.command);
    const commandId = current.command.request.commandId;
    const previous = readbacks.get(key);
    const readback =
      previous &&
      previous.commandId === commandId &&
      previous.ticket.sessionEpoch === run.epoch &&
      host!.isReadCurrent(previous.ticket)
        ? previous
        : { commandId, ticket: host!.reserveRead(context), checkpoint: {} };
    readbacks.set(key, readback);
    const { ticket } = readback;
    const response = await io.read(
      context,
      run.controller.signal,
      readback.checkpoint,
      (fetch) =>
        io.scheduler.run(key, run.controller.signal, () => {
          if (
            !active(key, run) ||
            getRecord(key)?.command.request.commandId !== commandId ||
            !host!.canAccess(context) ||
            !host!.isReadCurrent(ticket)
          )
            throw new DOMException("Recovery read superseded", "AbortError");
          return fetch();
        }),
    );
    if (
      !active(key, run) ||
      getRecord(key)?.command.request.commandId !== commandId ||
      getRecord(key)?.blocks.length
    )
      return;
    if (!host!.canAccess(context) || response.kind === "access") {
      await suspend(key);
      return;
    }
    if (response.kind === "session") {
      const stop = suspendActor(run.actorId);
      host?.interrupted(key, "session");
      await stop;
      return;
    }
    if (response.kind === "succeeded") {
      readbacks.delete(key);
      let accepted: RecoveryApplyResult | "failed";
      try {
        accepted = host!.applyRead(ticket, response.workspace);
      } catch {
        if (!active(key, run)) return;
        if (!host!.canAccess(context)) {
          await suspend(key);
          return;
        }
        accepted = host!.isReadCurrent(ticket) ? "failed" : "superseded";
      }
      if (accepted === "applied") {
        await finish(key, run);
        return;
      }
      if (accepted === "superseded" && retrySuperseded) {
        await read(key, run, false);
        return;
      }
      state.readbackErrors[key] =
        accepted === "failed"
          ? "Актуальные данные не загружены. Повторите загрузку."
          : "Актуальное чтение изменилось. Повторите загрузку.";
    } else if (response.kind === "failed") {
      if (!host!.isReadCurrent(ticket)) {
        readbacks.delete(key);
        if (retrySuperseded) {
          await read(key, run, false);
          return;
        }
      }
      state.readbackErrors[key] = response.message;
    }
    host?.interrupted(key, "readback");
  }
  async function send(
    key: RecoveryKey,
    run: Run,
    hadUnknown: boolean,
    foreground: boolean,
  ): Promise<boolean> {
    const current = getRecord(key);
    if (!current || !active(key, run) || current.blocks.length) return false;
    if (!host!.canAccess(commandContext(current.command))) {
      await suspend(key);
      return false;
    }
    state.phases[key] = "sending";
    const command = current.command;
    const execute = () => {
      if (!active(key, run) || !host!.canAccess(commandContext(command)))
        throw new Error("Session changed");
      return io.send(command, hadUnknown);
    };
    let response: RecoverySendResult;
    try {
      response = foreground
        ? await execute()
        : await io.scheduler.run(key, run.controller.signal, execute);
    } catch {
      if (!active(key, run)) return false;
      response = {
        kind: "blocked",
        reason: "protocol",
        code: "SAVE_OUTCOME_UNCONFIRMED",
      };
    }
    if (!active(key, run)) return false;
    if (response.kind === "succeeded") {
      const { result } = response;
      if (
        await update(key, (r) => ({
          ...r,
          outcome: { kind: "succeeded", result },
          readbackRequired: true,
        }))
      )
        await read(key, run);
      return false;
    }
    if (response.kind === "retryableUnknown") {
      state.phases[key] = "unknown";
      host?.interrupted(key, "unknown");
      return true;
    }
    if (response.kind === "blocked") {
      if (response.reason === "access") {
        if (isSessionAccessError(response.code)) {
          const stop = suspendActor(run.actorId);
          host?.interrupted(key, "session");
          await stop;
        } else await suspend(key);
      } else {
        host?.interrupted(key, "blocked");
        await update(key, (r) => ({
          ...r,
          blocks: [...new Set([...r.blocks, response.reason])],
        }));
        state.phases[key] = "blocked";
        state.contextErrors[key] = response.code;
      }
      return false;
    }
    host?.interrupted(key, "rejected");
    if (
      await update(key, (r) => ({
        ...r,
        outcome: {
          kind: "rejected",
          error: response.error,
          needsReadback: response.kind === "stale",
        },
        readbackRequired: response.kind === "stale",
      }))
    )
      await read(key, run);
    return false;
  }
  async function launch(key: RecoveryKey, initial = false) {
    const current = getRecord(key),
      session = host?.session();
    if (
      runs.has(key) ||
      !current ||
      current.blocks.length ||
      current.requiresAccessConfirmation ||
      !session?.canEdit ||
      session.actorId !== current.command.actorId ||
      state.storageError
    )
      return;
    if (!host!.canAccess(commandContext(current.command))) return;
    const run: Run = {
      controller: new AbortController(),
      epoch: session.epoch,
      actorId: session.actorId,
    };
    runs.set(key, run);
    let retryInitial = false;
    try {
      if (current.outcome.kind !== "unknown") {
        await read(key, run);
        return;
      }
      if (initial) {
        retryInitial = await send(key, run, false, true);
        return;
      }
      for (const delay of AUTO_RETRY_DELAYS_MS) {
        if (!active(key, run)) return;
        state.phases[key] = "retry-wait";
        if (
          !(await io.waitForRetry(delay, run.controller.signal)) ||
          !active(key, run)
        )
          return;
        if (!(await send(key, run, true, false))) return;
      }
    } finally {
      if (runs.get(key) === run) {
        runs.delete(key);
        if (retryInitial)
          queueMicrotask(() => {
            void launch(key);
          });
      }
    }
  }
  async function initializeActor(actorId: string) {
    if (
      state.initializedActor === actorId &&
      host?.session()?.actorId === actorId
    )
      return;
    stopRuntime();
    const generation = initialization;
    const isCurrentLoad = () =>
      generation === initialization && host?.session()?.actorId === actorId;
    await suspensions.get(actorId);
    await Promise.allSettled([...writes.values()]);
    if (!isCurrentLoad()) return;
    state.records = {};
    state.phases = {};
    state.readbackErrors = {};
    state.contextErrors = {};
    storageFailures.clear();
    state.storageError = suspensionErrors.has(actorId)
      ? "Не удалось сохранить остановку восстановления"
      : null;
    state.initializedActor = null;
    try {
      const loaded = await io.loadActor(actorId);
      if (!isCurrentLoad()) return;
      for (const record of loaded.records) {
        record.command = freezePendingCommand(record.command);
        state.records[record.key] = record;
        state.phases[record.key] = record.blocks.length ? "blocked" : "unknown";
      }
      for (const invalid of loaded.invalid) {
        if (invalid.key) {
          state.contextErrors[invalid.key] =
            "Контекст восстановления повреждён";
          state.phases[invalid.key] = "blocked";
        } else
          state.storageError =
            "Не удалось определить повреждённый контекст восстановления";
      }
      state.initializedActor = actorId;
      for (const key of Object.keys(state.records)) {
        if (!host!.canAccess(commandContext(state.records[key]!.command)))
          await suspend(key);
        else void launch(key);
      }
    } catch {
      if (!isCurrentLoad()) return;
      state.storageError = "Хранилище восстановления недоступно или повреждено";
    }
  }
  async function submit(
    command: PendingGeometryCommand,
    source: Exclude<RecoverySource, null>,
  ): Promise<RecoveryStartResult> {
    const key = recoveryKey(commandContext(command)),
      session = host?.session();
    if (
      !session?.canEdit ||
      session.actorId !== command.actorId ||
      state.initializedActor !== command.actorId ||
      state.storageError ||
      state.contextErrors[key] ||
      getRecord(key) ||
      preparing.has(key) ||
      !host!.canAccess(commandContext(command))
    )
      return "blocked";
    preparing.add(key);
    let prepared!: () => void;
    preparationWrites.set(
      key,
      new Promise<void>((resolve) => (prepared = resolve)),
    );
    try {
      const record = createRecoveryRecord(command, source);
      await io.insert(record);
      state.records[key] = record;
      if (
        host?.session()?.actorId !== command.actorId ||
        host.session()?.epoch !== session.epoch
      ) {
        await suspend(key);
        return "blocked";
      }
      void launch(key, true);
      return "started";
    } catch {
      failStorage(key);
      return "blocked";
    } finally {
      preparing.delete(key);
      preparationWrites.delete(key);
      prepared();
    }
  }
  async function prepareActorLogout(actorId: string): Promise<boolean> {
    await Promise.all([...preparationWrites.values()]);
    await Promise.allSettled([...writes.values()]);
    try {
      const loaded = await io.loadActor(actorId);
      if (
        loaded.invalid.length ||
        state.storageError ||
        [...storageFailures].some((key) => JSON.parse(key)[0] === actorId)
      )
        return false;
      return Object.values(state.records)
        .filter((record) => record.command.actorId === actorId)
        .every((record) => {
          const durable = loaded.records.find((r) => r.key === record.key);
          return (
            !record.blocks.includes("storage") &&
            !!durable &&
            JSON.stringify(durable.command) === JSON.stringify(record.command)
          );
        });
    } catch {
      return false;
    }
  }
  async function retry(key: RecoveryKey) {
    if (getRecord(key)?.outcome.kind === "unknown") await launch(key);
  }
  async function retryRead(key: RecoveryKey) {
    if (getRecord(key)?.outcome.kind !== "unknown") await launch(key);
  }
  async function suspend(key: RecoveryKey) {
    readbacks.delete(key);
    runs.get(key)?.controller.abort();
    runs.delete(key);
    state.phases[key] = "blocked";
    host?.interrupted(key, "access");
    await update(key, (r) => ({
      ...r,
      blocks: [...new Set([...r.blocks, "access" as const])],
      requiresAccessConfirmation: true,
    }));
  }
  function suspendActor(actorId: string, workOrderId?: string): Promise<void> {
    const keys = Object.values(state.records)
      .filter(
        (r) =>
          r.command.actorId === actorId &&
          (!workOrderId || r.command.target.workOrderId === workOrderId),
      )
      .map((r) => r.key);
    for (const key of keys) {
      runs.get(key)?.controller.abort();
      runs.delete(key);
    }
    const pending = keys.map((key) => suspend(key));
    const previous = suspensions.get(actorId);
    const operation = (async () => {
      await previous;
      await Promise.all(pending);
      const loaded = await io.loadActor(actorId);
      for (const record of loaded.records) {
        if (workOrderId && record.command.target.workOrderId !== workOrderId)
          continue;
        if (
          record.requiresAccessConfirmation &&
          record.blocks.includes("access")
        )
          continue;
        await io.replace(
          {
            ...record,
            revision: record.revision + 1,
            blocks: [...new Set([...record.blocks, "access" as const])],
            requiresAccessConfirmation: true,
          },
          record.revision,
        );
      }
      suspensionErrors.delete(actorId);
      if (
        state.storageError === "Не удалось сохранить остановку восстановления"
      )
        state.storageError = null;
    })().catch(() => {
      suspensionErrors.add(actorId);
      state.storageError = "Не удалось сохранить остановку восстановления";
    });
    suspensions.set(actorId, operation);
    return operation;
  }
  async function resumeAfterAccess(
    key: RecoveryKey,
    commandId: string,
    sessionEpoch: number,
  ) {
    const current = getRecord(key),
      session = host?.session();
    if (
      !current ||
      !session?.canEdit ||
      session.epoch !== sessionEpoch ||
      current.command.actorId !== session.actorId ||
      current.command.request.commandId !== commandId ||
      !host!.canAccess(commandContext(current.command))
    )
      return;
    if (
      await update(key, (r) => ({
        ...r,
        blocks: r.blocks.filter((b) => b !== "access"),
        requiresAccessConfirmation: false,
      }))
    ) {
      delete state.contextErrors[key];
      await launch(key);
    }
  }
  function isRunning(key: RecoveryKey) {
    return runs.has(key) || preparing.has(key);
  }
  function hideActor() {
    stopRuntime();
    state.initializedActor = null;
  }
  return {
    getRecord,
    bindHost,
    initializeActor,
    submit,
    prepareActorLogout,
    retry,
    retryRead,
    suspend,
    suspendActor,
    resumeAfterAccess,
    stopRuntime,
    isRunning,
    hideActor,
  };
}
