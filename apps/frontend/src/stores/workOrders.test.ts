import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const fetchAssignedWorkOrdersMock = vi.fn();

vi.mock("@/api/workOrders", () => ({
  fetchAssignedWorkOrders: fetchAssignedWorkOrdersMock,
}));

describe("work orders store", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it("loads assigned work orders and clears previous error", async () => {
    fetchAssignedWorkOrdersMock.mockResolvedValue({
      workOrders: [
        {
          id: "wo-1",
          code: "WO-001",
          title: "Проверка участка фидера",
          description: "Описание",
          status: "assigned",
        },
      ],
    });

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();

    await store.loadAssigned();

    expect(store.items).toHaveLength(1);
    expect(store.items[0]).toMatchObject({ code: "WO-001" });
    expect(store.isLoading).toBe(false);
    expect(store.errorMessage).toBeNull();
  });

  it("selects a work order locally without API calls", async () => {
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

    store.selectWorkOrder("wo-1");

    expect(store.selectedWorkOrderId).toBe("wo-1");
    expect(store.selectedWorkOrder?.code).toBe("WO-001");
    expect(fetchAssignedWorkOrdersMock).not.toHaveBeenCalled();
  });

  it("keeps a user-facing error when loading fails", async () => {
    fetchAssignedWorkOrdersMock.mockRejectedValue(new Error("network"));

    const { useWorkOrdersStore } = await import("@/stores/workOrders");
    const store = useWorkOrdersStore();

    await store.loadAssigned();

    expect(store.items).toEqual([]);
    expect(store.isLoading).toBe(false);
    expect(store.errorMessage).toBe(
      "Не удалось загрузить назначенные наряды. Попробуйте ещё раз.",
    );
  });
});
