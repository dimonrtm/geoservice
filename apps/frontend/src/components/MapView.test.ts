import { mount } from "@vue/test-utils";
import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { WorkspaceResponse } from "@/contracts/work-orders";

const mocks = vi.hoisted(() => ({
  abortLayerLoading: vi.fn(),
  applyCreatedFeature: vi.fn(),
  applyDeletedFeature: vi.fn(),
  applyPatchedFeature: vi.fn(),
  bindActiveLayerClick: vi.fn(),
  cancelEditing: vi.fn(),
  changeLayer: vi.fn(),
  createMap: vi.fn(),
  deleteEditingFeature: vi.fn(),
  destroyMap: vi.fn(),
  disconnectRealtime: vi.fn(),
  disableEditingOverlaySync: vi.fn(),
  enableEditingOverlaySync: vi.fn(),
  ensureWorkspaceLayers: vi.fn(),
  fitWorkspaceToAoi: vi.fn(),
  handleRealtimeLayerChange: vi.fn(),
  loadLayers: vi.fn(),
  mapOff: vi.fn(),
  mapOn: vi.fn(),
  reloadFeatures: vi.fn(),
  resetInteractionState: vi.fn(),
  saveChange: vi.fn(),
  setWorkspaceData: vi.fn(),
  stopPendingFeatureWork: vi.fn(),
  unbindActiveLayerClick: vi.fn(),
}));

vi.mock("maplibre-gl/dist/maplibre-gl.css", () => ({}));
vi.mock("maplibre-gl", () => ({ Marker: vi.fn() }));

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    isAuthenticated: true,
  }),
}));

vi.mock("@/composables/map/useMapInstance", () => ({
  useMapInstance: () => ({
    map: { value: { off: mocks.mapOff, on: mocks.mapOn } },
    createMap: mocks.createMap,
    destroyMap: mocks.destroyMap,
  }),
}));

vi.mock("@/composables/map/useLayerSelection", () => ({
  useLayerSelection: () => ({
    layers: { value: [] },
    activeLayer: { value: null },
    activeLayerId: { value: "" },
    loadLayers: mocks.loadLayers,
    changeLayer: mocks.changeLayer,
    abortLayerLoading: mocks.abortLayerLoading,
  }),
}));

vi.mock("@/composables/map/useFeatureLoading", async () => {
  const { ref } = await import("vue");

  return {
    useFeatureLoading: () => ({
      labelText: ref(""),
      reloadFeatures: mocks.reloadFeatures,
      createMoveEndHandler: () => vi.fn(),
      applyCreatedFeature: mocks.applyCreatedFeature,
      applyPatchedFeature: mocks.applyPatchedFeature,
      applyDeletedFeature: mocks.applyDeletedFeature,
      stopPendingFeatureWork: mocks.stopPendingFeatureWork,
    }),
  };
});

vi.mock("@/composables/map/useLayerRealtime", () => ({
  useLayerRealtime: () => ({
    handleLayerChange: mocks.handleRealtimeLayerChange,
    disconnect: mocks.disconnectRealtime,
    isConnected: { value: false },
    isReconnecting: { value: false },
    isSyncingAfterReconnect: { value: false },
    hasStoppedReconnect: { value: false },
    isAuthError: { value: false },
  }),
}));

vi.mock("@/composables/map/usePolygonEditing", () => ({
  usePolygonEditing: () => ({
    enableEditingOverlaySync: mocks.enableEditingOverlaySync,
    disableEditingOverlaySync: mocks.disableEditingOverlaySync,
    bindActiveLayerClick: mocks.bindActiveLayerClick,
    unbindActiveLayerClick: mocks.unbindActiveLayerClick,
    resetInteractionState: mocks.resetInteractionState,
    saveChange: mocks.saveChange,
    deleteEditingFeature: mocks.deleteEditingFeature,
    cancelEditing: mocks.cancelEditing,
  }),
}));

vi.mock("@/map/workspace-layers", () => ({
  ensureWorkspaceLayers: mocks.ensureWorkspaceLayers,
  fitWorkspaceToAoi: mocks.fitWorkspaceToAoi,
  setWorkspaceData: mocks.setWorkspaceData,
}));

function workspace(): WorkspaceResponse {
  return {
    workOrder: {
      id: "wo-1",
      code: "WO-001",
      title: "Feeder section inspection",
      description: null,
      status: "in_progress",
      scope: {
        aoi: {
          id: "aoi-1",
          name: "WO-001 workspace area",
          description: null,
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [65.5, 44.8],
                [65.54, 44.8],
                [65.54, 44.84],
                [65.5, 44.84],
                [65.5, 44.8],
              ],
            ],
          },
          extent: [65.5, 44.8, 65.54, 44.84],
        },
      },
      editVersion: {
        id: "ev-1",
        status: "open",
        baseNetworkRevision: 1,
        draftVersionToken: "1",
        hasPersistedChangeSet: false,
        basicValidation: null,
        changeSet: null,
        features: {
          type: "FeatureCollection",
          features: [
            {
              id: "feature-1",
              type: "Feature",
              geometry: { type: "Point", coordinates: [65.52, 44.82] },
              properties: { assetCode: "P-001" },
            },
          ],
        },
        associations: [
          {
            id: "assoc-1",
            fromFeatureId: "feature-1",
            toFeatureId: "feature-2",
            associationType: "connected_to",
            version: 1,
          },
        ],
      },
    },
  };
}

