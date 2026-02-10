import { http } from "@/api/http";
import { AxiosError } from "axios";
import {
  isApiFeatureCollectionOut,
  isApiFeatureOut,
  isDeleteFeatureOut,
} from "@/parsing/features";
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

export type PatchFeatureIn = {
  version: number;
  properties: Record<string, unknown>;
  geometry: GeoJSON.Geometry;
};
export type DeleteFeatureIn = { version: number };
export type DeleteFeatureOut = { status: "deleted"; featureId: string };

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

export async function fetchLayerFeatureById(
  layerId: string,
  featureId: string,
): Promise<ApiFeatureOut> {
  try {
    const url = `/api/v1/layers/${layerId}/features/${featureId}`;
    const response = await http.get(url);
    const raw = response.data as unknown;
    if (isApiFeatureOut(raw)) {
      return raw;
    }
    throw new Error("Пришел объект неизвестного типа");
  } catch (err: unknown) {
    throwHttpErrorIfAxiosError(err);
    throw err;
  }
}

function throwHttpErrorIfAxiosError(error: unknown): void {
  if (
    error instanceof AxiosError &&
    typeof error?.response?.status === "number"
  ) {
    throw new HttpError(error?.response?.status, error?.response?.data);
  }
}
