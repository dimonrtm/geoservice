export type WorkOrderDataIssue = { field: string; message: string };

export class WorkOrderResponseError extends Error {
  readonly operation: "list" | "open";
  readonly issues: readonly WorkOrderDataIssue[];
  constructor(
    operation: "list" | "open",
    issues: readonly WorkOrderDataIssue[],
  ) {
    super("Некорректный ответ сервера для операции с нарядом");
    this.operation = operation;
    this.issues = issues;
  }
}
