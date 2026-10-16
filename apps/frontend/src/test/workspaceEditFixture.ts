import type { WorkspaceResponse } from "@/contracts/work-orders";

export const target = {
  workOrderId: "wo-1",
  editVersionId: "ev-1",
  featureId: "line-1",
};
export const commandId = "11111111-1111-4111-8111-111111111111";
export const geometry = {
  type: "LineString" as const,
  coordinates: [
    [65, 44],
    [65.1, 44.1],
    [65.2, 44],
  ] as [number, number][],
};
export const candidate = {
  ...geometry,
  coordinates: [
    [65, 44],
    [65.1, 44.2],
    [65.2, 44],
  ] as [number, number][],
};
export const summary = {
  geometryStatus: "passed" as const,
  aoiStatus: "passed" as const,
  positionalAccuracyStatus: "POSITIONAL_ACCURACY_UNVERIFIED" as const,
  dirtyRelativeToBaseline: "passed" as const,
};
export function workspaceFixture(changed = false): WorkspaceResponse {
  return {
    workOrder: {
      id: target.workOrderId,
      code: "WO-001",
      title: "Работа",
      description: null,
      status: "in_progress",
      scope: {
        aoi: {
          id: "aoi",
          name: "AOI",
          description: null,
          extent: [64, 43, 66, 45],
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [64, 43],
                [66, 43],
                [66, 45],
                [64, 43],
              ],
            ],
          },
        },
      },
      editVersion: {
        id: target.editVersionId,
        status: "open",
        baseNetworkRevision: 1,
        draftVersionToken: changed ? "revision-b" : "revision-a",
        hasPersistedChangeSet: changed,
        basicValidation: changed ? summary : null,
        changeSet: changed
          ? {
              featureId: target.featureId,
              vertexIndex: 1,
              baselineGeometry: structuredClone(geometry),
              operation: "updated",
            }
          : null,
        features: {
          type: "FeatureCollection",
          features: [
            {
              id: target.featureId,
              type: "Feature",
              properties: {},
              geometry: structuredClone(changed ? candidate : geometry),
            },
          ],
        },
        associations: [],
      },
    },
  };
}
export function successFixture(id = commandId) {
  return {
    commandId: id,
    commandState: "succeeded" as const,
    draftVersionToken: "revision-b",
    operation: "updated" as const,
    hasPersistedChangeSet: true,
    updatedFeature: {
      id: target.featureId,
      geometry: structuredClone(candidate),
    },
    basicValidation: summary,
  };
}
