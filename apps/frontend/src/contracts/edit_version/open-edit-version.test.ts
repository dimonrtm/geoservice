import { describe, expect, it } from "vitest";
import { parseOpenedEditVersion } from "./open-edit-version";
import { WorkOrderResponseError } from "../work_order/work-order-response-error";
const workOrderId = "aaaaaaaa-1111-4111-8111-111111111111";
const id = "bbbbbbbb-1111-4111-8111-111111111111";
const editVersion = { id, workOrderId, status: "open" };
describe("open response", () => {
  it("returns only verified identity and state without requiring metadata", () => {
    expect(
      parseOpenedEditVersion(
        {
          editVersion: {
            ...editVersion,
            id: id.toUpperCase(),
            workOrderId: workOrderId.toUpperCase(),
            ownerId: 42,
          },
          created: "bad",
        },
        workOrderId,
      ),
    ).toEqual({ editVersion });
  });
  it.each([
    null,
    {},
    { editVersion: null },
    { editVersion: { ...editVersion, id: "" } },
    { editVersion: { ...editVersion, workOrderId: id } },
    { editVersion: { ...editVersion, status: "closed" } },
  ])("rejects an invalid Open %j", (value) => {
    expect(() => parseOpenedEditVersion(value, workOrderId)).toThrow(
      WorkOrderResponseError,
    );
  });
});
