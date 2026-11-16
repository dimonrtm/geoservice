import { expect, it } from "vitest";
import { classifySaveFailure } from "./workspaceSaveErrors";
const failure = (code: string, status = 422) => ({
  isAxiosError: true,
  response: {
    status,
    data: { code, message: "Ошибка", correlationId: "test" },
  },
});
it("distinguishes retryable transport, terminal domain, stale and guarded replay", () => {
  expect(classifySaveFailure({ isAxiosError: true }, true).kind).toBe(
    "retryableUnknown",
  );
  expect(classifySaveFailure(failure("INTERNAL_ERROR", 500), true).kind).toBe(
    "retryableUnknown",
  );
  expect(classifySaveFailure(failure("GEOMETRY_INVALID"), true).kind).toBe(
    "domainRejected",
  );
  expect(
    classifySaveFailure(failure("DRAFT_VERSION_STALE", 409), true).kind,
  ).toBe("stale");
  expect(
    classifySaveFailure(failure("REQUEST_VALIDATION_ERROR"), true).kind,
  ).toBe("blocked");
  expect(
    classifySaveFailure(failure("REQUEST_VALIDATION_ERROR"), false).kind,
  ).toBe("domainRejected");
  expect(
    classifySaveFailure(failure("EDIT_VERSION_NOT_FOUND", 404), true).kind,
  ).toBe("blocked");
});
it("does not invent a new intent for reused IDs, cancellation or unknown codes", () => {
  expect(
    classifySaveFailure(failure("COMMAND_ID_REUSED", 409), true),
  ).toMatchObject({ kind: "blocked", reason: "identity" });
  expect(
    classifySaveFailure({ isAxiosError: true, code: "ERR_CANCELED" }, true)
      .kind,
  ).toBe("blocked");
  expect(classifySaveFailure(failure("NEW_UNKNOWN_CODE", 422), true).kind).toBe(
    "blocked",
  );
  expect(classifySaveFailure(failure("GEOMETRY_INVALID", 400), true).kind).toBe(
    "blocked",
  );
});
