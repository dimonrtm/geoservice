export type ErrorActionId = "retry" | "refresh" | "reopen" | "sign-in";

export type ParsedApiError =
  | {
      kind: "api";
      status: number;
      code: string;
      message: string;
      correlationId: string | null;
    }
  | {
      kind: "http";
      status: number;
      correlationId: string | null;
    }
  | {
      kind: "network" | "timeout" | "unknown";
      status: null;
      correlationId: null;
    }
  | { kind: "cancelled" };

export type ErrorPresentation = {
  summary: string;
  guidance: string | null;
  action: { id: ErrorActionId; label: string } | null;
  diagnostics: {
    code: string | null;
    correlationId: string | null;
  };
};

const CORRELATION_ID_PATTERN = /^[A-Za-z0-9._:-]{1,128}$/;

export function isValidCorrelationId(value: unknown): value is string {
  return typeof value === "string" && CORRELATION_ID_PATTERN.test(value);
}
