import type { PolygonGeometry } from "@/contracts/geojson";
import type { BBox, Position } from "geojson";

export function movePolygonVertex(
  polygon: PolygonGeometry,
  ringIndex: number,
  vertexIndex: number,
  lng: number,
  lat: number,
): PolygonGeometry {
  const nextCoords = copyPolygon(polygon);
  const nextRing = nextCoords[ringIndex];
  if (!nextRing) {
    return polygon;
  }

  nextRing[vertexIndex] = [lng, lat];
  if (vertexIndex === 0 && nextRing.length >= 1) {
    nextRing[nextRing.length - 1] = [lng, lat];
  }

  return clonePolygonWithCoordinates(polygon, nextCoords);
}

export function removePolygonVertex(
  polygon: PolygonGeometry,
  ringIndex: number,
  vertexIndex: number,
): PolygonGeometry | null {
  const nextCoords = copyPolygon(polygon);
  const nextRing = nextCoords[ringIndex];
  if (!nextRing) {
    return null;
  }

  const unclosedRing = nextRing.slice(0, -1);
  if (unclosedRing.length <= 3) {
    return null;
  }

  unclosedRing.splice(vertexIndex, 1);
  const firstPoint = unclosedRing[0];
  if (!firstPoint) {
    return null;
  }

  nextCoords[ringIndex] = [...unclosedRing, copyPosition(firstPoint)];
  return clonePolygonWithCoordinates(polygon, nextCoords);
}

export function findNearestRingIndex(
  polygon: PolygonGeometry,
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
  polygon: PolygonGeometry,
  ringIndex: number,
  lng: number,
  lat: number,
): PolygonGeometry | null {
  const nextCoords = copyPolygon(polygon);
  const nextRing = nextCoords[ringIndex];
  if (!nextRing) {
    return null;
  }

  const unclosedRing = nextRing.slice(0, -1);
  if (unclosedRing.length < 3) {
    return null;
  }

  let minDistance = Number.POSITIVE_INFINITY;
  let bestSegmentIndex = 0;
  for (
    let segmentIndex = 0;
    segmentIndex < unclosedRing.length;
    segmentIndex++
  ) {
    const start = toLngLat(unclosedRing[segmentIndex]);
    const end = toLngLat(
      unclosedRing[(segmentIndex + 1) % unclosedRing.length],
    );
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
      bestSegmentIndex = segmentIndex;
    }
  }

  unclosedRing.splice(bestSegmentIndex + 1, 0, [lng, lat]);
  const firstPoint = unclosedRing[0];
  if (!firstPoint) {
    return null;
  }

  nextCoords[ringIndex] = [...unclosedRing, copyPosition(firstPoint)];
  return clonePolygonWithCoordinates(polygon, nextCoords);
}

function clonePolygonWithCoordinates(
  polygon: PolygonGeometry,
  coordinates: Position[][],
): PolygonGeometry {
  const cloned: PolygonGeometry = {
    type: "Polygon",
    coordinates,
  };

  if (polygon.bbox) {
    cloned.bbox = polygon.bbox.slice() as BBox;
  }

  return cloned;
}

function copyPolygon(polygon: PolygonGeometry): Position[][] {
  return polygon.coordinates.map((ring) =>
    ring.map((point) => copyPosition(point)),
  );
}

function copyPosition(point: Position): Position {
  return point.slice() as Position;
}

function getRingDistanceToPoint(
  ring: Position[],
  lng: number,
  lat: number,
): number | null {
  const unclosedRing = ring.slice(0, -1);
  if (unclosedRing.length < 3) {
    return null;
  }

  let minDistance = Number.POSITIVE_INFINITY;
  for (
    let segmentIndex = 0;
    segmentIndex < unclosedRing.length;
    segmentIndex++
  ) {
    const start = toLngLat(unclosedRing[segmentIndex]);
    const end = toLngLat(
      unclosedRing[(segmentIndex + 1) % unclosedRing.length],
    );
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
    }
  }

  return minDistance;
}

function toLngLat(point: Position | undefined): [number, number] | null {
  if (!isValidPosition(point)) {
    return null;
  }

  const [lng, lat] = point;
  if (typeof lng !== "number" || typeof lat !== "number") {
    return null;
  }

  return [lng, lat];
}

function isValidPosition(point: Position | undefined): point is Position {
  return (
    Array.isArray(point) &&
    Number.isFinite(point[0]) &&
    Number.isFinite(point[1])
  );
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
