import {
  type ApiFeatureOut,
  type ApiFeatureCollectionOut,
  type DeleteFeatureOut,
} from "@/api/layers";
import { isRecord, isString, isFiniteNumber } from "@/parsing/common";

export function isApiFeatureOut(x: unknown): x is ApiFeatureOut {
  if (!isRecord(x)) return false;
  if (x["type"] !== "Feature") return false;
  if (!isString(x["id"])) return false;
  if (!isFiniteNumber(x["version"])) return false;
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

export function isDeleteFeatureOut(x: unknown): x is DeleteFeatureOut {
  if (!isRecord(x)) {
    return false;
  }
  if (x["status"] !== "deleted") {
    return false;
  }
  if (!("featureId" in x) || !isString(x["featureId"])) {
    return false;
  }
  return true;
}