describe("MapView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.createMap.mockResolvedValue({
      off: mocks.mapOff,
      on: mocks.mapOn,
    });
  });

  it("creates only the base map in empty mode", async () => {
    const { default: MapView } = await import("@/components/MapView.vue");

    const wrapper = mount(MapView, {
      props: {
        mode: "empty",
      },
    });
    await flushPromises();

    expect(mocks.createMap).toHaveBeenCalledTimes(1);
    expect(mocks.loadLayers).not.toHaveBeenCalled();
    expect(mocks.reloadFeatures).not.toHaveBeenCalled();
    expect(mocks.handleRealtimeLayerChange).not.toHaveBeenCalled();
    expect(mocks.enableEditingOverlaySync).not.toHaveBeenCalled();
    expect(wrapper.get(".badge").text()).toContain(
      "Карта готова. Выберите наряд в списке.",
    );
  });

  it("passes auth readiness to realtime without exposing a token", async () => {
    const layer = {
      id: "layer-1",
      name: "power_lines",
      title: "Power lines",
    };
    mocks.loadLayers.mockResolvedValue({
      status: "ready",
      total: 1,
      layer,
    });
    const { default: MapView } = await import("@/components/MapView.vue");

    const wrapper = mount(MapView, {
      props: {
        mode: "editing",
      },
    });
    await flushPromises();

    expect(wrapper.get(".badge").text()).toContain(
      "Слои загружены: 1. Выбран слой: Power lines",
    );
    expect(mocks.handleRealtimeLayerChange).toHaveBeenCalledWith(layer, true);
    expect(mocks.handleRealtimeLayerChange).not.toHaveBeenCalledWith(
      layer,
      expect.any(String),
    );
  });
});

describe("MapView workspace mode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.createMap.mockResolvedValue({
      off: mocks.mapOff,
      on: mocks.mapOn,
    });
  });

  it("renders read-only workspace mode without legacy layer loading", async () => {
    const { default: MapView } = await import("@/components/MapView.vue");

    const wrapper = mount(MapView, {
      props: {
        mode: "workspace",
        workspace: workspace(),
        workspaceKey: "wo-1:ev-1",
        shouldFitWorkspace: true,
      },
    });
    await flushPromises();

    expect(mocks.createMap).toHaveBeenCalledTimes(1);
    expect(mocks.ensureWorkspaceLayers).toHaveBeenCalledTimes(1);
    expect(mocks.setWorkspaceData).toHaveBeenCalledWith(
      expect.anything(),
      workspace(),
    );
    expect(mocks.fitWorkspaceToAoi).toHaveBeenCalledWith(
      expect.anything(),
      workspace(),
    );
    expect(wrapper.emitted("workspaceFitted")?.[0]).toEqual(["wo-1:ev-1"]);
    expect(mocks.loadLayers).not.toHaveBeenCalled();
    expect(mocks.reloadFeatures).not.toHaveBeenCalled();
    expect(mocks.handleRealtimeLayerChange).not.toHaveBeenCalled();
    expect(mocks.enableEditingOverlaySync).not.toHaveBeenCalled();
    expect(wrapper.find(".badge").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("WO-001");
    expect(wrapper.text()).not.toContain("Версия: open");
    expect(wrapper.text()).not.toContain("Базовая ревизия сети: 1");
    expect(wrapper.text()).not.toContain("Объекты: 1");
    expect(wrapper.text()).not.toContain("Связи: 1");
    expect(wrapper.text()).not.toContain("EditVersion:");
    expect(wrapper.text()).not.toContain("baseNetworkRevision:");
    expect(wrapper.text()).not.toContain("features:");
    expect(wrapper.text()).not.toContain("associations:");
  });
});

