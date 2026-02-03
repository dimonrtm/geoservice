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
