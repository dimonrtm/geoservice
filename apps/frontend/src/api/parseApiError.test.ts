import { describe, expect, it } from "vitest";

import { parseApiError } from "@/api/parseApiError";

function axiosFailure(args: {
  status?: number;
  data?: unknown;
  headers?: Record<string, unknown>;
  code?: string;
  cancelled?: boolean;
}) {
  return {
    isAxiosError: true,
    code: args.code,
    __CANCEL__: args.cancelled,
    response:
      args.status === undefined
        ? undefined
        : {
            status: args.status,
            data: args.data,
            headers: args.headers ?? {},
          },
  };
}

describe("parseApiError", () => {
  it("parses a structured error and prefers the response header", () => {
    const parsed = parseApiError(
      axiosFailure({
        status: 404,
        headers: { "x-correlation-id": "header-id" },
        data: {
          code: "FEEDER_NOT_FOUND",
          message: "Фидер не найден.",
          correlationId: "body-id",
        },
      }),
    );

    expect(parsed).toEqual({
      kind: "api",
      status: 404,
      code: "FEEDER_NOT_FOUND",
      message: "Фидер не найден.",
      correlationId: "header-id",
    });
  });

  it("uses the structured body correlation id as fallback", () => {
    expect(
      parseApiError(
        axiosFailure({
          status: 401,
          data: {
            code: "AUTH_REQUIRED",
            message: "Сессия недействительна.",
            correlationId: "body-id",
          },
        }),
      ),
    ).toMatchObject({ kind: "api", correlationId: "body-id" });
  });

  it("keeps only status and header for an unstructured HTTP body", () => {
    expect(
      parseApiError(
        axiosFailure({
          status: 422,
          headers: { "X-Correlation-ID": "validation-id" },
          data: { detail: "raw detail must stay hidden" },
        }),
      ),
    ).toEqual({ kind: "http", status: 422, correlationId: "validation-id" });
  });

  it("ignores invalid diagnostic identifiers", () => {
    expect(
      parseApiError(
        axiosFailure({
          status: 500,
          headers: { "x-correlation-id": "contains space" },
          data: {
            code: "INTERNAL_ERROR",
            message: "Внутренняя ошибка сервиса",
            correlationId: "also invalid",
          },
        }),
      ),
    ).toMatchObject({ kind: "api", correlationId: null });
  });

  it.each([
    [axiosFailure({ code: "ECONNABORTED" }), "timeout"],
    [axiosFailure({ code: "ETIMEDOUT" }), "timeout"],
    [axiosFailure({}), "network"],
    [axiosFailure({ code: "ERR_CANCELED", cancelled: true }), "cancelled"],
    [new Error("not axios"), "unknown"],
  ])("classifies transport failure %#", (error, kind) => {
    expect(parseApiError(error).kind).toBe(kind);
  });
});
