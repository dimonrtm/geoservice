import {
  type ApiFeature,
  type ApiFeatureCollection,
  type FeatureGeometry,
  type FeatureProperties,
  isFeatureGeometry,
  isFiniteNumber,
  isRecord,
  isString,
} from "@/contracts/geojson";

export type LayerDto = {
  id: string;
  name: string;
  title: string;
  geometryType: string;
  srid: number;
};

export type LayersResponse = {
  layers: LayerDto[];
};

export type FeatureCollectionMeta = {
  bbox: [number, number, number, number];
  limit: number;
  returned: number;
  truncated: boolean;
  sort: "id:asc";
  next_cursor: string | null;
};

export type PatchFeatureIn<G extends FeatureGeometry = FeatureGeometry> = {
  version: number;
  properties: FeatureProperties;
  geometry: G;
};

export type CreateFeatureIn<G extends FeatureGeometry = FeatureGeometry> = {
  properties: FeatureProperties;
  geometry: G;
};

export type DeleteFeatureIn = {
  version: number;
};

export type DeleteFeatureOut = {
  status: "deleted";
  featureId: string;
};

export type PatchFeatureSuccessResponse<
  G extends FeatureGeometry = FeatureGeometry,
> = {
  feature: ApiFeature<G>;
};

export type VersionMismatchBody = {
  type: "VERSION_MISMATCH";
  featureId: string;
  requestVersion: number;
  currentVersion: number;
  message: string;
};

export type ApiFeatureCollectionResponse = ApiFeatureCollection & {
  meta: FeatureCollectionMeta;
};

export function isLayersResponse(raw: unknown): raw is LayersResponse {
  return (
    isRecord(raw) &&
    Array.isArray(raw.layers) &&
    raw.layers.every((layer) => isLayerDto(layer))
  );
}

export function isApiFeature(raw: unknown): raw is ApiFeature {
  return (
    isRecord(raw) &&
    raw.type === "Feature" &&
    isString(raw.id) &&
    isFiniteNumber(raw.version) &&
    isFeatureGeometry(raw.geometry) &&
    isFeatureProperties(raw.properties)
  );
}

export function isApiFeatureCollection(
  raw: unknown,
): raw is ApiFeatureCollection {
  return (
    isRecord(raw) &&
    raw.type === "FeatureCollection" &&
    Array.isArray(raw.features) &&
    raw.features.every((feature) => isApiFeature(feature))
  );
}

export function isApiFeatureCollectionResponse(
  raw: unknown,
): raw is ApiFeatureCollectionResponse {
  if (!isRecord(raw)) {
    return false;
  }
  const candidate: Record<string, unknown> = raw;
  const meta = candidate["meta"];
  if (!isApiFeatureCollection(candidate)) {
    return false;
  }
  return isFeatureCollectionMeta(meta);
}

export function isDeleteFeatureOut(raw: unknown): raw is DeleteFeatureOut {
  return isRecord(raw) && raw.status === "deleted" && isString(raw.featureId);
}

export function isPatchFeatureSuccessResponse(
  raw: unknown,
): raw is PatchFeatureSuccessResponse {
  return isRecord(raw) && isApiFeature(raw.feature);
}

export function isVersionMismatchBody(
  raw: unknown,
): raw is VersionMismatchBody {
  return (
    isRecord(raw) &&
    raw.type === "VERSION_MISMATCH" &&
    isString(raw.featureId) &&
    isFiniteNumber(raw.requestVersion) &&
    isFiniteNumber(raw.currentVersion) &&
    isString(raw.message)
  );
}

function isLayerDto(raw: unknown): raw is LayerDto {
  return (
    isRecord(raw) &&
    isString(raw.id) &&
    isString(raw.name) &&
    isString(raw.title) &&
    isString(raw.geometryType) &&
    isFiniteNumber(raw.srid)
  );
}

function isFeatureProperties(raw: unknown): raw is FeatureProperties {
  return isRecord(raw);
}

function isFeatureCollectionMeta(raw: unknown): raw is FeatureCollectionMeta {
  return (
    isRecord(raw) &&
    Array.isArray(raw.bbox) &&
    raw.bbox.length === 4 &&
    raw.bbox.every((value) => isFiniteNumber(value)) &&
    isFiniteNumber(raw.limit) &&
    isFiniteNumber(raw.returned) &&
    typeof raw.truncated === "boolean" &&
    raw.sort === "id:asc" &&
    (raw.next_cursor === null || isString(raw.next_cursor))
  );
}
