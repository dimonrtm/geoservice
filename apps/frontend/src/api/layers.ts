import { http } from "@/api/http";
import { AxiosError } from "axios";
type LayerDto = {
  id: string;
  name: string;
  title: string;
  geometryType: string;
  srid: number;
};
type FeatureCollection = { type: "FeatureCollection"; features: unknown[] };
class HttpError extends Error {
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
    const layerDtos = response.data as LayerDto[];
    return layerDtos;
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
}): Promise<FeatureCollection> {
  try {
    let limit = Math.min(args.limit, 5000);
    limit = Math.max(limit, 1);
    const url = `/api/v1/layers/${args.layerId}/features`;
    const response = await http.get(url, {
      params: { bbox: args.bbox.join(","), limit: limit },
      signal: args.signal,
    });
    const featureCollection = response.data as FeatureCollection;
    return featureCollection;
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
