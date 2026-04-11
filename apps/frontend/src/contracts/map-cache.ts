import type { ApiFeature } from "@/contracts/geojson";

export type MapBbox = [number, number, number, number];

export type TileKey = string;

export type TileDescriptor = {
  key: TileKey;
  bbox: MapBbox;
  zoom: number;
  x: number;
  y: number;
  step: number;
};

export type CachedTile = {
  key: TileKey;
  bbox: MapBbox;
  loadedAt: number;
  featureIds: string[];
};

export type TileLoadState = "idle" | "loading" | "ready" | "error";

export type TileEntry = {
  state: TileLoadState;
  data: CachedTile | null;
  error?: string;
};

export type FeatureIndex = Map<string, ApiFeature>;
export type TileIndex = Map<TileKey, TileEntry>;
