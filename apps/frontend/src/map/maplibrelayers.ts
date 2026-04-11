import { Map, type GeoJSONSource } from "maplibre-gl";
import type { LayerDto } from "@/contracts/api";
import type {
  ApiFeatureCollection,
  FeatureProperties,
  PolygonGeometry,
} from "@/contracts/geojson";
import type { FeatureCollection, Geometry } from "geojson";
import { type EditSession, type EditState } from "@/stores/edit";

export type Bbox = [number, number, number, number];
export type VersionIndex = Record<string, number>;

const emptyFc: FeatureCollection<Geometry, FeatureProperties> = {
  type: "FeatureCollection",
  features: [],
};
const editPolygonSourceId = "edit:polygon";
const editVerticesSourceId = "edit:vertices";

export function ensureLayerOnMap(map: Map | null, layer: LayerDto): void {
  if (!map) {
    return;
  }

  const sourceId = `src:${layer.id}`;
  const layerId = `layer:${layer.id}`;
  const outlineId = `layer:${layer.id}:outline`;
  if (!map.getSource(sourceId)) {
    map.addSource(sourceId, {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
  }

  if (map.getLayer(layerId)) {
    return;
  }

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
    return;
  }

  if (layer.geometryType.includes("Line")) {
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
    return;
  }

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

export function ensureEditSource(map: Map | null): void {
  if (!map) {
    return;
  }

  if (!map.getSource(editPolygonSourceId)) {
    map.addSource(editPolygonSourceId, { type: "geojson", data: emptyFc });
  }
  if (!map.getSource(editVerticesSourceId)) {
    map.addSource(editVerticesSourceId, { type: "geojson", data: emptyFc });
  }
}

export function ensureEditLayer(map: Map | null): void {
  if (!map) {
    return;
  }

  const editPolygonFillId = "edit:polygon:fill";
  const editPolygonOutlineId = "edit:polygon:outline";
  const editVerticesPointId = "edit:vertices:point";

  if (!map.getLayer(editPolygonFillId)) {
    map.addLayer({
      id: editPolygonFillId,
      type: "fill",
      source: editPolygonSourceId,
      paint: { "fill-color": "#FF0000", "fill-opacity": 0.25 },
    });
  }
  if (!map.getLayer(editPolygonOutlineId)) {
    map.addLayer({
      id: editPolygonOutlineId,
      type: "line",
      source: editPolygonSourceId,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-width": 2, "line-color": "#FF0000" },
    });
  }
  if (!map.getLayer(editVerticesPointId)) {
    map.addLayer({
      id: editVerticesPointId,
      type: "circle",
      source: editVerticesSourceId,
      paint: {
        "circle-radius": 3,
        "circle-stroke-width": 1,
        "circle-color": "#FF0000",
        "circle-stroke-color": "#FFFFFF",
      },
    });
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
  featureCollection: ApiFeatureCollection,
): void {
  if (!map) {
    return;
  }

  const source = map.getSource(sourceId) as GeoJSONSource | undefined;
  if (!source) {
    return;
  }

  source.setData(toMapLibreFeatureCollection(featureCollection));
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

  const visibility = visible ? "visible" : "none";
  if (map.getLayer(layerId)) {
    map.setLayoutProperty(layerId, "visibility", visibility);
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

  setLayerVisibility(map, `layer:${layer.id}`, visible);
  setLayerVisibility(map, `layer:${layer.id}:outline`, visible);
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
    setLayerVisibility(map, `layer:${layer.id}`, visible);
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

export function renderEditOverlay(map: Map | null, editState: EditState): void {
  if (!map) {
    return;
  }

  const editPolygonSource = map.getSource(editPolygonSourceId) as
    | GeoJSONSource
    | undefined;
  const editVerticesSource = map.getSource(editVerticesSourceId) as
    | GeoJSONSource
    | undefined;

  if (editState.mode === "idle") {
    editPolygonSource?.setData(emptyFc);
    editVerticesSource?.setData(emptyFc);
    return;
  }

  editPolygonSource?.setData(buildPolygonFC(editState.session));
  editVerticesSource?.setData(
    buildVerticesFC(editState.session.draft.geometry),
  );
}

function toMapLibreFeatureCollection(
  featureCollection: ApiFeatureCollection,
): FeatureCollection<Geometry, FeatureProperties> {
  return {
    type: "FeatureCollection",
    features: featureCollection.features.map((feature) => ({
      type: "Feature",
      id: feature.id,
      geometry: feature.geometry,
      properties: {
        ...(feature.properties ?? {}),
        __id: feature.id,
        __version: feature.version,
      },
    })),
  };
}

function buildPolygonFC(
  session: EditSession,
): FeatureCollection<Geometry, FeatureProperties> {
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: session.draft.geometry,
        properties: session.draft.properties,
      },
    ],
  };
}

function buildVerticesFC(
  polygon: PolygonGeometry,
): FeatureCollection<Geometry, FeatureProperties> {
  const features: FeatureCollection<Geometry, FeatureProperties>["features"] =
    [];
  let ringIndex = 0;

  for (const ring of polygon.coordinates) {
    let vertexIndex = 0;
    for (const point of ring.slice(0, ring.length - 1)) {
      features.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: point },
        properties: { ring: ringIndex, i: vertexIndex },
      });
      vertexIndex++;
    }
    ringIndex++;
  }

  return { type: "FeatureCollection", features };
}
