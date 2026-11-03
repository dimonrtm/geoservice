import type { Geometry, Position } from "geojson";
import type { TileDescriptor } from "@/contracts/map-cache";

type Bounds = TileDescriptor["bbox"];

// Slab intersection on the closed rectangle, including touches at a corner.
function segmentIntersects(start: Position, end: Position, bounds: Bounds) {
  let enter = 0;
  let leave = 1;
  for (const axis of [0, 1] as const) {
    const origin = start[axis]!;
    const delta = end[axis]! - origin;
    const minimum = bounds[axis];
    const maximum = bounds[axis + 2]!;
    if (delta === 0) {
      if (origin < minimum || origin > maximum) return false;
      continue;
    }
    const a = (minimum - origin) / delta;
    const b = (maximum - origin) / delta;
    enter = Math.max(enter, Math.min(a, b));
    leave = Math.min(leave, Math.max(a, b));
    if (enter > leave) return false;
  }
  return true;
}

function lineIntersects(line: Position[], bounds: Bounds) {
  return line.some((point, i) =>
    segmentIntersects(line[i - 1] ?? point, point, bounds),
  );
}

function ringContainsCorner(ring: Position[], [x, y]: Bounds) {
  let inside = false;
  for (let i = 1; i < ring.length; i++) {
    const a = ring[i - 1]!;
    const b = ring[i]!;
    if (
      a[1]! > y !== b[1]! > y &&
      x < a[0]! + ((y - a[1]!) * (b[0]! - a[0]!)) / (b[1]! - a[1]!)
    )
      inside = !inside;
  }
  return inside;
}

function polygonIntersects(rings: Position[][], bounds: Bounds) {
  if (rings.some((ring) => lineIntersects(ring, bounds))) return true;
  const [outer, ...holes] = rings;
  return (
    !!outer &&
    ringContainsCorner(outer, bounds) &&
    !holes.some((ring) => ringContainsCorner(ring, bounds))
  );
}

export function geometryIntersectsTile(
  geometry: Geometry,
  bounds: Bounds,
): boolean {
  switch (geometry.type) {
    case "Point":
      return segmentIntersects(
        geometry.coordinates,
        geometry.coordinates,
        bounds,
      );
    case "MultiPoint":
      return geometry.coordinates.some((p) => segmentIntersects(p, p, bounds));
    case "LineString":
      return lineIntersects(geometry.coordinates, bounds);
    case "MultiLineString":
      return geometry.coordinates.some((line) => lineIntersects(line, bounds));
    case "Polygon":
      return polygonIntersects(geometry.coordinates, bounds);
    case "MultiPolygon":
      return geometry.coordinates.some((polygon) =>
        polygonIntersects(polygon, bounds),
      );
    case "GeometryCollection":
      return geometry.geometries.some((item) =>
        geometryIntersectsTile(item, bounds),
      );
  }
}
