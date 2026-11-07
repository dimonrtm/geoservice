import {
  nonempty,
  ProtocolError,
  record,
  validSummary,
  type BasicValidation,
  type WorkspaceChangeSet,
} from "./workspace-edit";

export type EditVersionChangeSet = {
  draftVersionToken: string;
  hasPersistedChangeSet: boolean;
  basicValidation: BasicValidation | null;
  changeSet: Omit<WorkspaceChangeSet, "baselineGeometry"> | null;
};
export function parseEditVersionChangeSet(
  value: unknown,
): EditVersionChangeSet {
  if (
    !record(value) ||
    !nonempty(value.draftVersionToken) ||
    typeof value.hasPersistedChangeSet !== "boolean" ||
    !validSummary(value.basicValidation, value.hasPersistedChangeSet)
  )
    throw new ProtocolError();
  const change = value.changeSet;
  if (
    value.hasPersistedChangeSet
      ? !record(change) ||
        !nonempty(change.featureId) ||
        !Number.isInteger(change.vertexIndex) ||
        Number(change.vertexIndex) < 1 ||
        change.operation !== "updated" ||
        "baselineGeometry" in change
      : change !== null
  )
    throw new ProtocolError();
  return value as EditVersionChangeSet;
}
