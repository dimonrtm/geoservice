import axios from "axios";

import {
  isValidCorrelationId,
  type ParsedApiError,
} from "@/contracts/api-error";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function nonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function headerValue(headers: unknown, name: string): unknown {
  if (!isRecord(headers)) {
    return undefined;
  }

  const get = headers.get;
  if (typeof get === "function") {
    return get.call(headers, name);
  }

  const entry = Object.entries(headers).find(
    ([key]) => key.toLowerCase() === name.toLowerCase(),
  );
  return entry?.[1];
}

function responseCorrelationId(headers: unknown, body: unknown): string | null {
  const fromHeader = headerValue(headers, "X-Correlation-ID");
  if (isValidCorrelationId(fromHeader)) {
    return fromHeader;
  }
  if (isRecord(body) && isValidCorrelationId(body.correlationId)) {
    return body.correlationId;
  }
  return null;
}

export function parseApiError(error: unknown): ParsedApiError {
  if (axios.isCancel(error)) {
    return { kind: "cancelled" };
  }
  if (!axios.isAxiosError(error)) {
    return { kind: "unknown", status: null, correlationId: null };
  }
  if (error.code === "ERR_CANCELED") {
    return { kind: "cancelled" };
  }
  if (error.code === "ECONNABORTED" || error.code === "ETIMEDOUT") {
    return { kind: "timeout", status: null, correlationId: null };
  }
  if (!error.response) {
    return { kind: "network", status: null, correlationId: null };
  }

  const { status, data, headers } = error.response;
  const correlationId = responseCorrelationId(headers, data);
  if (
    isRecord(data) &&
    nonEmptyString(data.code) &&
    nonEmptyString(data.message)
  ) {
    return {
      kind: "api",
      status,
      code: data.code.trim(),
      message: data.message.trim(),
      correlationId,
    };
  }
  return { kind: "http", status, correlationId };
}
