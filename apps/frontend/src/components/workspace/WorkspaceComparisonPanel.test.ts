import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { expect, it, vi } from "vitest";
import { nextTick } from "vue";
import { installEditorRuntime, getEditorRuntime } from "@/editor/editorRuntime";
import { editorTestContext } from "@/test/editorTestContext";
import { useAuthStore } from "@/stores/auth";
import { target, workspaceFixture } from "@/test/workspaceEditFixture";
import WorkspaceComparisonPanel from "./WorkspaceComparisonPanel.vue";

it("preview goes through its owner and hiding preserves the comparison", async () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const runtime = installEditorRuntime(pinia);
  useAuthStore().token = "token";
  useAuthStore().user = { id: "actor", role: "editor", email: "a@local" };
  const s = editorTestContext();
  s.seed(workspaceFixture());
  s.workOrders.selectedWorkOrderId = s.editorSession.openedWorkOrderId =
    target.workOrderId;
  s.editorSession.openedEditVersionId = target.editVersionId;
  const key = s.editVersionCommands.recoveryKey!;
  s.editVersionCommands.staleComparisons[key] = {
    source: null,
    commandId: "stale",
    featureId: target.featureId,
    candidate: {
      type: "LineString",
      coordinates: [
        [65, 44],
        [65.1, 44.3],
        [65.2, 44],
      ],
    },
  };
  const show = vi.spyOn(s.editVersionCommands, "showComparisonPreview");
  const hide = vi.spyOn(s.editVersionCommands, "hideComparisonPreview");
  const wrapper = mount(WorkspaceComparisonPanel, {
    global: { plugins: [pinia] },
  });
  const buttons = wrapper.findAll("button");
  expect(buttons[0]!.attributes("disabled")).toBeDefined();
  await buttons[1]!.trigger("click");
  expect(s.editVersionCommands.comparisonPreview).toBe("candidate");
  expect(show).toHaveBeenCalledWith("candidate");
  await buttons[2]!.trigger("click");
  expect(s.editVersionCommands.comparisonPreview).toBe("current");
  s.seed(workspaceFixture(true));
  await nextTick();
  expect(s.editVersionCommands.previewGeometry?.coordinates[1]).toEqual([
    65.1, 44.2,
  ]);
  expect(wrapper.text()).toContain("65.1, 44.2");
  await buttons[3]!.trigger("click");
  expect(hide).toHaveBeenCalledOnce();
  expect(s.editVersionCommands.comparisonPreview).toBeNull();
  expect(s.editVersionCommands.staleComparisons[key]).toBeDefined();
  s.editVersionCommands.staleComparisons[key]!.source = {
    geometry: s.editVersionCommands.staleComparisons[key]!.candidate,
    vertexIndex: 1,
  };
  await nextTick();
  await buttons[0]!.trigger("click");
  expect(show).toHaveBeenCalledWith("source");
  s.editVersionCommands.staleComparisons.other = {
    ...s.editVersionCommands.staleComparisons[key]!,
  };
  s.editVersionCommands.localPhase = "stale";
  await nextTick();
  await wrapper.get('[data-test="comparison-discard"]').trigger("click");
  expect(s.editVersionCommands.staleComparisons[key]).toBeUndefined();
  expect(s.editVersionCommands.staleComparisons.other).toBeDefined();
  wrapper.unmount();
  expect(getEditorRuntime(pinia)).toBe(runtime);
  expect(runtime.workflow.cancelLocalEdit()).toBe(true);
  runtime.dispose();
});
