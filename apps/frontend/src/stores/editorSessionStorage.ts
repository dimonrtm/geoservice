type StoredOpenedWorkspace = {
  workOrderId: string;
  editVersionId: string;
};

type StoredSelectedWorkOrder = {
  workOrderId: string;
};

export type ResetWorkOrdersOptions = {
  preserveOpenedWorkspace?: boolean;
  preserveSelectedWorkOrder?: boolean;
};

const SELECTED_WORK_ORDER_STORAGE_KEY = "geoservice:selected-work-order";
const OPENED_WORKSPACE_STORAGE_KEY = "geoservice:opened-workspace";

function sessionStorageOrNull(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export function readStoredOpenedWorkspace(): StoredOpenedWorkspace | null {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return null;
  }

  try {
    const rawValue = storage.getItem(OPENED_WORKSPACE_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    const parsed = JSON.parse(rawValue) as Partial<StoredOpenedWorkspace>;
    if (
      typeof parsed.workOrderId !== "string" ||
      typeof parsed.editVersionId !== "string"
    ) {
      clearStoredOpenedWorkspace();
      return null;
    }

    return {
      workOrderId: parsed.workOrderId,
      editVersionId: parsed.editVersionId,
    };
  } catch {
    clearStoredOpenedWorkspace();
    return null;
  }
}

export function storeOpenedWorkspace(
  openedWorkspace: StoredOpenedWorkspace,
): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      OPENED_WORKSPACE_STORAGE_KEY,
      JSON.stringify(openedWorkspace),
    );
  } catch {
    // The in-memory workspace remains valid even if browser storage is unavailable.
  }
}

export function clearStoredOpenedWorkspace(): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.removeItem(OPENED_WORKSPACE_STORAGE_KEY);
  } catch {
    // Nothing to clean up if browser storage is unavailable.
  }
}

export function clearStoredSelectedWorkOrder(): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.removeItem(SELECTED_WORK_ORDER_STORAGE_KEY);
  } catch {
    // Nothing to clean up if browser storage is unavailable.
  }
}

export function readStoredSelectedWorkOrder(): StoredSelectedWorkOrder | null {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return null;
  }

  try {
    const rawValue = storage.getItem(SELECTED_WORK_ORDER_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    const parsed = JSON.parse(rawValue) as Partial<StoredSelectedWorkOrder>;
    if (
      typeof parsed.workOrderId !== "string" ||
      parsed.workOrderId.trim().length === 0
    ) {
      clearStoredSelectedWorkOrder();
      return null;
    }

    return { workOrderId: parsed.workOrderId };
  } catch {
    clearStoredSelectedWorkOrder();
    return null;
  }
}

export function storeSelectedWorkOrder(workOrderId: string): void {
  const storage = sessionStorageOrNull();
  if (!storage) {
    return;
  }

  try {
    storage.setItem(
      SELECTED_WORK_ORDER_STORAGE_KEY,
      JSON.stringify({ workOrderId }),
    );
  } catch {
    // The in-memory selection remains valid if browser storage is unavailable.
  }
}
