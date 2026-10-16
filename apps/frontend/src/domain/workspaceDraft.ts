import type { WorkspaceResponse } from "@/contracts/work-orders";
import {
  copyGeometry,
  isLineStringXY,
  isXY,
  type LineStringXY,
} from "@/contracts/workspace-edit";
export type WorkspaceLocalDraft = {
  featureId: string;
  vertexIndex: number;
  sourceGeometry: LineStringXY;
  sourceToken: string;
  candidateGeometry: LineStringXY;
};
export class DraftInputError extends Error {
  readonly code = "INVALID_LOCAL_EDIT";
}
export function createLocalDraft(
  workspace: WorkspaceResponse,
  featureId: string,
  vertexIndex: number,
): WorkspaceLocalDraft {
  const ev = workspace.workOrder.editVersion;
  const geometry = ev.features.features.find(
    (f) => f.id === featureId,
  )?.geometry;
  if (
    !isLineStringXY(geometry) ||
    !Number.isInteger(vertexIndex) ||
    vertexIndex < 1 ||
    vertexIndex >= geometry.coordinates.length - 1 ||
    (ev.changeSet &&
      (ev.changeSet.featureId !== featureId ||
        ev.changeSet.vertexIndex !== vertexIndex))
  )
    throw new DraftInputError("Недоступная вершина линии");
  return {
    featureId,
    vertexIndex,
    sourceToken: ev.draftVersionToken,
    sourceGeometry: copyGeometry(geometry),
    candidateGeometry: copyGeometry(geometry),
  };
}
export function updateLocalVertex(
  draft: WorkspaceLocalDraft,
  xy: [number, number],
): WorkspaceLocalDraft {
  if (!isXY(xy)) throw new DraftInputError("Некорректные координаты");
  const geometry = copyGeometry(draft.candidateGeometry);
  geometry.coordinates[draft.vertexIndex] = [...xy];
  return { ...draft, candidateGeometry: geometry };
}
export function isLocalDraftDirty(draft: WorkspaceLocalDraft): boolean {
  return draft.candidateGeometry.coordinates.some(
    (xy, i) =>
      xy[0] !== draft.sourceGeometry.coordinates[i]?.[0] ||
      xy[1] !== draft.sourceGeometry.coordinates[i]?.[1],
  );
}
