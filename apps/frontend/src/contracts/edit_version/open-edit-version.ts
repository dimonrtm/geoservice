import { isUuid, record } from "../workspace/workspace-edit";
import {
  WorkOrderResponseError,
  type WorkOrderDataIssue,
} from "../work_order/work-order-response-error";

export type OpenedEditVersion = {
  editVersion: { id: string; workOrderId: string; status: "open" };
};

export function parseOpenedEditVersion(
  value: unknown,
  workOrderId: string,
): OpenedEditVersion {
  if (!record(value) || !record(value.editVersion)) {
    throw new WorkOrderResponseError("open", [
      { field: "editVersion", message: "Некорректные данные рабочей версии" },
    ]);
  }
  const version = value.editVersion;
  const issues: WorkOrderDataIssue[] = [];
  const id = isUuid(version.id) ? version.id.toLowerCase() : null;
  const orderId = isUuid(version.workOrderId)
    ? version.workOrderId.toLowerCase()
    : null;
  if (!id)
    issues.push({
      field: "editVersion.id",
      message: "Некорректный идентификатор рабочей версии",
    });
  if (!orderId || orderId !== workOrderId.toLowerCase())
    issues.push({
      field: "editVersion.workOrderId",
      message: "Некорректный идентификатор наряда рабочей версии",
    });
  if (version.status !== "open")
    issues.push({
      field: "editVersion.status",
      message: "Некорректный статус рабочей версии",
    });
  if (issues.length || !id || !orderId)
    throw new WorkOrderResponseError("open", issues);
  return { editVersion: { id, workOrderId: orderId, status: "open" } };
}
