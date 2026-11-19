import { useEditVersionEditor } from "@/composables/edit_version/useEditVersionEditor";
import { useAuthStore } from "@/stores/auth";
import { useEditVersionCommandsStore } from "@/stores/edit_version/editVersionCommands";
import { useEditVersionDraftStore } from "@/stores/edit_version/editVersionDraft";
import { useEditorNavigationStore } from "@/stores/editor_navigation/editorNavigation";
import { useEditorSessionStore } from "@/stores/editor_session/editorSession";
import { useWorkOrdersStore } from "@/stores/work_order/workOrders";
import { useWorkspaceRecoveryStore } from "@/stores/workspace/workspace_recovery/workspaceRecovery";
import { getActivePinia, type Pinia } from "pinia";
import { watch } from "vue";
import {
  createEditorWorkflow,
  type EditorWorkflow,
} from "./createEditorWorkflow";
import {
  bindEditorDependencies,
  bindEditorWorkflow,
} from "./editorRuntimeBinding";
import type { EditorWorkflowPorts } from "./editorWorkflowPorts";

export type EditorRuntime = { workflow: EditorWorkflow; dispose(): void };
const runtimes = new WeakMap<Pinia, EditorRuntime>();
export function installEditorRuntime(pinia: Pinia): EditorRuntime {
  const existing = runtimes.get(pinia);
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
  const detach = workflow.attachRecoveryHost();
  let disposed = false;
  const runtime = {
    workflow,
    dispose() {
      if (disposed) return;
      disposed = true;
      detach();
      for (const stop of stops) stop();
      for (const release of unbind) release();
      runtimes.delete(pinia);
    },
  };
  runtimes.set(pinia, runtime);
  return runtime;
}
export function getEditorRuntime(
  pinia: Pinia | undefined = getActivePinia(),
): EditorRuntime {
  const runtime = pinia && runtimes.get(pinia);
  if (!runtime) throw new Error("Editor runtime must be installed before use");
  return runtime;
}
