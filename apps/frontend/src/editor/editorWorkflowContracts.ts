import type { NavigationContext } from "@/domain/workspace/workspaceNavigation";

export type EditorContext = {
  actorId: string;
  sessionEpoch: number;
  workOrderId: string;
  editVersionId: string;
  workspaceGeneration: number;
};
export type DraftIdentity = EditorContext & { draftGeneration: number };
export type SaveAttempt = {
  context: EditorContext;
  draftIdentity: DraftIdentity | null;
  commandId: string;
  navigationId: string | null;
};
export type SaveStartResult =
  | { kind: "started"; commandId: string }
  | { kind: "not-started" }
  | { kind: "superseded" };

export function sameEditorContext(a: EditorContext, b: EditorContext): boolean {
  return (
    a.actorId === b.actorId &&
    a.sessionEpoch === b.sessionEpoch &&
    a.workOrderId === b.workOrderId &&
    a.editVersionId === b.editVersionId &&
    a.workspaceGeneration === b.workspaceGeneration
  );
}
export function sameDraft(a: DraftIdentity | null, b: DraftIdentity): boolean {
  return (
    !!a && sameEditorContext(a, b) && a.draftGeneration === b.draftGeneration
  );
}
export function matchesNavigation(
  n: NavigationContext,
  attempt: SaveAttempt,
): boolean {
  return (
    n.id === attempt.navigationId &&
    n.actorId === attempt.context.actorId &&
    n.sessionEpoch === attempt.context.sessionEpoch &&
    n.sourceKey ===
      JSON.stringify([
        attempt.context.actorId,
        attempt.context.workOrderId,
        attempt.context.editVersionId,
      ])
  );
}
