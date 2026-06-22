import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/components/MapView.vue", () => ({
  default: {
    name: "MapView",
    props: ["mode"],
    template: '<div data-test="map-view" :data-mode="mode"></div>',
  },
}));

const loadAssignedMock = vi.fn();

describe("EditorWorkOrdersView", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it("loads work orders and renders empty map mode", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Проверка участка фидера",
        description: "Описание",
        status: "assigned",
      },
    ];
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } = await import(
      "@/components/EditorWorkOrdersView.vue"
    );
    const wrapper = mount(EditorWorkOrdersView);

    expect(loadAssignedMock).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain("Мои наряды");
    expect(wrapper.text()).toContain("WO-001");
    expect(wrapper.get('[data-test="map-view"]').attributes("data-mode")).toBe(
      "empty",
    );
  });

  it("selects and highlights a work order locally", async () => {
    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();
    store.items = [
      {
        id: "wo-1",
        code: "WO-001",
        title: "Проверка участка фидера",
        description: null,
        status: "assigned",
      },
    ];
    store.loadAssigned = loadAssignedMock;

    const { default: EditorWorkOrdersView } = await import(
      "@/components/EditorWorkOrdersView.vue"
    );
    const wrapper = mount(EditorWorkOrdersView);

    await wrapper.get('[data-test="work-order-wo-1"]').trigger("click");

    expect(store.selectedWorkOrderId).toBe("wo-1");
    expect(wrapper.get('[data-test="work-order-wo-1"]').classes()).toContain(
      "isSelected",
    );
  });
});
