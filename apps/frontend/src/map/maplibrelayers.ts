import { Map, type GeoJSONSource } from "maplibre-gl";
import type { LayerDto } from "@/api/layers";
import type { FeatureCollection, Geometry } from "geojson";
export type Bbox = [number, number, number, number];
export function ensureLayerOnMap(map: Map | null, layer: LayerDto): void {
  if (!map) {
    return;
  }
  const sourceId = "src:" + layer.id;
  const layerId = "layer:" + layer.id;
  const outlineId = "layer:" + layer.id + ":outline";
  const source = map.getSource(sourceId);
  if (!source) {
    map.addSource(sourceId, {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
  }
  const existLayer = map.getLayer(layerId);
  if (!existLayer) {
    if (layer.geometryType.includes("Point")) {
      map.addLayer({
        id: layerId,
        type: "circle",
        source: sourceId,
        paint: {
          "circle-radius": 5,
          "circle-stroke-width": 1,
          "circle-color": "#000000",
          "circle-stroke-color": "#FFFFFF",
        },
      });
    } else if (layer.geometryType.includes("Line")) {
      map.addLayer({
        id: layerId,
        type: "line",
        source: sourceId,
        layout: {
          "line-join": "round",
          "line-cap": "round",
        },
        paint: { "line-width": 2, "line-color": "#000000" },
      });
    } else {
      map.addLayer({
        id: layerId,
        type: "fill",
        source: sourceId,
        paint: { "fill-color": "#000000", "fill-opacity": 0.25 },
      });
      map.addLayer({
        id: outlineId,
        type: "line",
        source: sourceId,
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-width": 2, "line-color": "#000000" },
      });
    }
  }
}

export function getCurrentBbox(map: Map | null): Bbox {
  if (!map) {
    return [0, 0, 0, 0];
  }
  const bounds = map.getBounds();
  return [
    bounds.getWest(),
    bounds.getSouth(),
    bounds.getEast(),
    bounds.getNorth(),
  ];
}

export function setSourceData(
  map: Map | null,
  sourceId: string,
  featureCollection: { type: "FeatureCollection"; features: unknown[] },
) {
  if (!map) {
    return;
  }
  const source = map.getSource(sourceId) as GeoJSONSource | undefined;
  if (!source) {
    return;
  }
  source.setData(featureCollection as FeatureCollection<Geometry>);
}

export function isValidBbox(bbox: Bbox): boolean {
  return bbox.every(Number.isFinite) && bbox[0] < bbox[2] && bbox[1] < bbox[3];
}

export function setLayerVisibility(
  map: Map | null,
  layerId: string,
  visible: boolean,
): void {
  if (!map) {
    return;
  }
  const v = visible ? "visible" : "none";
  if (map.getLayer(layerId)) {
    map.setLayoutProperty(layerId, "visibility", v);
  }
}

export function setLayerPairVisibility(
  map: Map | null,
  layer: LayerDto,
  visible: boolean,
): void {
  if (!map) {
    return;
  }
  const baseId = "layer:" + layer.id;
  const outlineId = "layer:" + layer.id + ":outline";
  setLayerVisibility(map, baseId, visible);
  setLayerVisibility(map, outlineId, visible);
}

export function setAnyLayerVisibility(
  map: Map | null,
  layer: LayerDto,
  visible: boolean,
): void {
  if (!map) {
    return;
  }
  if (layer.geometryType.includes("Polygon")) {
    setLayerPairVisibility(map, layer, visible);
  } else {
    setLayerVisibility(map, "layer:" + layer.id, visible);
  }
}

export function formatNumber(n: number): string {
  return n.toFixed(4);
}

export function formatBbox(bbox: Bbox): string {
  return `${formatNumber(bbox[0])},${formatNumber(bbox[1])},${formatNumber(bbox[2])},${formatNumber(bbox[3])}`;
}

export function BboxClose(a: Bbox, b: Bbox, eps: number): boolean {
  return (
    Math.abs(a[0] - b[0]) < eps &&
    Math.abs(a[1] - b[1]) < eps &&
    Math.abs(a[2] - b[2]) < eps &&
    Math.abs(a[3] - b[3]) < eps
  );
}
