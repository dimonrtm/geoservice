import { fetchEditVersionMap } from "@/api/editVersionMap";
import { fetchEditVersionChangeSet } from "@/api/editVersionChangeSet";
import { fetchFeatureBaseline } from "@/api/featureBaseline";
import type { EditVersionMap } from "@/contracts/editVersionMap";
import type { EditVersionChangeSet } from "@/contracts/editVersionChangeSet";
import type { FeatureBaseline } from "@/contracts/featureBaseline";
import { parseWorkspaceResponse } from "@/contracts/workspace-edit";
import type { WorkspaceResponse } from "@/contracts/work-orders";
import { parseApiError } from "@/api/parseApiError";
import { SessionNotConfirmedError } from "@/api/sessionNotConfirmedError";
import { AUTO_RETRY_DELAYS_MS, waitForRetry } from "@/stores/workspaceRetry";

export function projectMap(
  editVersionMap: EditVersionMap,
  changes: EditVersionChangeSet | null,
  baseline: FeatureBaseline | null,
): WorkspaceResponse {
  const version = editVersionMap.workOrder.editVersion;
  const aligned =
    changes?.draftVersionToken === version.draftVersionToken ? changes : null;
  const change = aligned?.changeSet;
  const verified =
    change && baseline?.featureId === change.featureId
      ? { ...change, baselineGeometry: baseline.baselineGeometry }
      : null;
  return {
    workOrder: {
      ...editVersionMap.workOrder,
      editVersion: {
        ...version,
        changeSet: verified,
        hasPersistedChangeSet: aligned?.hasPersistedChangeSet ?? false,
        basicValidation: aligned?.basicValidation ?? null,
      },
    },
  };
}

export type SnapshotCheckpoint = {
  editVersionMap?: EditVersionMap;
  changes?: EditVersionChangeSet;
};

export class SnapshotReadFailure extends Error {
  constructor(stage: "changes" | "baseline") {
    super(
      stage === "changes"
        ? "Не удалось загрузить изменения рабочей версии."
        : "Не удалось загрузить исходную геометрию линии.",
    );
  }
}

type ScheduleRead = <T>(read: () => Promise<T>) => Promise<T>;

// Background recovery can outlive the displayed version. The caller scopes
// the checkpoint to one command, read ticket and authenticated session.
export async function readEditVersionSnapshot(
  workOrderId: string,
  editVersionId: string,
  signal = new AbortController().signal,
  checkpoint: SnapshotCheckpoint = {},
  schedule: ScheduleRead = (read) => read(),
): Promise<WorkspaceResponse> {
  async function readStage<T>(
    stage: "changes" | "baseline",
    fetch: () => Promise<T>,
  ) {
    for (const delay of AUTO_RETRY_DELAYS_MS) {
      await waitForRetry(delay, signal);
      signal.throwIfAborted();
      try {
        const value = await schedule(fetch);
        signal.throwIfAborted();
        return value;
      } catch (error) {
        signal.throwIfAborted();
        if (error instanceof DOMException && error.name === "AbortError")
          throw error;
        const parsed = parseApiError(error);
        if (
          (parsed.kind === "cancelled" &&
            !(error instanceof SessionNotConfirmedError)) ||
          ((parsed.kind === "api" || parsed.kind === "http") &&
            [401, 403, 404, 409].includes(parsed.status))
        )
          throw error;
      }
    }
    throw new SnapshotReadFailure(stage);
  }

  for (;;) {
    signal.throwIfAborted();
    const editVersionMap =
      checkpoint.editVersionMap ??
      (await schedule(() =>
        fetchEditVersionMap(workOrderId, editVersionId, signal),
      ));
    signal.throwIfAborted();
    checkpoint.editVersionMap = editVersionMap;
    const changes =
      checkpoint.changes ??
      (await readStage("changes", () =>
        fetchEditVersionChangeSet(workOrderId, editVersionId, signal),
      ));
    if (
      changes.draftVersionToken !==
      editVersionMap.workOrder.editVersion.draftVersionToken
    ) {
      delete checkpoint.editVersionMap;
      delete checkpoint.changes;
      continue;
    }
    checkpoint.changes = changes;
    const project = (baseline: FeatureBaseline | null) =>
      parseWorkspaceResponse(
        projectMap(editVersionMap, changes, baseline),
        workOrderId,
        editVersionId,
      );
    const changedFeature = changes.changeSet;
    if (!changedFeature) return project(null);
    return readStage("baseline", async () =>
      project(
        await fetchFeatureBaseline(
          workOrderId,
          editVersionId,
          changedFeature.featureId,
          signal,
        ),
      ),
    );
  }
}
