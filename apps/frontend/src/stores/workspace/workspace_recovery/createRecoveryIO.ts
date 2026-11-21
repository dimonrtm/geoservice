import { saveFeatureGeometry } from "@/api/edit_version/editVersions";
import { parseApiError } from "@/api/parseApiError";
import { readEditVersionSnapshot } from "@/composables/edit_version/useEditVersionEditor";
import { SnapshotReadFailure } from "@/composables/edit_version/readEditVersionSnapshot";
import {
  parseGeometrySaveResult,
  parseWorkspaceResponse,
} from "@/contracts/workspace/workspace-edit";
import { classifySaveFailure } from "../workspaceSaveErrors";
import { waitForRetry } from "../workspaceRetry";
import { createRecoveryStorage } from "./workspaceRecoveryStorage";
import { migrateLegacyRecovery } from "./workspaceRecoveryMigration";
import { createRecoveryScheduler } from "./workspaceRecoveryScheduler";
import { isSessionAccessError, type RecoveryIO } from "./workspaceRecoveryIO";

const MAX_CONCURRENT_BACKGROUND_RECOVERY_REQUESTS = 2;

export function createRecoveryIO(): RecoveryIO {
  const storage = createRecoveryStorage();
  return {
    insert: storage.insert,
    replace: storage.replace,
    remove: storage.remove,
    async loadActor(actorId) {
      await migrateLegacyRecovery(actorId, storage);
      return storage.list(actorId);
    },
    async send({ target, request }, hadUnknown) {
      try {
        const response = await saveFeatureGeometry(target, request);
        return {
          kind: "succeeded",
          result: parseGeometrySaveResult(response, target, request.commandId),
        };
      } catch (error) {
        return classifySaveFailure(error, hadUnknown);
      }
    },
    async read({ workOrderId, editVersionId }, signal, checkpoint, schedule) {
      try {
        const response = await readEditVersionSnapshot(
          workOrderId,
          editVersionId,
          signal,
          checkpoint,
          schedule,
        );
        return {
          kind: "succeeded",
          workspace: parseWorkspaceResponse(
            response,
            workOrderId,
            editVersionId,
          ),
        };
      } catch (error) {
        const parsed = parseApiError(error);
        if (parsed.kind === "api" && isSessionAccessError(parsed.code))
          return { kind: "session" };
        if (
          (parsed.kind === "api" || parsed.kind === "http") &&
          [401, 403, 404, 409].includes(parsed.status)
        )
          return { kind: "access" };
        return {
          kind: "failed",
          message:
            error instanceof SnapshotReadFailure
              ? error.message
              : "Актуальные данные не загружены. Повторите загрузку.",
        };
      }
    },
    waitForRetry,
    scheduler: createRecoveryScheduler(
      MAX_CONCURRENT_BACKGROUND_RECOVERY_REQUESTS,
    ),
  };
}
