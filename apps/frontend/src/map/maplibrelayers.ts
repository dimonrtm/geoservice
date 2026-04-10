import { Map, type GeoJSONSource } from "maplibre-gl";
import type { LayerDto, ApiFeatureCollectionOut } from "@/api/layers";
import type { FeatureCollection, GeoJsonProperties, Geometry } from "geojson";
import { type EditSession, type EditState } from "@/stores/edit";
export type Bbox = [number, number, number, number];
export type VersionIndex = Record<string, number>;

const emptyFc: FeatureCollection<Geometry, GeoJsonProperties> = {
  type: "FeatureCollection",
  features: [],
};
const editPolygonSourceId = "edit:polygon";
const editVerticesSourceId = "edit:vertices";

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

export function ensureEditSource(map: Map | null): void {
  if (!map) {
    return;
  }
  const editPolygonSource = map.getSource(editPolygonSourceId);
  if (!editPolygonSource) {
    map.addSource(editPolygonSourceId, { type: "geojson", data: emptyFc });
  }
  const editVerticesSource = map.getSource(editVerticesSourceId);
  if (!editVerticesSource) {
    map.addSource(editVerticesSourceId, { type: "geojson", data: emptyFc });
  }
}

export function ensureEditLayer(map: Map | null): void {
  if (!map) {
    return;
  }

  const editPolygonFillId: string = "edit:polygon:fill";
  const editPolygonOutlineId: string = "edit:polygon:outline";
  const editVerticesPointId: string = "edit:vertices:point";
  const editPolygonFill = map.getLayer(editPolygonFillId);
  if (!editPolygonFill) {
    map.addLayer({
      id: editPolygonFillId,
      type: "fill",
      source: editPolygonSourceId,
      paint: { "fill-color": "#FF0000", "fill-opacity": 0.25 },
    });
  }
  const editPolygonOutline = map.getLayer(editPolygonOutlineId);
  if (!editPolygonOutline) {
    map.addLayer({
      id: editPolygonOutlineId,
      type: "line",
      source: editPolygonSourceId,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-width": 2, "line-color": "#FF0000" },
    });
  }
  const editVerticesPoint = map.getLayer(editVerticesPointId);
  if (!editVerticesPoint) {
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

function toMapLibreFeatureCollection(
  featureCollection: ApiFeatureCollectionOut,
): GeoJSON.FeatureCollection<GeoJSON.Geometry, GeoJSON.GeoJsonProperties> {
  return {
    type: "FeatureCollection",
    features: featureCollection.features.map((feature) => ({
      type: "Feature",
      id: feature.id,
      geometry: feature.geometry as GeoJSON.Geometry,
      properties: {
        ...(feature.properties ?? {}),
        __id: feature.id,
        __version: feature.version,
      } as GeoJSON.GeoJsonProperties,
    })),
  };
}

export function setSourceData(
  map: Map | null,
  sourceId: string,
  featureCollection: ApiFeatureCollectionOut,
) {
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

function buildPolygonFC(
  session: EditSession,
): FeatureCollection<Geometry, GeoJsonProperties> {
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
  polygon: GeoJSON.Polygon,
): FeatureCollection<Geometry, GeoJsonProperties> {
  const features: GeoJSON.Feature[] = [];
  let ringIndex = 0;
  for (const ring of polygon.coordinates) {
    let vertexIndex = 0;
    for (const point of ring.slice(0, ring.length - 1)) {
      const feature: GeoJSON.Feature = {
        type: "Feature",
        geometry: { type: "Point", coordinates: point },
        properties: { ring: ringIndex, i: vertexIndex },
      };
      features.push(feature);
      vertexIndex++;
    }
    ringIndex++;
  }
  return { type: "FeatureCollection", features: features };
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
    if (editPolygonSource) {
      editPolygonSource.setData(emptyFc);
    }
    if (editVerticesSource) {
      editVerticesSource.setData(emptyFc);
    }
  } else if (editState.mode === "editing") {
    const polygonFc = buildPolygonFC(editState.session);
    const verticesFc = buildVerticesFC(editState.session.draft.geometry);
    if (editPolygonSource) {
      editPolygonSource.setData(polygonFc);
    }
    if (editVerticesSource) {
      editVerticesSource.setData(verticesFc);
    }
  }
}

export function movePolygonVertex(
  polygon: GeoJSON.Polygon,
  ring: number,
  i: number,
  lng: number,
  lat: number,
): GeoJSON.Polygon {
  const nextCoords: GeoJSON.Position[][] = copyPolygon(polygon);
  const nextRing = nextCoords[ring];
  if (!nextRing) {
    return polygon;
  }
  nextRing[i] = [lng, lat];
  if (i === 0 && nextRing.length >= 1) {
    nextRing[nextRing.length - 1] = [lng, lat];
  }
  const out: GeoJSON.Polygon = { type: "Polygon", coordinates: nextCoords };
  if (polygon.bbox) {
    out.bbox = polygon.bbox.slice() as GeoJSON.BBox;
  }
  return out;
}

export function removePolygonVertex(
  polygon: GeoJSON.Polygon,
  ringIndex: number,
  vertexIndex: number,
): GeoJSON.Polygon | null {
  const nextCoords: GeoJSON.Position[][] = copyPolygon(polygon);
  const nextRing = nextCoords[ringIndex];
  if (!nextRing) {
    return null;
  }
  const uncloseRing = nextRing.slice(0, -1);
  if (uncloseRing.length <= 3) {
    return null;
  }
  uncloseRing.splice(vertexIndex, 1);
  const firstPoint = uncloseRing[0];
  if (!firstPoint) {
    return null;
  }
  nextCoords[ringIndex] = [
    ...uncloseRing,
    firstPoint.slice() as GeoJSON.Position,
  ];
  const out: GeoJSON.Polygon = { type: "Polygon", coordinates: nextCoords };
  if (polygon.bbox) {
    out.bbox = polygon.bbox.slice() as GeoJSON.BBox;
  }
  return out;
}

function copyPolygon(polygon: GeoJSON.Polygon): GeoJSON.Position[][] {
  return polygon.coordinates.map((ring) =>
    ring.map((point) => point.slice() as GeoJSON.Position),
  );
}

export function findNearestRingIndex(
  polygon: GeoJSON.Polygon,
  lng: number,
  lat: number,
): number | null {
  let nearestRingIndex: number | null = null;
  let minDistance = Number.POSITIVE_INFINITY;

  for (let ringIndex = 0; ringIndex < polygon.coordinates.length; ringIndex++) {
    const ring = polygon.coordinates[ringIndex];
    if (!ring) {
      continue;
    }
    const distance = getRingDistanceToPoint(ring, lng, lat);
    if (distance === null) {
      continue;
    }
    if (distance < minDistance) {
      minDistance = distance;
      nearestRingIndex = ringIndex;
    }
  }

  return nearestRingIndex;
}

export function insertVertexOnNearestSegment(
  polygon: GeoJSON.Polygon,
  ringIndex: number,
  lng: number,
  lat: number,
): GeoJSON.Polygon | null {
  const nextCoords: GeoJSON.Position[][] = copyPolygon(polygon);
  const nextRing = nextCoords[ringIndex];
  if (!nextRing) {
    return null;
  }
  const uncloseRing = nextRing.slice(0, -1);
  if (uncloseRing.length < 3) {
    return null;
  }
  let minDistance = Number.MAX_VALUE;
  let bestJ: number = 0;
  for (let j = 0; j < uncloseRing.length; j++) {
    const u_j = uncloseRing[j];
    const u_j1 = uncloseRing[(j + 1) % uncloseRing.length];
    const start = toLngLat(u_j);
    const end = toLngLat(u_j1);
    if (!start || !end) {
      return null;
    }
    const distance = getDistanceToSegment(
      start[0],
      start[1],
      end[0],
      end[1],
      lng,
      lat,
    );
    if (distance < minDistance) {
      minDistance = distance;
      bestJ = j;
    }
  }
  uncloseRing.splice(bestJ + 1, 0, [lng, lat]);
  const firstPoint = uncloseRing[0];
  if (!firstPoint) {
    return null;
  }
  nextCoords[ringIndex] = [
    ...uncloseRing,
    firstPoint.slice() as GeoJSON.Position,
  ];
  const out: GeoJSON.Polygon = { type: "Polygon", coordinates: nextCoords };
  if (polygon.bbox) {
    out.bbox = polygon.bbox.slice() as GeoJSON.BBox;
  }
  return out;
}

function getRingDistanceToPoint(
  ring: GeoJSON.Position[],
  lng: number,
  lat: number,
): number | null {
  const unclosedRing = ring.slice(0, -1);
  if (unclosedRing.length < 3) {
    return null;
  }

  let minDistance = Number.POSITIVE_INFINITY;
  for (let j = 0; j < unclosedRing.length; j++) {
    const start = unclosedRing[j];
    const end = unclosedRing[(j + 1) % unclosedRing.length];
    const startCoords = toLngLat(start);
    const endCoords = toLngLat(end);
    if (!startCoords || !endCoords) {
      return null;
    }
    const distance = getDistanceToSegment(
      startCoords[0],
      startCoords[1],
      endCoords[0],
      endCoords[1],
      lng,
      lat,
    );
    if (distance < minDistance) {
      minDistance = distance;
    }
  }

  return minDistance;
}

function isValidPosition(
  point: GeoJSON.Position | undefined,
): point is GeoJSON.Position {
  return (
    Array.isArray(point) &&
    Number.isFinite(point[0]) &&
    Number.isFinite(point[1])
  );
}

function toLngLat(
  point: GeoJSON.Position | undefined,
): [number, number] | null {
  if (!isValidPosition(point)) {
    return null;
  }
  const [lng, lat] = point;
  if (typeof lng !== "number" || typeof lat !== "number") {
    return null;
  }
  return [lng, lat];
}

function getDistanceToSegment(
  ax: number,
  ay: number,
  bx: number,
  by: number,
  x: number,
  y: number,
): number {
  const abx = bx - ax;
  const aby = by - ay;
  const abSquared = abx * abx + aby * aby;
  if (abSquared === 0) {
    return Math.hypot(x - ax, y - ay);
  }

  const apx = x - ax;
  const apy = y - ay;
  const projection = (apx * abx + apy * aby) / abSquared;
  const clampedProjection = Math.max(0, Math.min(1, projection));
  const closestX = ax + abx * clampedProjection;
  const closestY = ay + aby * clampedProjection;
  return Math.hypot(x - closestX, y - closestY);
}