describe("MapView startup", () => {
  const layer = { id: "layer-1", name: "lines", title: "Линии" };
  const mapInstance = () => ({ off: mocks.mapOff, on: mocks.mapOn });

  beforeEach(() => {
    vi.resetAllMocks();
    mocks.createMap.mockResolvedValue(mapInstance());
    mocks.loadLayers.mockResolvedValue({ status: "ready", total: 1, layer });
  });

  it.each(["workspace", "empty", "editing"] as const)(
    "shows startup error in %s mode",
    async (mode) => {
      mocks.createMap.mockRejectedValue(new Error("WebGL unavailable"));
      const { default: MapView } = await import("./MapView.vue");
      const wrapper = mount(MapView, {
        props: { mode, workspace: workspace() },
      });
      await flushPromises();
      expect(wrapper.findAll('[role="alert"]')).toHaveLength(1);
      const alert = wrapper.get('[role="alert"]');
      expect(alert.text()).toContain("Не удалось запустить карту");
      expect(alert.text()).toContain(
        "Обновите страницу с помощью кнопки обновления в браузере.",
      );
      expect(alert.find("button").exists()).toBe(false);
      expect(wrapper.find(".toolbar").exists()).toBe(false);
      expect(wrapper.find(".badge").exists()).toBe(false);
      expect(wrapper.find(".realtimeBadge").exists()).toBe(false);
      expect(wrapper.emitted("readyChange")).toEqual([[false]]);
      wrapper.unmount();
    },
  );

  it.each(["workspace", "empty", "editing"] as const)(
    "reports readiness only after startup completes in %s mode",
    async (mode) => {
      let resolve!: (value: ReturnType<typeof mapInstance>) => void;
      mocks.createMap.mockReturnValue(
        new Promise((done) => {
          resolve = done;
        }),
      );
      const { default: MapView } = await import("./MapView.vue");
      const wrapper = mount(MapView, {
        props: { mode, workspace: workspace() },
      });
      expect(wrapper.find(".toolbar").exists()).toBe(false);
      expect(wrapper.emitted("readyChange")).toEqual([[false]]);
      resolve(mapInstance());
      await flushPromises();
      expect(wrapper.emitted("readyChange")).toEqual([[false], [true]]);
      expect(wrapper.find(".toolbar").exists()).toBe(mode === "editing");
      expect(wrapper.find('[role="alert"]').exists()).toBe(false);
      wrapper.unmount();
      expect(wrapper.emitted("readyChange")?.slice(-1)).toEqual([[false]]);
    },
  );

  it("shows startup error for null map", async () => {
    mocks.createMap.mockResolvedValue(null);
    const { default: MapView } = await import("./MapView.vue");
    const wrapper = mount(MapView, {
      props: { mode: "workspace", workspace: workspace() },
    });
    await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain(
      "Не удалось запустить карту",
    );
    expect(wrapper.emitted("readyChange")).toEqual([[false]]);
    wrapper.unmount();
  });

  it("shows error when initial workspace rendering throws", async () => {
    mocks.setWorkspaceData.mockImplementation(() => {
      throw new Error("render failed");
    });
    const { default: MapView } = await import("./MapView.vue");
    const wrapper = mount(MapView, {
      props: { mode: "workspace", workspace: workspace() },
    });
    await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain(
      "Не удалось запустить карту",
    );
    expect(wrapper.emitted("readyChange")).toEqual([[false]]);
    wrapper.unmount();
  });

  it.each(["resolve", "reject"])(
    "ignores startup %s after unmount",
    async (outcome) => {
      let resolve!: (value: ReturnType<typeof mapInstance>) => void;
      let reject!: (reason: Error) => void;
      mocks.createMap.mockReturnValue(
        new Promise((done, fail) => {
          resolve = done;
          reject = fail;
        }),
      );
      const { default: MapView } = await import("./MapView.vue");
      const wrapper = mount(MapView, {
        props: { mode: "workspace", workspace: workspace() },
      });
      wrapper.unmount();
      const events = [...(wrapper.emitted("readyChange") ?? [])];
      if (outcome === "resolve") resolve(mapInstance());
      else reject(new Error("late failure"));
      await flushPromises();
      expect(wrapper.emitted("readyChange") ?? []).toEqual(events);
      expect(mocks.ensureWorkspaceLayers).not.toHaveBeenCalled();
      expect(mocks.loadLayers).not.toHaveBeenCalled();
      expect(mocks.bindActiveLayerClick).not.toHaveBeenCalled();
    },
  );

  it("does not classify legacy data failure as map startup failure", async () => {
    mocks.loadLayers.mockRejectedValue(new Error("HTTP 503"));
    const { default: MapView } = await import("./MapView.vue");
    const wrapper = mount(MapView, { props: { mode: "editing" } });
    await flushPromises();
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
    expect(wrapper.get(".badge").text()).toContain(
      "Не удалось загрузить данные карты",
    );
    expect(wrapper.find(".toolbar").exists()).toBe(false);
    wrapper.unmount();
  });

  it("keeps an empty legacy layer list as a successful startup", async () => {
    mocks.loadLayers.mockResolvedValue({ status: "empty" });
    const { default: MapView } = await import("./MapView.vue");
    const wrapper = mount(MapView, { props: { mode: "editing" } });
    await flushPromises();
    expect(wrapper.get(".badge").text()).toBe("Слоев нет");
    expect(wrapper.find('[role="alert"]').exists()).toBe(false);
    expect(wrapper.emitted("readyChange")?.slice(-1)).toEqual([[true]]);
    wrapper.unmount();
  });
});
