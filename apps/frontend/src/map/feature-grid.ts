import type { MapBbox, TileDescriptor } from "@/contracts/map-cache";

const MIN_LON = -180;
const MAX_LON = 180;
const MIN_LAT = -90;
const MAX_LAT = 90;
const EDGE_EPS = 1e-9;

export function getGridStepForZoom(zoom: number): number {
  if (zoom < 10) {
    return 0;
  }
  if (zoom < 13) {
    return 0.2;
  }
  if (zoom < 16) {
    return 0.05;
  }
  return 0.01;
}

export function getTilesForViewport(
  bbox: MapBbox,
  zoom: number,
): TileDescriptor[] {
  const step = getGridStepForZoom(zoom);
  if (step <= 0) {
    return [];
  }

  const normalizedBbox = clampBboxToWorld(bbox);
  const minX = coordToIndex(normalizedBbox[0], MIN_LON, step);
  const maxX = coordToIndex(normalizedBbox[2] - EDGE_EPS, MIN_LON, step);
  const minY = coordToIndex(normalizedBbox[1], MIN_LAT, step);
  const maxY = coordToIndex(normalizedBbox[3] - EDGE_EPS, MIN_LAT, step);
  const descriptors: TileDescriptor[] = [];

  for (let x = minX; x <= maxX; x++) {
    for (let y = minY; y <= maxY; y++) {
      descriptors.push(buildTileDescriptor(x, y, zoom, step));
    }
  }

  return descriptors;
}

function buildTileDescriptor(
  x: number,
  y: number,
  zoom: number,
  step: number,
): TileDescriptor {
  const minLon = clamp(MIN_LON + x * step, MIN_LON, MAX_LON);
  const minLat = clamp(MIN_LAT + y * step, MIN_LAT, MAX_LAT);
  const maxLon = clamp(minLon + step, MIN_LON, MAX_LON);
  const maxLat = clamp(minLat + step, MIN_LAT, MAX_LAT);

  return {
    key: `${zoom}:${x}:${y}`,
    bbox: [minLon, minLat, maxLon, maxLat],
    zoom,
    x,
    y,
    step,
  };
}

function clampBboxToWorld(bbox: MapBbox): MapBbox {
  const minLon = clamp(Math.min(bbox[0], bbox[2]), MIN_LON, MAX_LON);
  const maxLon = clamp(Math.max(bbox[0], bbox[2]), MIN_LON, MAX_LON);
  const minLat = clamp(Math.min(bbox[1], bbox[3]), MIN_LAT, MAX_LAT);
  const maxLat = clamp(Math.max(bbox[1], bbox[3]), MIN_LAT, MAX_LAT);
  return [minLon, minLat, maxLon, maxLat];
}

function coordToIndex(value: number, origin: number, step: number): number {
  return Math.floor((value - origin) / step);
}

function clamp(value: number, minValue: number, maxValue: number): number {
  return Math.min(Math.max(value, minValue), maxValue);
}
