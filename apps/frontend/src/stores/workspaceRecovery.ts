import { defineStore } from "pinia";
import { ref } from "vue";
import { fetchWorkspace, saveFeatureGeometry } from "@/api/workOrders";
import { parseApiError } from "@/api/parseApiError";
import {
  freezePendingCommand,
  parseGeometrySaveResult,
  parseWorkspaceResponse,
  type PendingGeometryCommand,
} from "@/contracts/workspace-edit";
import {
  commandContext,
  createRecoveryRecord,
  recoveryKey,
  type RecoveryHost,
  type RecoveryKey,
  type RecoveryRecordV2,
  type RecoverySource,
  type RecoveryStartResult,
} from "@/contracts/workspace-recovery";
import { createRecoveryStorage } from "./workspaceRecoveryStorage";
import { migrateLegacyRecovery } from "./workspaceRecoveryMigration";
import { createRecoveryScheduler } from "./workspaceRecoveryScheduler";
import { AUTO_RETRY_DELAYS_MS, waitForRetry } from "./workspaceRetry";
import { classifySaveFailure } from "./workspaceSaveErrors";

type Phase =
  | "sending"
  | "retry-wait"
  | "unknown"
  | "reading-current"
  | "blocked";
type Run = { controller: AbortController; epoch: number; actorId: string };
export const useWorkspaceRecoveryStore = defineStore(
  "workspaceRecovery",
  () => {
    const records = ref<Record<RecoveryKey, RecoveryRecordV2>>({});
    const phases = ref<Record<RecoveryKey, Phase>>({});
    const readbackErrors = ref<Record<RecoveryKey, string>>({});
    const contextErrors = ref<Record<RecoveryKey, string>>({});
    const storageError = ref<string | null>(null);
    const initializedActor = ref<string | null>(null);
    const storage = createRecoveryStorage(),
      scheduler = createRecoveryScheduler(2);
    let host: RecoveryHost | null = null,
      initialization = 0;
    const runs = new Map<RecoveryKey, Run>(),
      preparing = new Set<RecoveryKey>();
    const writes = new Map<RecoveryKey, Promise<unknown>>();
    const preparationWrites = new Map<RecoveryKey, Promise<void>>();
    const storageFailures = new Set<RecoveryKey>();
    const suspensions = new Map<string, Promise<void>>();
    const suspensionErrors = new Set<string>();
    function getRecord(key: RecoveryKey) {
      return records.value[key] ?? null;
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
      phases.value[key] = "blocked";
      contextErrors.value[key] = "Не удалось сохранить контекст восстановления";
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
            await storage.replace(next, previous.revision);
          } catch (error) {
            if (
              getRecord(key)?.command.request.commandId ===
              next.command.request.commandId
            )
              records.value[key] = { ...next, revision: previous.revision };
            throw error;
          }
          if (
            getRecord(key)?.command.request.commandId ===
            next.command.request.commandId
          )
            records.value[key] = next;
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
        await storage.remove(
          key,
          current.command.request.commandId,
          current.revision,
        );
        if (!active(key, run)) return;
        delete records.value[key];
        delete phases.value[key];
        delete contextErrors.value[key];
        delete readbackErrors.value[key];
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
      phases.value[key] = "reading-current";
      delete readbackErrors.value[key];
      const ticket = host!.reserveRead(commandContext(current.command));
      try {
        const { workOrderId, editVersionId } = current.command.target;
        const workspace = await scheduler.run(
          key,
          run.controller.signal,
          () => {
            if (
              !active(key, run) ||
              !host!.canAccess(commandContext(current.command))
            )
              throw new Error("Session changed");
            return fetchWorkspace(workOrderId, editVersionId);
          },
        );
        if (!active(key, run) || getRecord(key)?.blocks.length) return;
        const accepted = host!.applyRead(
          ticket,
          parseWorkspaceResponse(workspace, workOrderId, editVersionId),
        );
        if (accepted === "superseded" && retrySuperseded) {
          await read(key, run, false);
          return;
        }
        if (accepted !== "applied") {
          readbackErrors.value[key] =
            "Актуальное чтение изменилось. Повторите загрузку.";
          host?.interrupted(key, "readback");
          return;
        }
        await finish(key, run);
      } catch (error) {
        if (!active(key, run)) return;
        const parsed = parseApiError(error);
        if (
          parsed.kind === "api" &&
          ["AUTH_REQUIRED", "USER_INACTIVE", "ROLE_NOT_ALLOWED"].includes(
            parsed.code,
          )
        ) {
          const stop = suspendActor(run.actorId);
          host?.interrupted(key, "session");
          await stop;
          return;
        }
        if (
          (parsed.kind === "api" || parsed.kind === "http") &&
          [401, 403, 404].includes(parsed.status)
        ) {
          await suspend(key);
          return;
        }
        readbackErrors.value[key] =
          "Актуальные данные не загружены. Повторите загрузку.";
        host?.interrupted(key, "readback");
      }
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
      phases.value[key] = "sending";
      const command = current.command;
      try {
        const execute = () => {
          if (!active(key, run) || !host!.canAccess(commandContext(command)))
            throw new Error("Session changed");
          return saveFeatureGeometry(command.target, command.request);
        };
        const response = foreground
          ? await execute()
          : await scheduler.run(key, run.controller.signal, execute);
        if (!active(key, run)) return false;
        const result = parseGeometrySaveResult(
          response,
          command.target,
          command.request.commandId,
        );
        if (
          await update(key, (r) => ({
            ...r,
            outcome: { kind: "succeeded", result },
            readbackRequired: true,
          }))
        )
          await read(key, run);
        return false;
      } catch (error) {
        if (!active(key, run)) return false;
        const failure = classifySaveFailure(error, hadUnknown);
        if (failure.kind === "retryableUnknown") {
          phases.value[key] = "unknown";
          host?.interrupted(key, "unknown");
          return true;
        }
        if (failure.kind === "blocked") {
          if (failure.reason === "access") {
            if (
              ["AUTH_REQUIRED", "USER_INACTIVE", "ROLE_NOT_ALLOWED"].includes(
                failure.code,
              )
            ) {
              const stop = suspendActor(run.actorId);
              host?.interrupted(key, "session");
              await stop;
            } else await suspend(key);
          } else {
            host?.interrupted(key, "blocked");
            await update(key, (r) => ({
              ...r,
              blocks: [...new Set([...r.blocks, failure.reason])],
            }));
            phases.value[key] = "blocked";
            contextErrors.value[key] = failure.code;
          }
          return false;
        }
        host?.interrupted(key, "rejected");
        if (
          await update(key, (r) => ({
            ...r,
            outcome: {
              kind: "rejected",
              error: failure.error,
              needsReadback: failure.kind === "stale",
            },
            readbackRequired: failure.kind === "stale",
          }))
        )
          await read(key, run);
        return false;
      }
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
        storageError.value
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
          phases.value[key] = "retry-wait";
          if (
            !(await waitForRetry(delay, run.controller.signal)) ||
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
        initializedActor.value === actorId &&
        host?.session()?.actorId === actorId
      )
        return;
      stopRuntime();
      const seq = initialization;
      await suspensions.get(actorId);
      await Promise.allSettled([...writes.values()]);
      if (seq !== initialization || host?.session()?.actorId !== actorId)
        return;
      records.value = {};
      phases.value = {};
      readbackErrors.value = {};
      contextErrors.value = {};
      storageFailures.clear();
      storageError.value = suspensionErrors.has(actorId)
        ? "Не удалось сохранить остановку восстановления"
        : null;
      initializedActor.value = null;
      try {
        await migrateLegacyRecovery(actorId, storage);
        const loaded = await storage.list(actorId);
        if (seq !== initialization || host?.session()?.actorId !== actorId)
          return;
        for (const record of loaded.records) {
          record.command = freezePendingCommand(record.command);
          records.value[record.key] = record;
          phases.value[record.key] = record.blocks.length
            ? "blocked"
            : "unknown";
        }
        for (const invalid of loaded.invalid) {
          if (invalid.key) {
            contextErrors.value[invalid.key] =
              "Контекст восстановления повреждён";
            phases.value[invalid.key] = "blocked";
          } else
            storageError.value =
              "Не удалось определить повреждённый контекст восстановления";
        }
        initializedActor.value = actorId;
        for (const key of Object.keys(records.value)) {
          if (!host!.canAccess(commandContext(records.value[key]!.command)))
            await suspend(key);
          else void launch(key);
        }
      } catch {
        storageError.value =
          "Хранилище восстановления недоступно или повреждено";
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
        initializedActor.value !== command.actorId ||
        storageError.value ||
        contextErrors.value[key] ||
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
        await storage.insert(record);
        records.value[key] = record;
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
        await migrateLegacyRecovery(actorId, storage);
        const loaded = await storage.list(actorId);
        if (
          loaded.invalid.length ||
          storageError.value ||
          [...storageFailures].some((key) => JSON.parse(key)[0] === actorId)
        )
          return false;
        return Object.values(records.value)
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
      runs.get(key)?.controller.abort();
      runs.delete(key);
      phases.value[key] = "blocked";
      host?.interrupted(key, "access");
      await update(key, (r) => ({
        ...r,
        blocks: [...new Set([...r.blocks, "access" as const])],
        requiresAccessConfirmation: true,
      }));
    }
    function suspendActor(
      actorId: string,
      workOrderId?: string,
    ): Promise<void> {
      const keys = Object.values(records.value)
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
        await migrateLegacyRecovery(actorId, storage);
        const loaded = await storage.list(actorId);
        for (const record of loaded.records) {
          if (workOrderId && record.command.target.workOrderId !== workOrderId)
            continue;
          if (
            record.requiresAccessConfirmation &&
            record.blocks.includes("access")
          )
            continue;
          await storage.replace(
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
          storageError.value === "Не удалось сохранить остановку восстановления"
        )
          storageError.value = null;
      })().catch(() => {
        suspensionErrors.add(actorId);
        storageError.value = "Не удалось сохранить остановку восстановления";
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
        delete contextErrors.value[key];
        await launch(key);
      }
    }
    function isRunning(key: RecoveryKey) {
      return runs.has(key) || preparing.has(key);
    }
    function hideActor() {
      stopRuntime();
      initializedActor.value = null;
    }
    return {
      records,
      phases,
      readbackErrors,
      contextErrors,
      storageError,
      initializedActor,
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
  },
);
