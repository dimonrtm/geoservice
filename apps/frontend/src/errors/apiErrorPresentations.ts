import type {
  ErrorActionId,
  ErrorPresentation,
  ParsedApiError,
} from "@/contracts/api-error";

type SessionMode = "initial" | "runtime";

const ACTION_LABELS: Record<ErrorActionId, string> = {
  retry: "Повторить",
  refresh: "Обновить список",
  reopen: "Открыть заново",
  "sign-in": "Войти снова",
};

function action(id: ErrorActionId): ErrorPresentation["action"] {
  return { id, label: ACTION_LABELS[id] };
}

function diagnostics(error: ParsedApiError): ErrorPresentation["diagnostics"] {
  if (error.kind === "api") {
    return { code: error.code, correlationId: error.correlationId };
  }
  if (error.kind === "http") {
    return { code: null, correlationId: error.correlationId };
  }
  return { code: null, correlationId: null };
}

function summary(error: ParsedApiError, fallback: string): string {
  return error.kind === "api" ? error.message : fallback;
}

function status(error: ParsedApiError): number | null {
  return error.kind === "api" || error.kind === "http" ? error.status : null;
}

function retryable(error: ParsedApiError): boolean {
  const httpStatus = status(error);
  return (
    error.kind === "network" ||
    error.kind === "timeout" ||
    (httpStatus !== null && httpStatus >= 500)
  );
}

function presentation(
  error: ParsedApiError,
  fallback: string,
  guidance: string | null,
  actionId: ErrorActionId | null,
): ErrorPresentation | null {
  if (error.kind === "cancelled") {
    return null;
  }
  return {
    summary: summary(error, fallback),
    guidance,
    action: actionId ? action(actionId) : null,
    diagnostics: diagnostics(error),
  };
}

export function presentLoginError(
  error: ParsedApiError,
): ErrorPresentation | null {
  if (error.kind === "api" && error.code === "INVALID_CREDENTIALS") {
    return presentation(
      error,
      error.message,
      "Проверьте электронную почту и пароль.",
      null,
    );
  }
  if (error.kind === "api" && error.code === "USER_INACTIVE") {
    return presentation(
      error,
      error.message,
      "Обратитесь к администратору.",
      null,
    );
  }
  return presentation(
    error,
    "Сейчас не удалось выполнить вход.",
    "Проверьте соединение и попробуйте ещё раз.",
    null,
  );
}

export function presentSessionError(
  error: ParsedApiError,
  mode: SessionMode,
): ErrorPresentation | null {
  if (mode === "initial" && status(error) === 401) {
    return null;
  }
  if (mode === "runtime" && status(error) === 401) {
    return presentation(
      error,
      "Сессия завершена.",
      "Войдите снова.",
      "sign-in",
    );
  }
  if (error.kind === "api" && error.code === "USER_INACTIVE") {
    return presentation(
      error,
      error.message,
      "Обратитесь к администратору.",
      null,
    );
  }
  return presentation(
    error,
    "Не удалось восстановить сессию.",
    retryable(error) ? "Проверьте соединение и повторите запрос." : null,
    retryable(error) ? "retry" : null,
  );
}

function requiresSignIn(error: ParsedApiError): boolean {
  return (
    status(error) === 401 ||
    (error.kind === "api" && error.code === "WORK_ORDER_ACTOR_NOT_FOUND")
  );
}

function workflowFallback(
  error: ParsedApiError,
  fallback: string,
  retryAction: ErrorActionId,
): ErrorPresentation | null {
  if (requiresSignIn(error)) {
    return presentation(
      error,
      "Сессия завершена.",
      "Войдите снова.",
      "sign-in",
    );
  }
  if (error.kind === "api" && error.code === "ROLE_NOT_ALLOWED") {
    return presentation(
      error,
      error.message,
      "Обратитесь к администратору, если доступ должен быть предоставлен.",
      null,
    );
  }
  if (error.kind === "api" && error.code === "USER_INACTIVE") {
    return presentation(
      error,
      error.message,
      "Обратитесь к администратору.",
      null,
    );
  }
  return presentation(
    error,
    fallback,
    retryable(error) ? "Проверьте соединение и повторите запрос." : null,
    retryable(error) ? retryAction : null,
  );
}

export function presentWorkOrdersLoadError(
  error: ParsedApiError,
): ErrorPresentation | null {
  return workflowFallback(
    error,
    "Не удалось загрузить назначенные наряды.",
    "retry",
  );
}

export function presentWorkspaceOpenError(
  error: ParsedApiError,
): ErrorPresentation | null {
  if (error.kind === "api") {
    if (
      ["WORK_ORDER_NOT_FOUND", "WORK_ORDER_NOT_ASSIGNED"].includes(error.code)
    ) {
      return presentation(
        error,
        error.message,
        "Список назначений мог измениться.",
        "refresh",
      );
    }
    if (error.code === "WORK_ORDER_STATE_CONFLICT") {
      return presentation(
        error,
        error.message,
        "Состояние наряда изменилось.",
        "refresh",
      );
    }
    if (error.code === "WORK_ORDER_CONTEXT_INVALID") {
      return presentation(
        error,
        error.message,
        "Повтор не устранит проблему. Передайте код обращения поддержке.",
        null,
      );
    }
  }
  return workflowFallback(error, "Не удалось открыть рабочую версию.", "retry");
}

export function presentWorkspaceRestoreError(
  error: ParsedApiError,
): ErrorPresentation | null {
  if (error.kind === "api") {
    if (error.code === "EDIT_VERSION_NOT_FOUND") {
      return presentation(
        error,
        error.message,
        "Сохранённая рабочая версия больше недоступна.",
        "reopen",
      );
    }
    if (error.code === "EDIT_VERSION_STATE_CONFLICT") {
      return presentation(
        error,
        error.message,
        "Состояние рабочей версии изменилось.",
        "refresh",
      );
    }
    if (error.code === "WORKSPACE_CONTEXT_INVALID") {
      return presentation(
        error,
        error.message,
        "Workspace невозможно сформировать. Передайте код обращения поддержке.",
        null,
      );
    }
  }
  return workflowFallback(
    error,
    "Не удалось восстановить рабочую версию.",
    "retry",
  );
}
