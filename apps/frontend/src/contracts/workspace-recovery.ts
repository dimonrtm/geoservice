import type { WorkspaceResponse } from "./work-orders";
import {
  copyGeometry,
  freezePendingCommand,
  isLineStringXY,
  isSaveRequest,
  nonempty,
  parseGeometrySaveResult,
  ProtocolError,
  record,
  type GeometrySaveResult,
  type LineStringXY,
  type PendingGeometryCommand,
  type SaveRejection,
} from "./workspace-edit";

export type RecoveryKey = string;
export type RecoveryContext = {
  actorId: string;
  workOrderId: string;
  editVersionId: string;
};
export type RecoverySource = {
  geometry: LineStringXY;
  vertexIndex: number;
} | null;
export type RecoveryOutcome =
  | { kind: "unknown" }
  | { kind: "succeeded"; result: GeometrySaveResult }
  | { kind: "rejected"; error: SaveRejection; needsReadback: boolean };
export type RecoveryBlock = "access" | "protocol" | "identity" | "storage";
export type RecoveryRecordV2 = {
  schemaVersion: 2;
  key: RecoveryKey;
  revision: number;
  command: PendingGeometryCommand;
  source: RecoverySource;
  outcome: RecoveryOutcome;
  readbackRequired: boolean;
  blocks: RecoveryBlock[];
  requiresAccessConfirmation: boolean;
};
export type RecoverySession = {
  actorId: string;
  epoch: number;
  canEdit: boolean;
};
export type ReadTicket = {
  key: RecoveryKey;
  sessionEpoch: number;
  generation: number;
};
export type RecoveryApplyResult = "applied" | "superseded" | "blocked";
export type RecoveryStartResult = "started" | "blocked";
export type RecoveryCompletion = {
  record: RecoveryRecordV2;
  sessionEpoch: number;
};
export type RecoveryStorageLoad = {
  records: RecoveryRecordV2[];
  invalid: Array<{ key: RecoveryKey | null; reason: string }>;
};
export type RecoveryHost = {
  session(): RecoverySession | null;
  canAccess(context: RecoveryContext): boolean;
  reserveRead(context: RecoveryContext): ReadTicket;
  applyRead(
    ticket: ReadTicket,
    workspace: WorkspaceResponse,
  ): RecoveryApplyResult;
  complete(completion: RecoveryCompletion): void;
  interrupted(
    key: RecoveryKey,
    reason:
      | "unknown"
      | "readback"
      | "rejected"
      | "access"
      | "blocked"
      | "session",
  ): void;
};
export function commandContext(
  command: PendingGeometryCommand,
): RecoveryContext {
  return {
    actorId: command.actorId,
    workOrderId: command.target.workOrderId,
    editVersionId: command.target.editVersionId,
  };
}
export function recoveryKey(context: RecoveryContext): RecoveryKey {
  return JSON.stringify([
    context.actorId,
    context.workOrderId,
    context.editVersionId,
  ]);
}
export function parseRecoveryRecord(
  value: unknown,
  expectedActorId: string,
): RecoveryRecordV2 {
  if (!record(value) || value.schemaVersion !== 2 || !record(value.command))
    throw new ProtocolError();
  const command = value.command;
  if (
    command.actorId !== expectedActorId ||
    !nonempty(expectedActorId) ||
    !record(command.target) ||
    !nonempty(command.target.workOrderId) ||
    !nonempty(command.target.editVersionId) ||
    !nonempty(command.target.featureId) ||
    !isSaveRequest(command.request) ||
    value.key !==
      recoveryKey({
        actorId: expectedActorId,
        workOrderId: command.target.workOrderId,
        editVersionId: command.target.editVersionId,
      }) ||
    !Number.isSafeInteger(value.revision) ||
    Number(value.revision) < 1 ||
    typeof value.readbackRequired !== "boolean" ||
    typeof value.requiresAccessConfirmation !== "boolean" ||
    !Array.isArray(value.blocks) ||
    value.blocks.some(
      (block) =>
        !["access", "protocol", "identity", "storage"].includes(String(block)),
    ) ||
    !record(value.outcome)
  )
    throw new ProtocolError();
  if (value.source !== null) {
    const source = value.source;
    if (
      !record(source) ||
      !isLineStringXY(source.geometry) ||
      !Number.isInteger(source.vertexIndex) ||
      Number(source.vertexIndex) < 1 ||
      Number(source.vertexIndex) >= source.geometry.coordinates.length - 1 ||
      source.geometry.coordinates.length !==
        command.request.geometry.coordinates.length
    )
      throw new ProtocolError();
  }
  if (value.outcome.kind === "succeeded") {
    parseGeometrySaveResult(
      value.outcome.result,
      {
        workOrderId: command.target.workOrderId,
        editVersionId: command.target.editVersionId,
        featureId: command.target.featureId,
      },
      command.request.commandId,
    );
  } else if (value.outcome.kind === "rejected") {
    const error = value.outcome.error;
    if (
      !record(error) ||
      typeof error.status !== "number" ||
      !nonempty(error.code) ||
      !nonempty(error.message) ||
      !(
        error.correlationId === null || typeof error.correlationId === "string"
      ) ||
      typeof value.outcome.needsReadback !== "boolean"
    )
      throw new ProtocolError();
  } else if (value.outcome.kind !== "unknown") throw new ProtocolError();
  if (value.outcome.kind === "rejected") {
    if (
      value.readbackRequired !== value.outcome.needsReadback ||
      (value.outcome.error &&
        record(value.outcome.error) &&
        value.outcome.error.code === "DRAFT_VERSION_STALE" &&
        !value.readbackRequired)
    )
      throw new ProtocolError();
  } else if (!value.readbackRequired) throw new ProtocolError();
  if (value.requiresAccessConfirmation !== value.blocks.includes("access"))
    throw new ProtocolError();
  return value as RecoveryRecordV2;
}
export function createRecoveryRecord(
  command: PendingGeometryCommand,
  source: Exclude<RecoverySource, null>,
): RecoveryRecordV2 {
  const frozen = freezePendingCommand(
    JSON.parse(JSON.stringify(command)) as PendingGeometryCommand,
  );
  return parseRecoveryRecord(
    {
      schemaVersion: 2,
      key: recoveryKey(commandContext(command)),
      revision: 1,
      command: frozen,
      source: {
        geometry: copyGeometry(source.geometry),
        vertexIndex: source.vertexIndex,
      },
      outcome: { kind: "unknown" },
      readbackRequired: true,
      blocks: [],
      requiresAccessConfirmation: false,
    },
    command.actorId,
  );
}
