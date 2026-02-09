import { http } from "@/api/http";
import { AxiosError } from "axios";
export type LayerDto = {
  id: string;
  name: string;
  title: string;
  geometryType: string;
  srid: number;
};
export type FeatureCollection = {
  type: "FeatureCollection";
  features: unknown[];
};

export class HttpError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown) {
    super();
    this.status = status;
    this.body = body;
  }
}

export type ApiFeatureOut<
  G extends GeoJSON.Geometry = GeoJSON.Geometry,
  P extends GeoJSON.GeoJsonProperties = GeoJSON.GeoJsonProperties,
> = GeoJSON.Feature<G, P> & {
  id: string;
  version: number;
};

export type ApiFeatureCollectionOut<
  G extends GeoJSON.Geometry = GeoJSON.Geometry,
  P extends GeoJSON.GeoJsonProperties = GeoJSON.GeoJsonProperties,
> = Omit<GeoJSON.FeatureCollection<G, P>, "features"> & {
  features: ApiFeatureOut<G, P>[];
};

type PatchFeatureIn = {
  version: number;
  properties: Record<string, unknown>;
  geometry: GeoJSON.Geometry;
};
type DeleteFeatureIn = { version: number };
type DeleteFeatureOut = { status: "deleted"; featureId: string };

export async function fetchLayers(signal?: AbortSignal): Promise<LayerDto[]> {
  try {
    const response = await http.get("/api/v1/layers", { signal: signal });
    const raw = response.data as unknown;
    if (
      raw &&
      typeof raw === "object" &&
      Array.isArray((raw as { layers: LayerDto[] }).layers)
    ) {
      return (raw as { layers: LayerDto[] }).layers as LayerDto[];
    }
    throw Error("Объект неизвестного типа");
  } catch (err: unknown) {
    throwHttpErrorIfAxiosError(err);
    throw err;
  }
}

export async function fetchLayerFeaturesByBbox(args: {
  layerId: string;
  bbox: [number, number, number, number];
  limit: number;
  signal?: AbortSignal;
}): Promise<ApiFeatureCollectionOut> {
  try {
    let limit = Math.min(args.limit, 5000);
    limit = Math.max(limit, 1);
    const url = `/api/v1/layers/${args.layerId}/features`;
    const response = await http.get(url, {
      params: { bbox: args.bbox.join(","), limit: limit },
      signal: args.signal,
    });
    const raw = response.data as unknown;
    if (isApiFeatureCollectionOut(raw)) {
      return raw;
    }
    throw Error("Пришел объект неожиданного типа");
  } catch (err: unknown) {
    throwHttpErrorIfAxiosError(err);
    throw err;
  }
}

export async function patchLayerFeature(
  layerId: string,
  featureId: string,
  body: PatchFeatureIn,
  signal?: AbortSignal,
): Promise<ApiFeatureOut> {
  try {
    const url = `/api/v1/layers/${layerId}/features/${featureId}`;
    const response = await http.patch(url, body, { signal: signal });
    const raw = response.data as unknown;
    if (isApiFeatureOut((raw as { feature: unknown }).feature)) {
      return (raw as { feature: unknown }).feature as ApiFeatureOut;
    }
    throw new Error("Пришел объект неожиданного типа");
  } catch (err: unknown) {
    throwHttpErrorIfAxiosError(err);
    throw err;
  }
}

export async function deleteLayerFeature(
  layerId: string,
  featureId: string,
  body: DeleteFeatureIn,
  signal?: AbortSignal,
): Promise<DeleteFeatureOut> {
  try {
    const url = `/api/v1/layers/${layerId}/features/${featureId}`;
    const response = await http.delete(url, { data: body, signal: signal });
    const raw = response.data as unknown;
    if (isDeleteFeatureOut(raw)) {
      return raw;
    }
    throw new Error("Пришел объект неожиданного типа");
  } catch (err: unknown) {
    throwHttpErrorIfAxiosError(err);
    throw err;
  }
}

function isRecord(raw: unknown): raw is Record<string, unknown> {
  return typeof raw === "object" && raw !== null;
}

function isApiFeatureOut(x: unknown): x is ApiFeatureOut {
  if (!isRecord(x)) return false;
  if (x["type"] !== "Feature") return false;
  if (typeof x["id"] !== "string") return false;
  if (typeof x["version"] !== "number" || !Number.isFinite(x["version"]))
    return false;
  if (!("geometry" in x) || !isRecord(x["geometry"])) return false;
  if (!("properties" in x) || !isRecord(x["properties"])) return false;
  return true;
}

export function isApiFeatureCollectionOut(
  x: unknown,
): x is ApiFeatureCollectionOut {
  if (!isRecord(x)) return false;
  if (x["type"] !== "FeatureCollection") return false;
  if (!Array.isArray(x["features"])) return false;
  return x["features"].every(isApiFeatureOut);
}

function isDeleteFeatureOut(x: unknown): x is DeleteFeatureOut {
  if (!isRecord(x)) {
    return false;
  }
  if (x["status"] !== "deleted") {
    return false;
  }
  if (!("featureId" in x) || typeof x["featureId"] !== "string") {
    return false;
  }
  return true;
}

function throwHttpErrorIfAxiosError(error: unknown): void {
  if (
    error instanceof AxiosError &&
    typeof error?.response?.status === "number"
  ) {
    throw new HttpError(error?.response?.status, error?.response?.data);
  }
}
