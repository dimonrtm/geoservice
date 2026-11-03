import { shallowRef } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useFeatureLoading } from "./useFeatureLoading";
import {
  fetchLayerFeatureById,
  fetchLayerFeaturesByBbox,
  HttpError,
} from "@/api/layers";
import type { ApiFeature } from "@/contracts/geojson";
import type { Map as MapLibreMap } from "maplibre-gl";

vi.mock("maplibre-gl", () => ({ Marker: vi.fn() }));
vi.mock("@/api/layers", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/api/layers")>()),
  fetchLayerFeatureById: vi.fn(),
  fetchLayerFeaturesByBbox: vi.fn(),
}));
const layer = {
  id: "layer",
  name: "layer",
  title: "layer",
  srid: 4326,
  geometryType: "Point",
};
const feature: ApiFeature = {
  type: "Feature",
  id: "object",
  version: 1,
  properties: {},
  geometry: { type: "Point", coordinates: [70.01, 52.01] },
};
function setup(limit = 4096) {
  const setData = vi.fn(),
    restart = vi.fn();
  const map = {
    getZoom: () => 13,
    getBounds: () => ({
      getWest: () => 70,
      getSouth: () => 52,
      getEast: () => 70.02,
      getNorth: () => 52.02,
    }),
    getSource: () => ({ setData }),
  };
  const loading = useFeatureLoading(
    shallowRef(map as unknown as MapLibreMap),
    restart,
    limit,
  );
  return { loading, restart, setData };
}
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(fetchLayerFeaturesByBbox).mockResolvedValue({
    type: "FeatureCollection",
    features: [],
    meta: {
      bbox: [70, 52, 70.02, 52.02],
      limit: 500,
      returned: 0,
      sort: "id:asc",
      truncated: false,
      next_cursor: null,
    },
  });
});
describe("feature readback and event ordering", () => {
  it("keeps confirmed absence across newer delayed events in the same generation", async () => {
    const { loading, setData } = setup();
    await loading.reloadFeatures(layer, { force: true });
    vi.mocked(fetchLayerFeatureById).mockRejectedValueOnce(
      new HttpError(404, null),
    );
    await loading.applyPatchedFeature(layer, feature, true);
    await loading.applyPatchedFeature(layer, { ...feature, version: 2 }, true);
    expect(fetchLayerFeatureById).toHaveBeenCalledTimes(1);
    expect(setData.mock.lastCall?.[0].features).toEqual([]);
  });
  it("ignores a late lookup from the previous subscription", async () => {
    const { loading, setData } = setup();
    let finish!: (feature: ApiFeature) => void;
    vi.mocked(fetchLayerFeatureById).mockReturnValueOnce(
      new Promise((resolve) => (finish = resolve)),
    );
    const lookup = loading.applyPatchedFeature(layer, feature, true);
    loading.clearLayerCache(layer.id);
    await loading.reloadFeatures(layer, { force: true });
    finish(feature);
    await lookup;
    expect(setData.mock.lastCall?.[0].features).toEqual([]);
  });
  it("requests a new generation when bounded deletion history fills", () => {
    const { loading, restart } = setup(2);
    loading.applyDeletedFeature(layer, "a", 1);
    expect(restart).not.toHaveBeenCalled();
    loading.applyDeletedFeature(layer, "b", 1);
    expect(restart).toHaveBeenCalledOnce();
  });
});
