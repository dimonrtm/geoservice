import { http } from "@/api/http";
import { AxiosError } from "axios";
import {
  type CreateFeatureIn,
  isApiFeature,
  isApiFeatureCollection,
  isDeleteFeatureOut,
  isLayersResponse,
  isPatchFeatureSuccessResponse,
  type DeleteFeatureIn,
  type DeleteFeatureOut,
  type LayerDto,
  type PatchFeatureIn,
} from "@/contracts/api";
import type { ApiFeature, ApiFeatureCollection } from "@/contracts/geojson";

export class HttpError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown) {
    super();
    this.status = status;
    this.body = body;
  }
}

export async function fetchLayers(signal?: AbortSignal): Promise<LayerDto[]> {
  try {
    const response = await http.get("/api/v1/layers", { signal: signal });
    const raw = response.data as unknown;
    if (isLayersResponse(raw)) {
      return raw.layers;
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
}): Promise<ApiFeatureCollection> {
  try {
    let limit = Math.min(args.limit, 5000);
    limit = Math.max(limit, 1);
    const url = `/api/v1/layers/${args.layerId}/features`;
    const response = await http.get(url, {
      params: { bbox: args.bbox.join(","), limit: limit },
      signal: args.signal,
    });
    const raw = response.data as unknown;
    if (isApiFeatureCollection(raw)) {
      return raw;
    }
    throw Error("Пришел объект неожиданного типа");
  } catch (err: unknown) {
    throwHttpErrorIfAxiosError(err);
    throw err;
  }
}

export async function createLayerFeature(
  layerId: string,
  body: CreateFeatureIn,
  signal?: AbortSignal,
): Promise<ApiFeature> {
  try {
    const url = `/api/v1/layers/${layerId}/features`;
    const response = await http.post(url, body, { signal });
    const raw = response.data as unknown;
    if (isApiFeature(raw)) {
      return raw;
    }
    throw new Error("Unexpected feature payload");
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
): Promise<ApiFeature> {
  try {
    const url = `/api/v1/layers/${layerId}/features/${featureId}`;
    const response = await http.patch(url, body, { signal: signal });
    const raw = response.data as unknown;
    if (isPatchFeatureSuccessResponse(raw)) {
      return raw.feature;
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
): Promise<ApiFeature> {
  try {
    const url = `/api/v1/layers/${layerId}/features/${featureId}`;
    const response = await http.get(url);
    const raw = response.data as unknown;
    if (isApiFeature(raw)) {
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
