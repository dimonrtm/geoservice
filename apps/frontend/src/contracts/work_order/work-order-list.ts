import type { WorkOrderStatus } from "./work-orders";
import { isUuid, record } from "../workspace/workspace-edit";
import {
  WorkOrderResponseError,
  type WorkOrderDataIssue,
} from "./work-order-response-error";

export type WorkOrderListEntry = {
  rowKey: string;
  id: string | null;
  code: string | null;
  title: string | null;
  description: string | null;
  status: WorkOrderStatus | null;
  issues: WorkOrderDataIssue[];
};
export type IdentifiedWorkOrderListEntry = WorkOrderListEntry & { id: string };
export function hasWorkOrderId(
  entry: WorkOrderListEntry,
): entry is IdentifiedWorkOrderListEntry {
  return entry.id !== null;
}

function parseEntry(value: unknown, index: number): WorkOrderListEntry {
  const entry: WorkOrderListEntry = {
    rowKey: `row-${index}`,
    id: null,
    code: null,
    title: null,
    description: null,
    status: null,
    issues: [],
  };
  if (!record(value)) {
    entry.issues.push({ field: "item", message: "Некорректные данные наряда" });
    return entry;
  }
  if (isUuid(value.id)) entry.id = value.id.toLowerCase();
  else
    entry.issues.push({
      field: "id",
      message: "Некорректный идентификатор наряда",
    });
  if (typeof value.code === "string") entry.code = value.code;
  else entry.issues.push({ field: "code", message: "Некорректный код наряда" });
  if (typeof value.title === "string") entry.title = value.title;
  else
    entry.issues.push({
      field: "title",
      message: "Некорректное название наряда",
    });
  if (typeof value.description === "string" || value.description === null)
    entry.description = value.description;
  else
    entry.issues.push({
      field: "description",
      message: "Некорректное описание наряда",
    });
  if (value.status === "assigned" || value.status === "in_progress")
    entry.status = value.status;
  else
    entry.issues.push({
      field: "status",
      message: "Некорректный статус наряда",
    });
  return entry;
}

export function parseAssignedWorkOrders(value: unknown): {
  workOrders: WorkOrderListEntry[];
} {
  if (!record(value) || !Array.isArray(value.workOrders)) {
    throw new WorkOrderResponseError("list", [
      { field: "workOrders", message: "Некорректное поле списка нарядов" },
    ]);
  }
  return { workOrders: value.workOrders.map(parseEntry) };
}
