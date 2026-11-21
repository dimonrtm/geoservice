import type {
  GeometrySaveResult,
  PendingGeometryCommand,
} from "@/contracts/workspace/workspace-edit";
import type {
  RecoveryContext,
  RecoveryStorageLoad,
} from "@/contracts/workspace/workspace-recovery";
import type { WorkspaceResponse } from "@/contracts/work_order/work-orders";
import type { SnapshotCheckpoint } from "@/composables/edit_version/readEditVersionSnapshot";
import type { SaveFailureDisposition } from "../workspaceSaveErrors";
import type { RecoveryStorage } from "./workspaceRecoveryIndexedDb";
import type { createRecoveryScheduler } from "./workspaceRecoveryScheduler";

export type RecoverySendResult =
  | { kind: "succeeded"; result: GeometrySaveResult }
  | SaveFailureDisposition;
export type RecoveryReadResult =
  | { kind: "succeeded"; workspace: WorkspaceResponse }
  | { kind: "session" | "access" }
  | { kind: "failed"; message: string };

export interface RecoveryIO extends Pick<
  RecoveryStorage,
  "insert" | "replace" | "remove"
> {
  loadActor(actorId: string): Promise<RecoveryStorageLoad>;
  send(
    command: PendingGeometryCommand,
    hadUnknown: boolean,
  ): Promise<RecoverySendResult>;
  read(
    context: RecoveryContext,
    signal: AbortSignal,
    checkpoint: SnapshotCheckpoint,
    schedule: <T>(fetch: () => Promise<T>) => Promise<T>,
  ): Promise<RecoveryReadResult>;
  waitForRetry(delay: number, signal: AbortSignal): Promise<boolean>;
  scheduler: ReturnType<typeof createRecoveryScheduler>;
}

export function isSessionAccessError(code: string): boolean {
  return ["AUTH_REQUIRED", "USER_INACTIVE", "ROLE_NOT_ALLOWED"].includes(code);
}
