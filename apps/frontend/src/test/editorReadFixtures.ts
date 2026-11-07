import type { WorkspaceResponse } from "@/contracts/work-orders";
import { isLineStringXY } from "@/contracts/workspace-edit";

const versions = new Map<
  string,
  WorkspaceResponse["workOrder"]["editVersion"]
>();
export async function fixtureMap(
  read: (workOrderId: string, versionId: string) => Promise<WorkspaceResponse>,
  workOrderId: string,
  versionId: string,
) {
  const value = await read(workOrderId, versionId);
  versions.set(
    JSON.stringify([workOrderId, versionId]),
    value.workOrder.editVersion,
  );
  return value;
}
export function fixtureChangeSet(workOrderId: string, versionId: string) {
  const {
    draftVersionToken,
    hasPersistedChangeSet,
    basicValidation,
    changeSet,
  } = versions.get(JSON.stringify([workOrderId, versionId]))!;
  return {
    draftVersionToken,
    hasPersistedChangeSet,
    basicValidation,
    changeSet,
  };
}
export function fixtureBaseline(
  workOrderId: string,
  versionId: string,
  featureId: string,
) {
  const version = versions.get(JSON.stringify([workOrderId, versionId]))!;
  const baselineGeometry =
    version.changeSet?.baselineGeometry ??
    version.features.features.find((feature) => feature.id === featureId)
      ?.geometry;
  if (!isLineStringXY(baselineGeometry))
    throw new Error("Missing fixture baseline");
  return { featureId, baselineGeometry };
}
