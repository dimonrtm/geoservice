import type { FeatureCollection, Geometry } from "geojson";
import type { GeoJSONSource, Map } from "maplibre-gl";

import type { WorkspaceResponse } from "@/contracts/work-orders";

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
      "line-color": "#0f766e",
      "line-width": 3,
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
  const featureSource = map.getSource(featureSourceId) as
    | GeoJSONSource
    | undefined;

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
  featureSource?.setData(workspace.workOrder.editVersion.features);
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

function addLayerIfMissing(
  map: Map,
  layer: Parameters<Map["addLayer"]>[0],
): void {
  if (!map.getLayer(layer.id)) {
    map.addLayer(layer);
  }
}
