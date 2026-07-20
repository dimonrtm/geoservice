import { describe, expect, it } from "vitest";

import type { ParsedApiError } from "@/contracts/api-error";
import {
  presentLoginError,
  presentSessionError,
  presentWorkOrdersLoadError,
  presentWorkspaceOpenError,
  presentWorkspaceRestoreError,
} from "@/errors/apiErrorPresentations";

function api(
  code: string,
  status: number,
  message = `Причина ${code}`,
): ParsedApiError {
  return { kind: "api", code, status, message, correlationId: "request-id" };
}

const network: ParsedApiError = {
  kind: "network",
  status: null,
  correlationId: null,
};

describe("api error presentations", () => {
  it("keeps invalid credentials actionable through the existing form", () => {
    expect(presentLoginError(api("INVALID_CREDENTIALS", 401))).toEqual({
      summary: "Причина INVALID_CREDENTIALS",
      guidance: "Проверьте электронную почту и пароль.",
      action: null,
      diagnostics: { code: "INVALID_CREDENTIALS", correlationId: "request-id" },
    });
  });

  it("keeps initial AUTH_REQUIRED silent", () => {
    expect(
      presentSessionError(api("AUTH_REQUIRED", 401), "initial"),
    ).toBeNull();
  });

  it("turns runtime AUTH_REQUIRED into sign-in action", () => {
    expect(
      presentSessionError(api("AUTH_REQUIRED", 401), "runtime"),
    ).toMatchObject({
      action: { id: "sign-in", label: "Войти снова" },
    });
  });

  it.each([
    ["WORK_ORDER_NOT_FOUND", "refresh"],
    ["WORK_ORDER_NOT_ASSIGNED", "refresh"],
    ["WORK_ORDER_STATE_CONFLICT", "refresh"],
    ["WORK_ORDER_CONTEXT_INVALID", null],
    ["ROLE_NOT_ALLOWED", null],
  ])("maps workspace open code %s", (code, actionId) => {
    const presentation = presentWorkspaceOpenError(api(code, 409));
    expect(presentation?.action?.id ?? null).toBe(actionId);
  });

  it.each([
    ["EDIT_VERSION_NOT_FOUND", "reopen"],
    ["EDIT_VERSION_STATE_CONFLICT", "refresh"],
    ["WORKSPACE_CONTEXT_INVALID", null],
  ])("maps workspace restore code %s", (code, actionId) => {
    const presentation = presentWorkspaceRestoreError(api(code, 409));
    expect(presentation?.action?.id ?? null).toBe(actionId);
  });

  it("retries list transport failures", () => {
    expect(presentWorkOrdersLoadError(network)?.action).toEqual({
      id: "retry",
      label: "Повторить",
    });
  });

  it("routes a missing workflow actor to sign-in", () => {
    expect(
      presentWorkOrdersLoadError(api("WORK_ORDER_ACTOR_NOT_FOUND", 404))
        ?.action,
    ).toEqual({ id: "sign-in", label: "Войти снова" });
  });

  it("keeps an inactive account non-retryable", () => {
    const presentation = presentWorkOrdersLoadError(api("USER_INACTIVE", 403));
    expect(presentation?.guidance).toBe("Обратитесь к администратору.");
    expect(presentation?.action).toBeNull();
  });

  it("does not present a cancelled request", () => {
    expect(presentWorkOrdersLoadError({ kind: "cancelled" })).toBeNull();
  });

  it("does not invent a retry for an unknown client error", () => {
    const presentation = presentWorkspaceOpenError(
      api("UNKNOWN_CLIENT_ERROR", 422),
    );
    expect(presentation?.summary).toBe("Причина UNKNOWN_CLIENT_ERROR");
    expect(presentation?.action).toBeNull();
  });

  it("preserves only correlation diagnostics for unstructured HTTP", () => {
    const presentation = presentWorkOrdersLoadError({
      kind: "http",
      status: 503,
      correlationId: "http-id",
    });
    expect(presentation?.diagnostics).toEqual({
      code: null,
      correlationId: "http-id",
    });
    expect(presentation?.action?.id).toBe("retry");
  });
});
