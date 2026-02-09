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

export async function fetchLayers(signal?: AbortSignal): Promise<LayerDto[]> {
  try {
    const response = await http.get("/api/v1/layers", { signal: signal });
    const raw = response.data as unknown;
    console.log(raw);
    if (
      raw &&
      typeof raw === "object" &&
      Array.isArray((raw as { layers: LayerDto[] }).layers)
    ) {
      return (raw as { layers: LayerDto[] }).layers as LayerDto[];
    }
    throw Error("Объект неизвестного типа");
  } catch (err: unknown) {
    if (
      err instanceof AxiosError &&
      typeof err?.response?.status === "number"
    ) {
      throw new HttpError(err?.response?.status, err?.response?.data);
    }
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
    if (
      err instanceof AxiosError &&
      typeof err?.response?.status === "number"
    ) {
      throw new HttpError(err?.response?.status, err?.response?.data);
    }
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
