import type { FeatureCollection, Geometry } from "geojson";
import type { GeoJSONSource, Map } from "maplibre-gl";

import type { WorkspaceResponse } from "@/contracts/work-orders";
import type { WorkspaceLocalDraft } from "@/domain/workspaceDraft";

const emptyFeatureCollection: FeatureCollection<
  Geometry,
  Record<string, unknown>
> = {
  type: "FeatureCollection",
  features: [],
};

const aoiSourceId = "workspace:aoi";
const featureSourceId = "workspace:features";

export function ensureWorkspaceLayers(map: Map | null): void {
  if (!map) {
    return;
  }

  if (!map.getSource(aoiSourceId)) {
    map.addSource(aoiSourceId, {
      type: "geojson",
      data: emptyFeatureCollection,
    });
  }

  if (!map.getSource(featureSourceId)) {
    map.addSource(featureSourceId, {
      type: "geojson",
      promoteId: "__workspaceFeatureId",
      data: emptyFeatureCollection,
    });
  }

  addLayerIfMissing(map, {
    id: "workspace:aoi:fill",
    type: "fill",
    source: aoiSourceId,
    paint: {
      "fill-color": "#f59e0b",
      "fill-opacity": 0.14,
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:aoi:outline",
    type: "line",
    source: aoiSourceId,
    paint: {
      "line-color": "#d97706",
      "line-width": 2,
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:features:polygons",
    type: "fill",
    source: featureSourceId,
    filter: [
      "match",
      ["geometry-type"],
      ["Polygon", "MultiPolygon"],
      true,
      false,
    ],
    paint: {
      "fill-color": "#2563eb",
      "fill-opacity": 0.2,
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:features:polygon-outline",
    type: "line",
    source: featureSourceId,
    filter: [
      "match",
      ["geometry-type"],
      ["Polygon", "MultiPolygon"],
      true,
      false,
    ],
    paint: {
      "line-color": "#1d4ed8",
      "line-width": 2,
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:features:lines",
    type: "line",
    source: featureSourceId,
    filter: [
      "match",
      ["geometry-type"],
      ["LineString", "MultiLineString"],
      true,
      false,
    ],
    paint: {
      "line-color": [
        "case",
        ["==", ["get", "__workspaceSelected"], true],
        "#ea580c",
        "#0f766e",
      ],
      "line-width": [
        "case",
        ["==", ["get", "__workspaceSelected"], true],
        5,
        3,
      ],
    },
  });
  addLayerIfMissing(map, {
    id: "workspace:features:points",
    type: "circle",
    source: featureSourceId,
    filter: ["match", ["geometry-type"], ["Point", "MultiPoint"], true, false],
    paint: {
      "circle-color": "#7c3aed",
      "circle-radius": 5,
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 1,
    },
  });
}

export function setWorkspaceData(
  map: Map | null,
  workspace: WorkspaceResponse,
): void {
  if (!map) {
    return;
  }

  const aoiSource = map.getSource(aoiSourceId) as GeoJSONSource | undefined;

  aoiSource?.setData({
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: workspace.workOrder.scope.aoi.geometry,
        properties: {
          id: workspace.workOrder.scope.aoi.id,
          name: workspace.workOrder.scope.aoi.name,
        },
      },
    ],
  });
  setWorkspaceDraftData(map, workspace, null);
}

export function fitWorkspaceToAoi(
  map: Map | null,
  workspace: WorkspaceResponse,
): void {
  if (!map) {
    return;
  }

  const [west, south, east, north] = workspace.workOrder.scope.aoi.extent;
  map.fitBounds(
    [
      [west, south],
      [east, north],
    ],
    { padding: 48, duration: 0 },
  );
}

export function setWorkspaceDraftData(
  map: Map,
  workspace: WorkspaceResponse,
  draft: WorkspaceLocalDraft | null,
): void {
  const source = map.getSource(featureSourceId) as GeoJSONSource | undefined;
  const data = {
    type: "FeatureCollection",
    features: workspace.workOrder.editVersion.features.features.map(
      (feature) => ({
        ...feature,
        geometry:
          draft?.featureId === feature.id
            ? draft.candidateGeometry
            : feature.geometry,
        properties: {
          ...feature.properties,
          __workspaceFeatureId: feature.id,
          __workspaceSelected: draft?.featureId === feature.id,
        },
      }),
    ),
  };
  // Detach Vue proxies and mutable store references before the worker boundary.
  source?.setData(JSON.parse(JSON.stringify(data)) as FeatureCollection);
}

function addLayerIfMissing(
  map: Map,
  layer: Parameters<Map["addLayer"]>[0],
): void {
  if (!map.getLayer(layer.id)) {
    map.addLayer(layer);
  }
}

export function setWorkspaceComparisonData(
  map: Map,
  geometry: import("@/contracts/workspace-edit").LineStringXY | null,
): void {
  const id = "workspace:comparison";
  if (!map.getSource(id))
    map.addSource(id, { type: "geojson", data: emptyFeatureCollection });
  addLayerIfMissing(map, {
    id,
    type: "line",
    source: id,
    paint: {
      "line-color": "#a21caf",
      "line-width": 6,
      "line-dasharray": [2, 1],
    },
  });
  (map.getSource(id) as GeoJSONSource)?.setData(
    geometry
      ? {
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              properties: {},
              geometry: JSON.parse(JSON.stringify(geometry)),
            },
          ],
        }
      : emptyFeatureCollection,
  );
}
