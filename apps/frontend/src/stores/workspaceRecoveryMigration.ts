import {
  commandContext,
  recoveryKey,
  type RecoveryOutcome,
  type RecoveryRecordV2,
} from "@/contracts/workspace-recovery";
import { decode, type RecoveryStorage } from "./workspaceRecoveryStorage";

export async function migrateLegacyRecovery(
  actorId: string,
  storage: RecoveryStorage,
): Promise<void> {
  const key = "geoservice:workspace-recovery:v1:" + actorId;
  const raw = sessionStorage.getItem(key);
  if (raw === null) return;
  const old = decode(JSON.parse(raw), actorId);
  let outcome: RecoveryOutcome = { kind: "unknown" };
  if (old.state === "succeeded" || (old.state === "blocked" && old.result))
    outcome = { kind: "succeeded", result: old.result! };
  else if (old.state === "rejected")
    outcome = {
      kind: "rejected",
      error: old.error,
      needsReadback: old.needsReadback,
    };
  const record: RecoveryRecordV2 = {
    schemaVersion: 2,
    revision: 1,
    key: recoveryKey(commandContext(old.command)),
    command: old.command,
    source: null,
    outcome,
    readbackRequired: outcome.kind !== "rejected" || outcome.needsReadback,
    blocks: old.state === "blocked" ? [old.reason] : [],
    requiresAccessConfirmation:
      old.state === "blocked" && old.reason === "access",
  };
  await storage.importLegacy(record, raw);
  // Do not remove a record replaced by another legacy writer while importing.
  if (sessionStorage.getItem(key) !== raw)
    throw new Error("Legacy recovery changed during import");
  sessionStorage.removeItem(key);
  await storage.acknowledgeLegacyRemoval(
    actorId,
    old.command.request.commandId,
  );
}
