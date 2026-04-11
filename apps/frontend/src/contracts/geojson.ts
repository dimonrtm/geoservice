import type {
  BBox,
  Feature,
  FeatureCollection,
  Geometry,
  LineString,
  MultiLineString,
  MultiPoint,
  MultiPolygon,
  Point,
  Polygon,
  Position,
} from "geojson";

export type FeatureGeometry = Geometry;
export type PolygonGeometry = Polygon;
export type FeatureProperties = Record<string, unknown>;

export type ApiFeature<
  G extends FeatureGeometry = FeatureGeometry,
  P extends FeatureProperties = FeatureProperties,
> = Feature<G, P> & {
  id: string;
  version: number;
};

export type ApiFeatureCollection<
  G extends FeatureGeometry = FeatureGeometry,
  P extends FeatureProperties = FeatureProperties,
> = Omit<FeatureCollection<G, P>, "features"> & {
  features: ApiFeature<G, P>[];
};

export type PolygonValidationOk = { ok: true; value: PolygonGeometry };
export type PolygonValidationError = {
  ok: false;
  code:
    | "INVALID_COORDINATES"
    | "RING_NOT_CLOSED"
    | "RING_TOO_SHORT"
    | "GEOM_NOT_POLYGON";
  message: string;
};
export type PolygonValidationResult =
  | PolygonValidationOk
  | PolygonValidationError;

export function isRecord(raw: unknown): raw is Record<string, unknown> {
  return typeof raw === "object" && raw !== null;
}

export function isString(x: unknown): x is string {
  return typeof x === "string";
}

export function isFiniteNumber(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

export function toFiniteNumber(x: unknown): number | null {
  const n = typeof x === "number" ? x : typeof x === "string" ? Number(x) : NaN;
  return Number.isFinite(n) ? n : null;
}

export function isFeatureGeometry(value: unknown): value is FeatureGeometry {
  if (!isRecord(value) || !isString(value.type)) {
    return false;
  }

  switch (value.type) {
    case "Point":
      return isPointGeometry(value);
    case "MultiPoint":
      return isMultiPointGeometry(value);
    case "LineString":
      return isLineStringGeometry(value);
    case "MultiLineString":
      return isMultiLineStringGeometry(value);
    case "Polygon":
      return isPolygonGeometry(value);
    case "MultiPolygon":
      return isMultiPolygonGeometry(value);
    default:
      return false;
  }
}

export function isPolygonGeometry(value: unknown): value is PolygonGeometry {
  return (
    isRecord(value) &&
    value.type === "Polygon" &&
    isPolygonCoordinates(value.coordinates)
  );
}

export function clonePolygonGeometry(
  geometry: PolygonGeometry,
): PolygonGeometry {
  const cloneCoordinates: Position[][] = geometry.coordinates.map((ring) =>
    ring.map((point) => point.slice() as Position),
  );
  const cloned: PolygonGeometry = {
    type: "Polygon",
    coordinates: cloneCoordinates,
  };

  if (geometry.bbox) {
    cloned.bbox = geometry.bbox.slice() as BBox;
  }

  return cloned;
}

export function validatePolygonGeometry(
  geom: PolygonGeometry,
): PolygonValidationResult {
  if (geom.type !== "Polygon") {
    return {
      ok: false,
      code: "GEOM_NOT_POLYGON",
      message: "Геометрия не является полигоном",
    };
  }
  if (geom.coordinates.length === 0) {
    return {
      ok: false,
      code: "INVALID_COORDINATES",
      message: "В полигоне должно быть хотя бы одно кольцо",
    };
  }

  for (const ring of geom.coordinates) {
    if (ring.length < 4) {
      return {
        ok: false,
        code: "RING_TOO_SHORT",
        message: "Кольцо полигона должно содержать минимум 4 точки",
      };
    }
    const firstPoint = ring[0];
    const lastPoint = ring[ring.length - 1];
    if (
      firstPoint &&
      lastPoint &&
      (firstPoint[0] !== lastPoint[0] || firstPoint[1] !== lastPoint[1])
    ) {
      return {
        ok: false,
        code: "RING_NOT_CLOSED",
        message: "Все кольца полигона должны быть замкнутыми",
      };
    }
    for (const point of ring) {
      if (!isValidPoint(point)) {
        return {
          ok: false,
          code: "INVALID_COORDINATES",
          message: "Полигон содуржит невалидные координаты",
        };
      }
    }
  }

  return { ok: true, value: geom };
}

function isPointGeometry(value: unknown): value is Point {
  return isRecord(value) && isPosition(value.coordinates);
}

function isMultiPointGeometry(value: unknown): value is MultiPoint {
  return isRecord(value) && isPositionArray(value.coordinates, 1);
}

function isLineStringGeometry(value: unknown): value is LineString {
  return isRecord(value) && isPositionArray(value.coordinates, 2);
}

function isMultiLineStringGeometry(value: unknown): value is MultiLineString {
  if (!isRecord(value)) {
    return false;
  }
  if (!Array.isArray(value.coordinates) || value.coordinates.length === 0) {
    return false;
  }
  return value.coordinates.every((line) => isPositionArray(line, 2));
}

function isMultiPolygonGeometry(value: unknown): value is MultiPolygon {
  if (!isRecord(value)) {
    return false;
  }
  if (!Array.isArray(value.coordinates) || value.coordinates.length === 0) {
    return false;
  }
  return value.coordinates.every((polygon) => isPolygonCoordinates(polygon));
}

function isPolygonCoordinates(value: unknown): value is Polygon["coordinates"] {
  if (!Array.isArray(value) || value.length === 0) {
    return false;
  }
  return value.every((ring) => isPositionArray(ring, 4));
}

function isPositionArray(
  value: unknown,
  minLength: number,
): value is Position[] {
  return (
    Array.isArray(value) &&
    value.length >= minLength &&
    value.every((point) => isPosition(point))
  );
}

function isPosition(value: unknown): value is Position {
  return (
    Array.isArray(value) &&
    value.length >= 2 &&
    isFiniteNumber(value[0]) &&
    isFiniteNumber(value[1])
  );
}

function isValidPoint(point: Position): boolean {
  return (
    point.every((coord) => Number.isFinite(coord)) &&
    (point[0] as number) >= -180 &&
    (point[0] as number) <= 180 &&
    (point[1] as number) >= -90 &&
    (point[1] as number) <= 90
  );
}
