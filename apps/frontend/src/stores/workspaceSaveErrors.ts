import { parseApiError } from "@/api/parseApiError";
import type { SaveRejection } from "@/contracts/workspace-edit";
export type SaveFailureDisposition =
  | { kind: "retryableUnknown" }
  | { kind: "domainRejected" | "stale"; error: SaveRejection }
  | {
      kind: "blocked";
      reason: "access" | "protocol" | "identity";
      code: string;
    };
const domainCodes: Record<string, number> = {
  GEOMETRY_INVALID: 422,
  GEOMETRY_OUTSIDE_AOI: 422,
  GEOMETRY_STRUCTURE_CHANGED: 422,
  FEATURE_NOT_EDITABLE: 422,
  WORK_ORDER_CONTEXT_INVALID: 422,
  MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED: 409,
};
export function classifySaveFailure(
  error: unknown,
  hadUnknownOutcome: boolean,
): SaveFailureDisposition {
  const parsed = parseApiError(error);
  if (
    parsed.kind === "network" ||
    parsed.kind === "timeout" ||
    ((parsed.kind === "api" || parsed.kind === "http") && parsed.status >= 500)
  )
    return { kind: "retryableUnknown" };
  if (parsed.kind === "api") {
    const rejection = {
      status: parsed.status,
      code: parsed.code,
      message: parsed.message,
      correlationId: parsed.correlationId,
    };
    if (parsed.code === "DRAFT_VERSION_STALE" && parsed.status === 409)
      return { kind: "stale", error: rejection };
    if (
      domainCodes[parsed.code] === parsed.status ||
      (parsed.code === "REQUEST_VALIDATION_ERROR" &&
        parsed.status === 422 &&
        !hadUnknownOutcome)
    )
      return { kind: "domainRejected", error: rejection };
    if (
      [
        "AUTH_REQUIRED",
        "USER_INACTIVE",
        "ROLE_NOT_ALLOWED",
        "EDIT_VERSION_NOT_FOUND",
        "SAVE_CONTEXT_CLOSED",
      ].includes(parsed.code)
    )
      return { kind: "blocked", reason: "access", code: parsed.code };
    if (parsed.code === "COMMAND_ID_REUSED")
      return { kind: "blocked", reason: "identity", code: parsed.code };
  }
  return {
    kind: "blocked",
    reason: "protocol",
    code: "SAVE_OUTCOME_UNCONFIRMED",
  };
}
