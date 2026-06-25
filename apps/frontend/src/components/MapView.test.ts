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

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    isAuthenticated: true,
    token: "token-1",
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
    expect(wrapper.text()).toContain("Карта готова. Выберите наряд в списке.");
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
    expect(wrapper.text()).toContain("WO-001");
    expect(wrapper.text()).toContain("Версия: open");
    expect(wrapper.text()).toContain("Базовая ревизия сети: 1");
    expect(wrapper.text()).toContain("Объекты: 1");
    expect(wrapper.text()).toContain("Связи: 1");
    expect(wrapper.text()).not.toContain("EditVersion:");
    expect(wrapper.text()).not.toContain("baseNetworkRevision:");
    expect(wrapper.text()).not.toContain("features:");
    expect(wrapper.text()).not.toContain("associations:");
  });
});
