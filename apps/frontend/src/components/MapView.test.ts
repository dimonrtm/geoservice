import { mount } from "@vue/test-utils";
import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

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
  handleRealtimeLayerChange: vi.fn(),
  loadLayers: vi.fn(),
  mapOff: vi.fn(),
  mapOn: vi.fn(),
  reloadFeatures: vi.fn(),
  resetInteractionState: vi.fn(),
  saveChange: vi.fn(),
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
