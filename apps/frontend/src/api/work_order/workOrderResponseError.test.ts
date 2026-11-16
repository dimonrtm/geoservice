import { expect, it } from "vitest";
import { parseApiError } from "../parseApiError";
import { WorkOrderResponseError } from "@/contracts/work_order/work-order-response-error";
import { ProtocolError } from "@/contracts/workspace/workspace-edit";
import {
  presentWorkOrdersLoadError,
  presentWorkspaceOpenError,
} from "@/errors/apiErrorPresentations";
it.each(["list", "open"] as const)(
  "explains %s protocol errors without retry or access denial",
  (operation) => {
    const error = parseApiError(
      new WorkOrderResponseError(operation, [
        { field: "id", message: "Некорректный идентификатор наряда" },
      ]),
    );
    expect(error).toMatchObject({ kind: "protocol", status: null });
    const view = (
      operation === "list"
        ? presentWorkOrdersLoadError
        : presentWorkspaceOpenError
    )(error);
    expect(view).toMatchObject({
      action: null,
      diagnostics: { code: "INVALID_SERVER_RESPONSE" },
      guidance: "Некорректный идентификатор наряда",
    });
  },
);
it("does not reclassify existing Save/recovery ProtocolError", () => {
  expect(parseApiError(new ProtocolError()).kind).toBe("unknown");
});
