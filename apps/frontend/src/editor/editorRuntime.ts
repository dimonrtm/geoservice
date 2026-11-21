import { useEditVersionEditor } from "@/composables/edit_version/useEditVersionEditor";
import { bindSessionAccessEffects, useAuthStore } from "@/stores/auth";
import { useEditVersionCommandsStore } from "@/stores/edit_version/editVersionCommands";
import { useEditVersionDraftStore } from "@/stores/edit_version/editVersionDraft";
import { useEditorNavigationStore } from "@/stores/editor_navigation/editorNavigation";
import { useEditorSessionStore } from "@/stores/editor_session/editorSession";
import { useWorkOrdersStore } from "@/stores/work_order/workOrders";
import { useWorkspaceRecoveryStore } from "@/stores/workspace/workspace_recovery/workspaceRecovery";
import type { Pinia } from "pinia";
import { watch } from "vue";
import { createEditorWorkflow } from "./createEditorWorkflow";
import {
  bindEditorDependencies,
  bindEditorRuntime,
  findEditorRuntime,
  type EditorRuntime,
  bindEditorWorkflow,
} from "./editorRuntimeBinding";
import type { EditorWorkflowPorts } from "./editorWorkflowPorts";

export { getEditorRuntime, type EditorRuntime } from "./editorRuntimeBinding";
export function installEditorRuntime(pinia: Pinia): EditorRuntime {
  const existing = findEditorRuntime(pinia);
  if (existing) return existing;
  const auth = useAuthStore(pinia),
    workOrders = useWorkOrdersStore(pinia);
  const editorSession = useEditorSessionStore(pinia),
    editVersionDraft = useEditVersionDraftStore(pinia);
  const editVersionCommands = useEditVersionCommandsStore(pinia),
    editorNavigation = useEditorNavigationStore(pinia);
  const recovery = useWorkspaceRecoveryStore(pinia),
    editor = useEditVersionEditor(pinia);
  const stops = new Set<() => void>();
  const ports: EditorWorkflowPorts = {
    auth,
    workOrders,
    editorSession,
    editVersionDraft,
    editVersionCommands,
    editorNavigation,
    recovery,
    editor,
    context: () =>
      auth.user &&
      editorSession.openedWorkOrderId &&
      editorSession.openedEditVersionId
        ? {
            actorId: auth.user.id,
            sessionEpoch: auth.sessionEpoch,
            workOrderId: editorSession.openedWorkOrderId,
            editVersionId: editorSession.openedEditVersionId,
            workspaceGeneration: editorSession.workspaceGeneration,
          }
        : null,
    createCommandId: () => crypto.randomUUID(),
    watchConfirmation(read, changed, options) {
      const stop = watch(read, changed, options);
      const dispose = () => {
        stop();
        stops.delete(dispose);
      };
      stops.add(dispose);
      return dispose;
    },
  };
  const workflow = createEditorWorkflow(ports);
  const unbind = [
    editorSession,
    editVersionDraft,
    editVersionCommands,
    editorNavigation,
  ].flatMap((owner) => [
    bindEditorWorkflow(owner, workflow),
    bindEditorDependencies(owner, ports),
    bindEditorDependencies(owner.$state, ports),
  ]);
  const releaseAccess = bindSessionAccessEffects(auth, {
    beforeAccessLoss: workflow.suspendWorkspaceRecoveryForAccessLoss,
    afterEpochChange: recovery.hideActor,
    prepareExplicitLogin: recovery.suspendActor,
    afterSessionTransition({ previous, current, cause }) {
      const actorChanged = previous.actorId !== current.actorId;
      const sessionReplaced =
        previous.actorId !== null && previous.sessionId !== current.sessionId;
      if (!actorChanged && !sessionReplaced && cause !== "initial-ended")
        return;
      const preserve = cause === "initial-restore" && previous.actorId === null;
      const options = {
        preserveSelectedWorkOrder: preserve,
        preserveOpenedWorkspace: preserve,
      };
      workOrders.reset(options);
      workflow.resetEditor(options);
    },
  });
  const detach = workflow.attachRecoveryHost();
  let disposed = false;
  const runtime: EditorRuntime = {
    workflow,
    sessionAccess: {
      get actorId() {
        return auth.user?.id ?? null;
      },
      get isAuthenticated() {
        return auth.isAuthenticated;
      },
      get canEdit() {
        return auth.isAuthenticated && auth.user?.role === "editor";
      },
      get sessionEpoch() {
        return auth.sessionEpoch;
      },
      logout: () => auth.logout(),
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      releaseAccess();
      detach();
      for (const stop of stops) stop();
      for (const release of unbind) release();
      releaseRuntime();
    },
  };
  const releaseRuntime = bindEditorRuntime(pinia, runtime);
  return runtime;
}
