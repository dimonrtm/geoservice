import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useWorkOrdersStore } from "./workOrders";
const { fetchAssignedWorkOrdersMock } = vi.hoisted(() => ({
  fetchAssignedWorkOrdersMock: vi.fn(),
}));
vi.mock("@/api/workOrders", () => ({
  fetchAssignedWorkOrders: fetchAssignedWorkOrdersMock,
}));
const SELECTED_WORK_ORDER_STORAGE_KEY = "geoservice:selected-work-order";
function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });

  return { promise, resolve, reject };
}
describe("assigned work orders", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    sessionStorage.clear();
    vi.clearAllMocks();
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

    const store = useWorkOrdersStore();

    await store.loadAssigned();

    expect(store.items).toHaveLength(1);
    expect(store.items[0]).toMatchObject({ code: "WO-001" });
    expect(store.isLoading).toBe(false);
    expect(store.loadError).toBeNull();
  });

  it("persists the selected work order in session storage", async () => {
    const store = useWorkOrdersStore();

    store.selectWorkOrder("wo-1");

    expect(store.selectedWorkOrderId).toBe("wo-1");
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1" }),
    );
  });

  it("keeps selection in memory when session storage writes fail", async () => {
    const setItemSpy = vi
      .spyOn(Storage.prototype, "setItem")
      .mockImplementation(() => {
        throw new DOMException("storage unavailable", "SecurityError");
      });

    try {
      const store = useWorkOrdersStore();

      expect(() => store.selectWorkOrder("wo-1")).not.toThrow();
      expect(store.selectedWorkOrderId).toBe("wo-1");
    } finally {
      setItemSpy.mockRestore();
    }
  });

  it("selects a work order locally without API calls", async () => {
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
    fetchAssignedWorkOrdersMock.mockRejectedValue({ isAxiosError: true });

    const store = useWorkOrdersStore();

    await store.loadAssigned();

    expect(store.items).toEqual([]);
    expect(store.isLoading).toBe(false);
    expect(store.loadError).toMatchObject({
      summary: "Не удалось загрузить назначенные наряды.",
      action: { id: "retry", label: "Повторить" },
    });
  });

  it("keeps the selected marker when assigned work orders fail to load", async () => {
    sessionStorage.setItem(
      SELECTED_WORK_ORDER_STORAGE_KEY,
      JSON.stringify({ workOrderId: "wo-1" }),
    );
    fetchAssignedWorkOrdersMock.mockRejectedValue({ isAxiosError: true });

    const store = useWorkOrdersStore();

    await store.loadAssigned();

    expect(store.loadError).not.toBeNull();
    expect(sessionStorage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY)).toBe(
      JSON.stringify({ workOrderId: "wo-1" }),
    );
  });

  it("ignores assigned work orders response after reset", async () => {
    const assignedResponse = {
      workOrders: [
        {
          id: "wo-1",
          code: "WO-001",
          title: "Old user work order",
          description: null,
          status: "assigned" as const,
        },
      ],
    };
    const assignedDeferred = createDeferred<typeof assignedResponse>();
    fetchAssignedWorkOrdersMock.mockReturnValue(assignedDeferred.promise);

    const store = useWorkOrdersStore();

    const loading = store.loadAssigned();
    expect(store.isLoading).toBe(true);

    store.reset();
    assignedDeferred.resolve(assignedResponse);
    await loading;

    expect(store.items).toEqual([]);
    expect(store.isLoading).toBe(false);
    expect(store.loadError).toBeNull();
  });
});
it("keeps selection independent of editor and recovery initialization", () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const orders = useWorkOrdersStore();
  orders.selectWorkOrder("wo");
  expect(orders.selectedWorkOrderId).toBe("wo");
  expect(Object.keys(pinia.state.value)).toEqual(["workOrders"]);
  expect(orders).not.toHaveProperty("saveLocalDraft");
});
