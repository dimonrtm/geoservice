import { stopRecovery } from "@/test/recoveryIntegration";
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
  store.items = [
    {
      id: target.workOrderId,
      code: "WO",
      title: "Work",
      description: null,
      status: "in_progress",
    },
  ];
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
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute("open");
  };
  sessionStorage.clear();
  vi.resetAllMocks();
});
afterEach(() => {
  stopRecovery();
  vi.useRealTimers();
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
    await vi.waitFor(() =>
      expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1),
    );
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
    expect(button.attributes("disabled")).toBeDefined();
    resolve(
      successFixture(api.saveFeatureGeometry.mock.calls[0]![1].commandId),
    );
    await flushPromises();
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain("Правка сохранена в рабочей версии"),
    );
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
  it("dirty revert requires two decisions and Escape never restores discarded draft", async () => {
    const { wrapper, store } = setup(true);
    const button = wrapper.get('[data-test="revert-edit"]');
    (button.element as HTMLButtonElement).focus();
    const original = JSON.stringify(store.localDraft);
    await button.trigger("click");
    await flushPromises();
    expect(wrapper.get('[role="dialog"]').text()).toContain("окончательно");
    expect(document.activeElement).toBe(
      wrapper.get('[data-test="revert-safe"]').element,
    );
    await wrapper.get('[role="dialog"]').trigger("keydown", { key: "Escape" });
    expect(JSON.stringify(store.localDraft)).toBe(original);
    await button.trigger("click");
    await wrapper.get('[data-test="revert-proceed"]').trigger("click");
    expect(store.localDraft).toBeNull();
    expect(wrapper.get('[role="dialog"]').text()).toContain("История");
    await wrapper.get('[role="dialog"]').trigger("keydown", { key: "Escape" });
    await flushPromises();
    expect(store.localDraft).toBeNull();
    expect(api.saveFeatureGeometry).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(button.element);
  });
  it("traps focus and confirms clean revert without a discard step", async () => {
    const { wrapper, store } = setup(true);
    store.cancelLocalEdit();
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.fetchWorkspace.mockResolvedValue(workspaceFixture());
    await wrapper.get('[data-test="revert-edit"]').trigger("click");
    await flushPromises();
    const safe = wrapper.get('[data-test="revert-safe"]');
    const proceed = wrapper.get('[data-test="revert-proceed"]');
    await safe.trigger("keydown", { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(proceed.element);
    await proceed.trigger("keydown", { key: "Tab" });
    expect(document.activeElement).toBe(safe.element);
    await proceed.trigger("click");
    await flushPromises();
    await vi.waitFor(() =>
      expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1),
    );
    await vi.waitFor(() => expect(store.localDraft).toBeNull());
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
  });
  it("unknown retry launches one bounded series through the actual store", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const { wrapper, store } = setup();
    api.saveFeatureGeometry.mockRejectedValue({ isAxiosError: true });
    const save = store.saveLocalDraft();
    await save;
    await vi.runAllTimersAsync();
    await wrapper.get('[data-test="retry-command"]').trigger("click");
    await vi.runAllTimersAsync();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(11);
    vi.useRealTimers();
  });
  it("stale readback exposes explicit discard without another PUT", async () => {
    const { wrapper, store } = setup();
    api.saveFeatureGeometry.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 409,
        data: { code: "DRAFT_VERSION_STALE", message: "stale" },
      },
    });
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await wrapper.get('[data-test="save-edit"]').trigger("click");
    await flushPromises();
    await vi.waitFor(() => expect(store.canDiscardRejectedAttempt).toBe(true));
    await wrapper.get('[data-test="discard-rejected"]').trigger("click");
    expect(store.localDraft).toBeNull();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    expect(api.fetchWorkspace).toHaveBeenCalledTimes(1);
  });
  it("does not steal focus on asynchronous status updates and clears context notices", async () => {
    const { wrapper, store, auth } = setup(true);
    const other = document.createElement("button");
    document.body.append(other);
    other.focus();
    store.localPhase = "unknown";
    await flushPromises();
    expect(document.activeElement).toBe(other);
    auth.user = { id: "other", email: "other@example.local", role: "editor" };
    await flushPromises();
    expect(wrapper.text()).not.toContain(
      "Возврат к исходному состоянию пока недоступен",
    );
  });
  it("retries only one GET after known success", async () => {
    const { wrapper, store } = setup();
    api.saveFeatureGeometry.mockImplementation((_t, r) =>
      Promise.resolve(successFixture(r.commandId)),
    );
    api.fetchWorkspace.mockRejectedValue(new Error("read"));
    await wrapper.get('[data-test="save-edit"]').trigger("click");
    await flushPromises();
    await vi.waitFor(() => expect(store.readbackError).toBeTruthy());
    expect(wrapper.text()).toContain(
      "Операция выполнена, но актуальные данные карты не удалось загрузить",
    );
    expect(wrapper.find('[role="progressbar"]').exists()).toBe(false);
    api.fetchWorkspace.mockResolvedValue(workspaceFixture(true));
    await wrapper.get('[data-test="retry-read"]').trigger("click");
    await flushPromises();
    expect(api.saveFeatureGeometry).toHaveBeenCalledTimes(1);
    await vi.waitFor(() => expect(api.fetchWorkspace).toHaveBeenCalledTimes(2));
  });
});
