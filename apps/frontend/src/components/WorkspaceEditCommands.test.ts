import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/stores/auth";
import { useWorkOrdersStore } from "@/stores/workOrders";
import {
  target,
  workspaceFixture,
  successFixture,
} from "@/test/workspaceEditFixture";
import WorkspaceEditCommands from "./WorkspaceEditCommands.vue";
const api = vi.hoisted(() => ({
  saveFeatureGeometry: vi.fn(),
  fetchWorkspace: vi.fn(),
}));
vi.mock("@/api/workOrders", () => api);
const wrappers: ReturnType<typeof mount>[] = [];
function setup(changed = false) {
  const pinia = createPinia();
  setActivePinia(pinia);
  const auth = useAuthStore();
  auth.token = "test";
  auth.user = { id: "actor", email: "editor@example.local", role: "editor" };
  const store = useWorkOrdersStore();
  store.workspace = workspaceFixture(changed);
  store.workspace.workOrder.scope.aoi.geometry = {
    type: "Polygon",
    coordinates: [
      [
        [64, 43],
        [66, 43],
        [66, 45],
        [64, 45],
        [64, 43],
      ],
    ],
  };
  store.openedWorkOrderId = store.selectedWorkOrderId = target.workOrderId;
  store.openedEditVersionId = target.editVersionId;
  store.beginLocalEdit(target.featureId, 1);
  store.moveLocalVertex([65.1, 44.3]);
  const wrapper = mount(WorkspaceEditCommands, {
    global: { plugins: [pinia] },
    attachTo: document.body,
  });
  wrappers.push(wrapper);
  return { wrapper, store, auth };
}
beforeEach(() => {
  sessionStorage.clear();
  vi.resetAllMocks();
});
afterEach(() => {
  wrappers.splice(0).forEach((w) => w.unmount());
  document.body.innerHTML = "";
});
describe("workspace commands", () => {
  it("saves immediately and prevents duplicate activation until readback", async () => {
    const { wrapper, store } = setup();
    let resolve!: (v: ReturnType<typeof successFixture>) => void;
    api.saveFeatureGeometry.mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    const button = wrapper.get('[data-test="save-edit"]');
    await button.trigger("click");
    await button.trigger("click");
    await store.saveLocalDraft();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
    expect(button.attributes("disabled")).toBeDefined();
    resolve(
      successFixture(api.saveFeatureGeometry.mock.calls[0]![1].commandId),
    );
    await flushPromises();
    expect(wrapper.text()).toContain("Правка сохранена в рабочей версии");
    expect(store.localDraft).toBeNull();
  });
  it("cancels without dialog or HTTP, keeps selection and moves focus off disabled button", async () => {
    const { wrapper, store } = setup(true);
    const button = wrapper.get('[data-test="cancel-edit"]');
    (button.element as HTMLButtonElement).focus();
    await button.trigger("click");
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([
      65.1, 44.2,
    ]);
    expect(store.localDraft?.featureId).toBe(target.featureId);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(wrapper.get("h2").element);
  });
  it("revert explains unavailability without changing draft or calling API", async () => {
    const { wrapper, store } = setup(true);
    const draft = JSON.stringify(store.localDraft);
    await wrapper.get('[data-test="revert-edit"]').trigger("click");
    expect(wrapper.text()).toContain(
      "Возврат к исходному состоянию пока недоступен",
    );
    expect(wrapper.text()).toContain("Есть несохранённые изменения");
    expect(JSON.stringify(store.localDraft)).toBe(draft);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
  it("clears the revert notice after a new vertex movement", async () => {
    const { wrapper, store } = setup(true);
    await wrapper.get('[data-test="revert-edit"]').trigger("click");
    expect(wrapper.text()).toContain(
      "Возврат к исходному состоянию пока недоступен",
    );
    expect(store.moveLocalVertex([65.1, 44.4])).toBe(true);
    await flushPromises();
    expect(wrapper.text()).not.toContain(
      "Возврат к исходному состоянию пока недоступен",
    );
    expect(wrapper.text()).toContain("Есть несохранённые изменения");
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([
      65.1, 44.4,
    ]);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
  it("clears the revert notice when a line is selected", async () => {
    const { wrapper, store } = setup(true);
    store.cancelLocalEdit();
    await flushPromises();
    await wrapper.get('[data-test="revert-edit"]').trigger("click");
    expect(wrapper.text()).toContain(
      "Возврат к исходному состоянию пока недоступен",
    );
    expect(store.beginLocalEdit(target.featureId, 1)).toBe(true);
    await flushPromises();
    expect(wrapper.text()).not.toContain(
      "Возврат к исходному состоянию пока недоступен",
    );
    expect(store.localDraft?.featureId).toBe(target.featureId);
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
  });
  it.each(["unknown", "stale", "blocked"] as const)(
    "offers no recovery or cancellation during %s",
    async (phase) => {
      const { wrapper, store } = setup(true);
      store.phase = phase;
      await flushPromises();
      expect(wrapper.findAll("button")).toHaveLength(3);
      for (const b of wrapper.findAll("button"))
        expect(b.attributes("disabled")).toBeDefined();
      expect(wrapper.text()).toContain("недоступно");
    },
  );
  it("does not steal focus on asynchronous status updates and clears context notices", async () => {
    const { wrapper, store, auth } = setup(true);
    await wrapper.get('[data-test="revert-edit"]').trigger("click");
    const other = document.createElement("button");
    document.body.append(other);
    other.focus();
    store.phase = "unknown";
    await flushPromises();
    expect(document.activeElement).toBe(other);
    auth.user = { id: "other", email: "other@example.local", role: "editor" };
    await flushPromises();
    expect(wrapper.text()).not.toContain(
      "Возврат к исходному состоянию пока недоступен",
    );
  });
  it("shows known save success when GET fails without offering a retry", async () => {
    const { wrapper } = setup();
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.fetchWorkspace.mockRejectedValue(new Error("read"));
    await wrapper.get('[data-test="save-edit"]').trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain(
      "Правка сохранена, но актуальные данные карты не удалось загрузить",
    );
    expect(wrapper.find('[role="progressbar"]').exists()).toBe(false);
    expect(wrapper.findAll("button")).toHaveLength(3);
  });
});
