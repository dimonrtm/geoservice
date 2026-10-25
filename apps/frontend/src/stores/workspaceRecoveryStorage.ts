import {
  record,
  nonempty,
  isSaveRequest,
  parseGeometrySaveResult,
  type WorkspaceRecoveryRecord,
} from "@/contracts/workspace-edit";
export {
  createRecoveryStorage,
  RecoveryStorageError,
  type RecoveryStorage,
} from "./workspaceRecoveryIndexedDb";
export type RecoveryReadResult =
  | { kind: "empty" | "invalid" | "unavailable" }
  | { kind: "record"; record: WorkspaceRecoveryRecord };

const PREFIX = "geoservice:workspace-recovery:v1:";
export function decode(
  value: unknown,
  actorId: string,
): WorkspaceRecoveryRecord {
  if (!record(value) || value.schemaVersion !== 1 || !record(value.command))
    throw new Error("record");
  const command = value.command;
  if (
    command.actorId !== actorId ||
    !record(command.target) ||
    !nonempty(command.target.workOrderId) ||
    !nonempty(command.target.editVersionId) ||
    !nonempty(command.target.featureId) ||
    !isSaveRequest(command.request)
  )
    throw new Error("command");
  const target = {
    workOrderId: command.target.workOrderId,
    editVersionId: command.target.editVersionId,
    featureId: command.target.featureId,
  };
  if (value.state === "succeeded")
    parseGeometrySaveResult(value.result, target, command.request.commandId);
  else if (value.state === "rejected") {
    const e = value.error;
    if (
      !record(e) ||
      typeof e.status !== "number" ||
      !nonempty(e.code) ||
      !nonempty(e.message) ||
      !(e.correlationId === null || typeof e.correlationId === "string") ||
      typeof value.needsReadback !== "boolean"
    )
      throw new Error("rejection");
  } else if (value.state === "blocked") {
    if (!["access", "protocol", "identity"].includes(String(value.reason)))
      throw new Error("reason");
    if (value.result !== undefined)
      parseGeometrySaveResult(value.result, target, command.request.commandId);
  } else if (value.state !== "unknown") throw new Error("state");
  return value as WorkspaceRecoveryRecord;
}
export function readRecoveryRecord(actorId: string): RecoveryReadResult {
  let raw: string | null;
  try {
    raw = window.sessionStorage.getItem(PREFIX + actorId);
  } catch {
    return { kind: "unavailable" };
  }
  if (raw === null) return { kind: "empty" };
  try {
    return { kind: "record", record: decode(JSON.parse(raw), actorId) };
  } catch {
    return { kind: "invalid" };
  }
}
export function writeRecoveryRecord(value: WorkspaceRecoveryRecord): boolean {
  try {
    const parsed = decode(value, value.command.actorId);
    const previous = readRecoveryRecord(value.command.actorId);
    if (previous.kind === "invalid" || previous.kind === "unavailable")
      return false;
    if (
      previous.kind === "record" &&
      JSON.stringify(previous.record.command) !== JSON.stringify(parsed.command)
    )
      return false;
    window.sessionStorage.setItem(
      PREFIX + value.command.actorId,
      JSON.stringify(parsed),
    );
    return true;
  } catch {
    return false;
  }
}
export function removeRecoveryRecord(
  actorId: string,
  commandId: string,
): boolean {
  const previous = readRecoveryRecord(actorId);
  if (previous.kind === "empty") return true;
  if (
    previous.kind !== "record" ||
    previous.record.command.request.commandId !== commandId
  )
    return false;
  try {
    window.sessionStorage.removeItem(PREFIX + actorId);
    return true;
  } catch {
    return false;
  }
}

// Initial auth restoration can fail before the caller knows the actor.
export function blockStoredRecoveriesForAccessLoss(actorId?: string): boolean {
  try {
    const actors = actorId
      ? [actorId]
      : Object.keys(window.sessionStorage)
          .filter((k) => k.startsWith(PREFIX))
          .map((k) => k.slice(PREFIX.length));
    let ok = true;
    for (const actor of actors) {
      const stored = readRecoveryRecord(actor);
      if (stored.kind === "empty") continue;
      if (stored.kind !== "record") {
        ok = false;
        continue;
      }
      const previous = stored.record;
      const result =
        previous.state === "succeeded"
          ? previous.result
          : previous.state === "blocked"
            ? previous.result
            : undefined;
      if (
        !writeRecoveryRecord({
          schemaVersion: 1,
          command: previous.command,
          state: "blocked",
          reason: "access",
          ...(result ? { result } : {}),
        })
      )
        ok = false;
    }
    return ok;
  } catch {
    return false;
  }
}
