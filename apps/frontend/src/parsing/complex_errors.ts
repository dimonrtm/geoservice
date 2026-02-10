import { type VersionMismatchBody } from "@/stores/edit";
import { isRecord, isString, isFiniteNumber } from "@/parsing/common";

export function isVersionMismatchBody(x: unknown): x is VersionMismatchBody {
  if (!isRecord(x)) {
    return false;
  }
  if (x["type"] !== "VERSION_MISMATCH") {
    return false;
  }
  if (!isString(x["featureId"])) {
    return false;
  }
  if (!isFiniteNumber(x["requestVersion"])) {
    return false;
  }
  if (!isFiniteNumber(x["currentVersion"])) {
    return false;
  }
  if (!isString(x["message"])) {
    return false;
  }
  return true;
}
