import { mount } from "@vue/test-utils";
import { nextTick, reactive } from "vue";
import { expect, it, vi } from "vitest";
import WorkspaceRecoveryList from "./WorkspaceRecoveryList.vue";

const access = reactive({ actorId: "a", sessionEpoch: 1 });
const resume = vi.fn();
vi.mock("@/editor/editorRuntimeBinding", () => ({
  getEditorRuntime: () => ({ sessionAccess: access }),
}));
vi.mock("@/stores/work_order/workOrders", () => ({
  useWorkOrdersStore: () => ({ items: [{ id: "work", code: "WO" }] }),
}));
vi.mock("@/stores/workspace/workspace_recovery/workspaceRecovery", () => ({
  useWorkspaceRecoveryStore: () => ({
    records: {
      rec: {
        key: "rec",
        requiresAccessConfirmation: true,
        blocks: ["access"],
        command: {
          actorId: "a",
          target: { workOrderId: "work" },
          request: { commandId: "cmd" },
        },
      },
    },
    resumeAfterAccess: resume,
  }),
}));

it("closes stale consent on session change and filters another actor's command", async () => {
  HTMLDialogElement.prototype.showModal = function () {
    this.open = true;
  };
  const wrapper = mount(WorkspaceRecoveryList);
  try {
    await wrapper.get('[data-test="resume-recovery"]').trigger("click");
    expect(wrapper.find("dialog").exists()).toBe(true);
    access.sessionEpoch++;
    await nextTick();
    expect(wrapper.find("dialog").exists()).toBe(false);
    expect(resume).not.toHaveBeenCalled();
    await wrapper.get('[data-test="resume-recovery"]').trigger("click");
    await wrapper.get('[data-test="confirm-resume"]').trigger("click");
    expect(resume).toHaveBeenCalledExactlyOnceWith(
      "rec",
      "cmd",
      access.sessionEpoch,
    );
    access.actorId = "b";
    await nextTick();
    expect(wrapper.find("article").exists()).toBe(false);
  } finally {
    wrapper.unmount();
  }
});
