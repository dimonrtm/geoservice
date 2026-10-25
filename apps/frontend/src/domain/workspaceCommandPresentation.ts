import type { useWorkOrdersStore } from "@/stores/workOrders";
import { isLocalDraftDirty } from "./workspaceDraft";
import { vertexMoveBlockReason } from "./workspaceLineInteraction";

export type WorkspaceCommandState = Pick<
  ReturnType<typeof useWorkOrdersStore>,
  | "activeWorkspace"
  | "localDraft"
  | "phase"
  | "recoveryRecord"
  | "commandResult"
  | "saveError"
  | "readbackError"
  | "storageError"
  | "editBlockReason"
  | "didSaveChangeGeometry"
  | "rejectedCandidateGeometry"
  | "canRetryPendingCommand"
  | "canRetryCurrentRead"
  | "canDiscardRejectedAttempt"
  | "workspaceInteractionLocked"
>;
export type WorkspaceCommandPresentation = {
  canRetryCommand: boolean;
  canRetryRead: boolean;
  canDiscardRejectedAttempt: boolean;
  canSave: boolean;
  canCancel: boolean;
  canRevert: boolean;
  busy: boolean;
  statusText: string;
  positionalAccuracyMessage: string;
  severity: "info" | "success" | "error";
};
const rejectionMessages: Record<string, string> = {
  GEOMETRY_INVALID:
    "Правка не сохранена: форма линии недопустима. Измените положение вершины или отмените правку.",
  GEOMETRY_OUTSIDE_AOI:
    "Правка не сохранена: линия выходит за область работ. Переместите вершину внутрь области или отмените правку.",
  GEOMETRY_STRUCTURE_CHANGED:
    "Правка не сохранена: разрешено перемещать только одну внутреннюю вершину линии.",
  FEATURE_NOT_EDITABLE: "Эта линия недоступна для редактирования.",
  WORK_ORDER_CONTEXT_INVALID:
    "Контекст наряда недоступен для сохранения. Редактирование временно недоступно.",
  MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED:
    "В этой рабочей версии можно изменять только одну линию.",
  REQUEST_VALIDATION_ERROR:
    "Правка не сохранена: данные не прошли проверку. Исправьте или отмените правку.",
};

export function presentWorkspaceCommands(
  store: WorkspaceCommandState,
  actorCanEdit: boolean,
): WorkspaceCommandPresentation {
  const view: WorkspaceCommandPresentation = {
    canRetryCommand: false,
    canRetryRead: false,
    canDiscardRejectedAttempt: false,
    canSave: false,
    canCancel: false,
    canRevert: false,
    busy: false,
    statusText: "Нет несохранённых изменений",
    severity: "info",
    positionalAccuracyMessage:
      "Позиционная точность не проверена. Топология не проверена. Сохранение не подтверждает точность положения линии",
  };
  const error = (text: string) => ({
    ...view,
    statusText: text,
    severity: "error" as const,
  });
  const recovery = store.recoveryRecord;
  const succeeded = recovery?.state === "succeeded";
  const stale =
    store.phase === "stale" ||
    store.saveError === "DRAFT_VERSION_STALE" ||
    (recovery?.state === "rejected" &&
      recovery.error.code === "DRAFT_VERSION_STALE");
  if (!actorCanEdit || !store.activeWorkspace)
    return error(
      "Редактирование недоступно: рабочая область или доступ изменились.",
    );
  if (store.storageError)
    return error(
      recovery
        ? "Не удалось сохранить данные восстановления. Редактирование временно недоступно."
        : "Правка не отправлена: не удалось подготовить данные восстановления. Редактирование временно недоступно.",
    );
  if (store.phase === "blocked")
    return error(
      "Не удалось безопасно продолжить работу. Редактирование временно недоступно.",
    );
  if (store.workspaceInteractionLocked)
    return {
      ...view,
      statusText: "Завершите выбор в диалоге возврата к исходной геометрии.",
    };
  view.canRetryCommand = store.canRetryPendingCommand;
  view.canRetryRead = store.canRetryCurrentRead;
  view.canDiscardRejectedAttempt = store.canDiscardRejectedAttempt;
  if (store.readbackError)
    return error(
      succeeded
        ? "Операция выполнена, но актуальные данные карты не удалось загрузить. Редактирование временно недоступно"
        : "Изменение отклонено. Актуальные данные карты не удалось загрузить. Редактирование временно недоступно",
    );
  if (store.phase === "reading-current")
    return {
      ...view,
      busy: true,
      statusText: succeeded
        ? "Операция выполнена. Загружаем актуальные данные…"
        : "Загружаем актуальные данные…",
    };
  if (store.phase === "sending")
    return { ...view, busy: true, statusText: "Отправляем запрос…" };
  if (store.phase === "retry-wait")
    return {
      ...view,
      busy: true,
      statusText: "Ожидаем повторной попытки запроса…",
    };
  if (store.phase === "unknown" || recovery?.state === "unknown")
    return error(
      "Результат операции неизвестен. Повторите прежний запрос. Редактирование временно недоступно",
    );
  if (stale)
    return error(
      "Данные изменились после начала вашей правки. Она не сохранена. Редактирование временно недоступно",
    );
  if (recovery)
    return error(
      "Редактирование временно недоступно: восстановление не завершено.",
    );
  if (
    store.saveError === "FEATURE_NOT_EDITABLE" ||
    store.saveError === "WORK_ORDER_CONTEXT_INVALID"
  )
    return error(rejectionMessages[store.saveError]!);

  const draft = store.localDraft;
  const dirty = draft !== null && isLocalDraftDirty(draft);
  const eligiblePhase = ["idle", "editing", "rejected"].includes(store.phase);
  view.canCancel = eligiblePhase && dirty;
  view.canRevert =
    eligiblePhase &&
    store.activeWorkspace.workOrder.editVersion.hasPersistedChangeSet;
  const unchangedRejection =
    draft &&
    store.rejectedCandidateGeometry &&
    JSON.stringify(draft.candidateGeometry.coordinates) ===
      JSON.stringify(store.rejectedCandidateGeometry.coordinates);
  const geometryValidationMessage = dirty
    ? vertexMoveBlockReason(
        draft.candidateGeometry,
        store.activeWorkspace.workOrder.scope.aoi.geometry,
      )
    : null;
  view.canSave =
    view.canCancel && !unchangedRejection && !geometryValidationMessage;
  if ((store.phase === "rejected" || unchangedRejection) && store.saveError) {
    view.statusText =
      rejectionMessages[store.saveError] ??
      "Правка не сохранена. Проверьте данные или отмените правку.";
    view.severity = "error";
  } else if (geometryValidationMessage) {
    view.statusText = geometryValidationMessage;
    view.severity = "error";
  } else if (dirty) {
    view.statusText = "Есть несохранённые изменения";
  } else if (store.commandResult && !draft) {
    view.statusText =
      store.didSaveChangeGeometry === false
        ? "Сохранение выполнено без новых изменений"
        : store.didSaveChangeGeometry === true
          ? "Правка сохранена в рабочей версии"
          : "Прежняя операция выполнена";
    view.severity = "success";
  }
  return view;
}
