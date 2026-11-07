import { useWorkOrdersStore } from "@/stores/workOrders";
import { useEditorNavigationStore } from "@/stores/editorNavigation";
import { useEditVersionDraftStore } from "@/stores/editVersionDraft";
import { useEditorSessionStore } from "@/stores/editorSession";
import { useEditVersionCommandsStore } from "@/stores/editVersionCommands";
import { useEditVersionEditor } from "@/composables/useEditVersionEditor";
import { useFeatureBaselineStore } from "@/stores/featureBaseline";
import { isLineStringXY } from "@/contracts/workspace-edit";
import type { WorkspaceResponse } from "@/contracts/work-orders";

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
