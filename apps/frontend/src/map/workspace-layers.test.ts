import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  ensureWorkspaceLayers,
  fitWorkspaceToAoi,
  setWorkspaceData,
} from "@/map/workspace-layers";
import type { WorkspaceResponse } from "@/contracts/work-orders";

const setDataMock = vi.fn();

function workspace(): WorkspaceResponse {
  return {
    workOrder: {
      id: "wo-1",
      code: "WO-001",
      title: "Проверка участка фидера",
      description: null,
      status: "in_progress",
      scope: {
        aoi: {
          id: "aoi-1",
          name: "Рабочая область WO-001",
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
        associations: [],
      },
    },
  };
}

function fakeMap() {
  const sources = new Map<string, Record<string, unknown>>();
  const layers = new Set<string>();
  return {
    addSource: vi.fn((id: string, source: Record<string, unknown>) => {
      sources.set(id, { ...source, setData: setDataMock });
    }),
    getSource: vi.fn((id: string) => sources.get(id)),
    addLayer: vi.fn((layer: { id: string }) => {
      layers.add(layer.id);
    }),
    getLayer: vi.fn((id: string) => (layers.has(id) ? { id } : undefined)),
    fitBounds: vi.fn(),
  };
}

describe("workspace map layers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("creates read-only workspace sources and layers", () => {
    const map = fakeMap();

    ensureWorkspaceLayers(map as never);

    expect(map.addSource).toHaveBeenCalledWith(
      "workspace:aoi",
      expect.objectContaining({ type: "geojson" }),
    );
    expect(map.addSource).toHaveBeenCalledWith(
      "workspace:features",
      expect.objectContaining({ type: "geojson" }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({ id: "workspace:aoi:fill" }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({ id: "workspace:features:points" }),
    );
  });

  it("sets AOI and feature data", () => {
    const map = fakeMap();
    ensureWorkspaceLayers(map as never);

    setWorkspaceData(map as never, workspace());

    expect(setDataMock).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "FeatureCollection",
        features: expect.any(Array),
      }),
    );
    expect(setDataMock).toHaveBeenCalledTimes(2);
  });

  it("fits map to AOI extent", () => {
    const map = fakeMap();

    fitWorkspaceToAoi(map as never, workspace());

    expect(map.fitBounds).toHaveBeenCalledWith(
      [
        [65.5, 44.8],
        [65.54, 44.84],
      ],
      { padding: 48, duration: 0 },
    );
  });
});
