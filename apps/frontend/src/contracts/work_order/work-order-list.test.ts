import { describe, expect, it } from "vitest";
import { parseAssignedWorkOrders } from "./work-order-list";
import { WorkOrderResponseError } from "./work-order-response-error";

const id = "aaaaaaaa-1111-4111-8111-111111111111";
const order = {
  id,
  code: "WO-1",
  title: "Наряд",
  description: null,
  status: "assigned",
};
describe("assigned work order response", () => {
  it("preserves rows and usable values while reporting every damaged field", () => {
    const { workOrders } = parseAssignedWorkOrders({
      workOrders: [
        { ...order, title: 7, status: "unknown" },
        order,
        null,
        { ...order, id: undefined },
      ],
    });
    expect(workOrders).toHaveLength(4);
    expect(workOrders[0]).toMatchObject({
      id,
      code: "WO-1",
      title: null,
      status: null,
      issues: [
        { field: "title", message: "Некорректное название наряда" },
        { field: "status", message: "Некорректный статус наряда" },
      ],
    });
    expect(workOrders[1]?.issues).toEqual([]);
    expect(workOrders[2]).toMatchObject({
      id: null,
      issues: [{ field: "item", message: "Некорректные данные наряда" }],
    });
    expect(workOrders[3]?.issues.map((issue) => issue.field)).toEqual(["id"]);
    expect(new Set(workOrders.map((row) => row.rowKey)).size).toBe(4);
  });
  it.each(["id", "code", "title", "description", "status"] as const)(
    "reports missing and mistyped %s",
    (field) => {
      for (const value of [undefined, 42, {}]) {
        const result = parseAssignedWorkOrders({
          workOrders: [{ ...order, [field]: value }],
        }).workOrders[0]!;
        expect(result.issues.map((issue) => issue.field)).toEqual([field]);
        expect(result[field]).toBeNull();
      }
    },
  );
  it("accepts empty display strings and nullable description without inventing values", () => {
    expect(
      parseAssignedWorkOrders({
        workOrders: [
          {
            ...order,
            id: id.toUpperCase(),
            code: "",
            title: "",
            description: null,
          },
        ],
      }).workOrders[0],
    ).toMatchObject({ id, code: "", title: "", description: null, issues: [] });
  });
  it.each([null, [], {}, { workOrders: null }, { workOrders: {} }])(
    "rejects an unusable envelope %j",
    (value) => {
      expect(() => parseAssignedWorkOrders(value)).toThrow(
        WorkOrderResponseError,
      );
    },
  );
  it("accepts an empty list", () =>
    expect(parseAssignedWorkOrders({ workOrders: [] })).toEqual({
      workOrders: [],
    }));
});
