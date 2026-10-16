import type { WorkspaceResponse } from "./work-orders";

export type LineStringXY = {
  type: "LineString";
  coordinates: [number, number][];
};
export type BasicValidation = {
  geometryStatus: "passed";
  aoiStatus: "passed";
  positionalAccuracyStatus: "POSITIONAL_ACCURACY_UNVERIFIED";
  dirtyRelativeToBaseline: "passed";
};
export type WorkspaceChangeSet = {
  featureId: string;
  vertexIndex: number;
  baselineGeometry: LineStringXY;
  operation: "updated";
};
export type SaveTarget = {
  workOrderId: string;
  editVersionId: string;
  featureId: string;
};
export type GeometrySaveRequest = {
  commandId: string;
  draftVersionToken: string;
  geometry: LineStringXY;
};
export type GeometrySaveResult = {
  commandId: string;
  commandState: "succeeded";
  draftVersionToken: string;
  operation: "updated" | "unchanged";
  hasPersistedChangeSet: boolean;
  updatedFeature: { id: string; geometry: LineStringXY };
  basicValidation: BasicValidation | null;
};
export type PendingGeometryCommand = {
  actorId: string;
  target: SaveTarget;
  request: GeometrySaveRequest;
};
export type SaveRejection = {
  status: number;
  code: string;
  message: string;
  correlationId: string | null;
};
export type WorkspaceRecoveryRecord = {
  schemaVersion: 1;
  command: PendingGeometryCommand;
} & (
  | { state: "unknown" }
  | { state: "succeeded"; result: GeometrySaveResult }
  | { state: "rejected"; error: SaveRejection; needsReadback: boolean }
  | {
      state: "blocked";
      reason: "access" | "protocol" | "identity";
      result?: GeometrySaveResult;
    }
);
export class ProtocolError extends Error {
  constructor() {
    super(
      "Некорректный ответ или контекст восстановления рабочего пространства",
    );
  }
}
export function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
export function nonempty(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}
export function isUuid(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(value)
  );
}
export function isXY(value: unknown): value is [number, number] {
  return (
    Array.isArray(value) &&
    value.length === 2 &&
    value.every((v) => typeof v === "number" && Number.isFinite(v)) &&
    Math.abs(value[0]) <= 180 &&
    Math.abs(value[1]) <= 90
  );
}
export function isLineStringXY(value: unknown): value is LineStringXY {
  return (
    record(value) &&
    value.type === "LineString" &&
    Array.isArray(value.coordinates) &&
    value.coordinates.length >= 2 &&
    value.coordinates.every(isXY)
  );
}
export function isSaveRequest(value: unknown): value is GeometrySaveRequest {
  return (
    record(value) &&
    Object.keys(value).length === 3 &&
    isUuid(value.commandId) &&
    nonempty(value.draftVersionToken) &&
    isLineStringXY(value.geometry)
  );
}
function validSummary(value: unknown, changed: boolean): boolean {
  return changed
    ? record(value) &&
        value.geometryStatus === "passed" &&
        value.aoiStatus === "passed" &&
        value.positionalAccuracyStatus === "POSITIONAL_ACCURACY_UNVERIFIED" &&
        value.dirtyRelativeToBaseline === "passed"
    : value === null;
}
export function parseGeometrySaveResult(
  value: unknown,
  target: SaveTarget,
  commandId: string,
): GeometrySaveResult {
  if (
    !record(value) ||
    !isUuid(value.commandId) ||
    value.commandId !== commandId ||
    value.commandState !== "succeeded" ||
    !nonempty(value.draftVersionToken) ||
    typeof value.hasPersistedChangeSet !== "boolean" ||
    value.operation !==
      (value.hasPersistedChangeSet ? "updated" : "unchanged") ||
    !validSummary(value.basicValidation, value.hasPersistedChangeSet) ||
    !record(value.updatedFeature) ||
    value.updatedFeature.id !== target.featureId ||
    !isLineStringXY(value.updatedFeature.geometry)
  )
    throw new ProtocolError();
  return value as GeometrySaveResult;
}
export function parseWorkspaceResponse(
  value: unknown,
  workOrderId: string,
  editVersionId: string,
): WorkspaceResponse {
  if (!record(value) || !record(value.workOrder)) throw new ProtocolError();
  const wo = value.workOrder;
  const ev = wo.editVersion;
  if (
    wo.id !== workOrderId ||
    !record(ev) ||
    ev.id !== editVersionId ||
    ev.status !== "open" ||
    !nonempty(ev.draftVersionToken) ||
    typeof ev.hasPersistedChangeSet !== "boolean" ||
    !validSummary(ev.basicValidation, ev.hasPersistedChangeSet) ||
    !record(ev.features) ||
    ev.features.type !== "FeatureCollection" ||
    !Array.isArray(ev.features.features) ||
    !Array.isArray(ev.associations) ||
    !record(wo.scope) ||
    !record(wo.scope.aoi)
  )
    throw new ProtocolError();
  const features = ev.features.features;
  if (
    !features.every(
      (f) =>
        record(f) &&
        nonempty(f.id) &&
        f.type === "Feature" &&
        record(f.geometry) &&
        nonempty(f.geometry.type) &&
        record(f.properties),
    )
  )
    throw new ProtocolError();
  if (
    new Set(features.map((f) => (f as Record<string, unknown>).id)).size !==
    features.length
  )
    throw new ProtocolError();
  if (!ev.hasPersistedChangeSet) {
    if (ev.changeSet !== null) throw new ProtocolError();
  } else {
    const cs = ev.changeSet;
    if (
      !record(cs) ||
      !nonempty(cs.featureId) ||
      cs.operation !== "updated" ||
      !Number.isInteger(cs.vertexIndex) ||
      !isLineStringXY(cs.baselineGeometry)
    )
      throw new ProtocolError();
    const index = cs.vertexIndex as number;
    const baseline = cs.baselineGeometry.coordinates;
    const feature = features.find((f) => record(f) && f.id === cs.featureId);
    if (
      !record(feature) ||
      !isLineStringXY(feature.geometry) ||
      index < 1 ||
      index >= baseline.length - 1 ||
      feature.geometry.coordinates.length !== baseline.length
    )
      throw new ProtocolError();
    const current = feature.geometry.coordinates;
    const differences = baseline.flatMap((xy, i) =>
      xy[0] !== current[i]?.[0] || xy[1] !== current[i]?.[1] ? [i] : [],
    );
    if (differences.length !== 1 || differences[0] !== index)
      throw new ProtocolError();
  }
  return value as WorkspaceResponse;
}

export function copyGeometry(geometry: LineStringXY): LineStringXY {
  return {
    type: "LineString",
    coordinates: geometry.coordinates.map(([x, y]) => [x, y]),
  };
}

export function freezePendingCommand(
  command: PendingGeometryCommand,
): PendingGeometryCommand {
  for (const xy of command.request.geometry.coordinates) Object.freeze(xy);
  Object.freeze(command.request.geometry.coordinates);
  Object.freeze(command.request.geometry);
  Object.freeze(command.request);
  Object.freeze(command.target);
  return Object.freeze(command);
}
