import { useWorkOrdersStore } from "@/stores/work_order/workOrders";
import { useEditorNavigationStore } from "@/stores/editor_navigation/editorNavigation";
import { useEditVersionDraftStore } from "@/stores/edit_version/editVersionDraft";
import { useEditorSessionStore } from "@/stores/editor_session/editorSession";
import { useEditVersionCommandsStore } from "@/stores/edit_version/editVersionCommands";
import { useEditVersionEditor } from "@/composables/edit_version/useEditVersionEditor";
import { useFeatureBaselineStore } from "@/stores/edit_version/featureBaseline";
import { isLineStringXY } from "@/contracts/workspace/workspace-edit";
import type { WorkspaceResponse } from "@/contracts/work_order/work-orders";

export function editorTestContext() {
  const editor = useEditVersionEditor();
  return {
    workOrders: useWorkOrdersStore(),
    editorNavigation: useEditorNavigationStore(),
    editVersionDraft: useEditVersionDraftStore(),
    editorSession: useEditorSessionStore(),
    editVersionCommands: useEditVersionCommandsStore(),
    editor,
    seed(snapshot: WorkspaceResponse | null) {
      if (!snapshot) return editor.reset();
      editor.applyReadback(snapshot);
      const version = snapshot.workOrder.editVersion;
      const line = version.features.features.find((feature) =>
        isLineStringXY(feature.geometry),
      );
      if (!version.changeSet && line && isLineStringXY(line.geometry))
        useFeatureBaselineStore().accept({
          featureId: line.id,
          baselineGeometry: line.geometry,
        });
    },
  };
}
