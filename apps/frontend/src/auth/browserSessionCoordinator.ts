import {
  sessionClock,
  type BrowserSessionMarker,
  type SessionClock,
} from "./browserSessionTypes";

export const SESSION_MARKER_KEY = "geoservice.auth.session.v1";
export const AUTH_LOCK_NAME = "geoservice.auth.cookie.v1";

export type CoordinatorPorts = {
  locks?: {
    request<T>(
      name: string,
      options: { signal: AbortSignal },
      action: () => Promise<T>,
    ): Promise<T>;
  };
  storage?: Pick<Storage, "getItem" | "setItem" | "removeItem">;
  events: Pick<EventTarget, "addEventListener" | "removeEventListener">;
  createChannel?: (
    name: string,
  ) => Pick<
    BroadcastChannel,
    "postMessage" | "addEventListener" | "removeEventListener" | "close"
  >;
  clock?: SessionClock;
};

export class AuthOperationSupersededError extends Error {
  readonly currentMarker: BrowserSessionMarker | null;

  constructor(currentMarker: BrowserSessionMarker | null) {
    super("Намерение авторизации заменено другой вкладкой");
    this.name = "AuthOperationSupersededError";
    this.currentMarker = currentMarker;
  }
}

export class AuthCoordinationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthCoordinationError";
  }
}

function parseMarker(value: unknown): BrowserSessionMarker | null {
  if (!value || typeof value !== "object") return null;
  const marker = value as Partial<BrowserSessionMarker>;
  if (
    marker.version !== 1 ||
    !Number.isSafeInteger(marker.revision) ||
    (marker.revision ?? -1) < 0 ||
    typeof marker.sessionId !== "string" ||
    !marker.sessionId.trim() ||
    !["active", "ended"].includes(marker.state ?? "")
  )
    return null;
  return {
    version: 1,
    revision: marker.revision!,
    sessionId: marker.sessionId,
    state: marker.state!,
  };
}

export function createBrowserSessionCoordinator(ports: CoordinatorPorts) {
  const clock = ports.clock ?? sessionClock;
  let ownsLock = false;
  let disposed = false;
  const listeners = new Set<(marker: BrowserSessionMarker) => void>();
  let channel:
    | ReturnType<NonNullable<CoordinatorPorts["createChannel"]>>
    | undefined;
  try {
    channel = ports.createChannel?.(SESSION_MARKER_KEY);
  } catch {
    /* status/storage остаются доступными */
  }

  function requireStorage() {
    if (!ports.storage || disposed)
      throw new AuthCoordinationError("Общее хранилище авторизации недоступно");
    return ports.storage;
  }

  function readSessionMarker(): BrowserSessionMarker | null {
    let raw: string | null;
    try {
      raw = requireStorage().getItem(SESSION_MARKER_KEY);
    } catch {
      throw new AuthCoordinationError(
        "Не удалось прочитать состояние авторизации",
      );
    }
    if (!raw) return null;
    try {
      return parseMarker(JSON.parse(raw));
    } catch {
      return null;
    }
  }

  function notify(marker: BrowserSessionMarker) {
    if (!disposed) for (const listener of listeners) listener(marker);
  }

  // Событие — только сигнал: читаем актуальное durable-состояние, а не задержанный payload.
  function reconcile() {
    try {
      const marker = readSessionMarker();
      if (marker) notify(marker);
    } catch {
      /* проверит status monitor */
    }
  }
  const onStorage: EventListener = (event) => {
    const key = (event as StorageEvent).key;
    if (key === SESSION_MARKER_KEY || key === null) reconcile();
  };
  ports.events.addEventListener("storage", onStorage);
  channel?.addEventListener("message", reconcile);

  async function runAuthOperation<T>(
    _operation: "login" | "refresh" | "logout",
    expectedRevision: number | null,
    action: () => Promise<T>,
  ): Promise<T> {
    if (!ports.locks || disposed)
      throw new AuthCoordinationError("Web Locks недоступен для авторизации");
    const controller = new AbortController();
    const timer = clock.setTimeout(
      () =>
        controller.abort(
          new AuthCoordinationError("Истекло время ожидания авторизации"),
        ),
      30000,
    );
    try {
      return await ports.locks.request(
        AUTH_LOCK_NAME,
        { signal: controller.signal },
        async () => {
          clock.clearTimeout(timer);
          controller.signal.throwIfAborted();
          const storage = requireStorage();
          const marker = readSessionMarker();
          if ((marker?.revision ?? null) !== expectedRevision)
            throw new AuthOperationSupersededError(marker);
          // Проверяем право записи до HTTP: read-only storage не даёт общей координации.
          try {
            storage.setItem(`${SESSION_MARKER_KEY}.probe`, "1");
            storage.removeItem(`${SESSION_MARKER_KEY}.probe`);
          } catch {
            throw new AuthCoordinationError(
              "Не удалось записать состояние авторизации",
            );
          }
          ownsLock = true;
          try {
            return await action();
          } finally {
            ownsLock = false;
          }
        },
      );
    } catch (error) {
      if (controller.signal.aborted) throw controller.signal.reason;
      throw error;
    } finally {
      clock.clearTimeout(timer);
    }
  }

  function writeSessionMarker(input: BrowserSessionMarker): void {
    if (!ownsLock || disposed)
      throw new AuthCoordinationError(
        "Запись состояния авторизации требует auth lock",
      );
    const marker = parseMarker(input);
    const previous = readSessionMarker();
    if (
      !marker ||
      (previous && marker.revision <= previous.revision) ||
      (previous?.sessionId === marker.sessionId &&
        previous.state === "ended" &&
        marker.state === "active")
    )
      throw new AuthCoordinationError(
        "Некорректное изменение состояния авторизации",
      );
    try {
      requireStorage().setItem(SESSION_MARKER_KEY, JSON.stringify(marker));
    } catch {
      throw new AuthCoordinationError(
        "Не удалось записать состояние авторизации",
      );
    }
    notify(marker);
    try {
      channel?.postMessage(marker);
    } catch {
      /* durable marker уже опубликован */
    }
  }

  return {
    runAuthOperation,
    readSessionMarker,
    writeSessionMarker,
    subscribe(listener: (marker: BrowserSessionMarker) => void): () => void {
      if (!disposed) listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    dispose(): void {
      disposed = true;
      listeners.clear();
      ports.events.removeEventListener("storage", onStorage);
      channel?.removeEventListener("message", reconcile);
      channel?.close();
    },
  };
}

let browserCoordinator:
  | ReturnType<typeof createBrowserSessionCoordinator>
  | undefined;

export function getBrowserSessionCoordinator() {
  if (!browserCoordinator) {
    let storage: Storage | undefined;
    try {
      storage = window.localStorage;
    } catch {
      /* ошибка будет явной перед HTTP */
    }
    browserCoordinator = createBrowserSessionCoordinator({
      locks: navigator.locks,
      storage,
      events: window,
      createChannel:
        typeof BroadcastChannel === "undefined"
          ? undefined
          : (name) => new BroadcastChannel(name),
    });
  }
  return browserCoordinator;
}

// При superseded startup restore можно повторить только с currentMarker.active
// и X-Expected-Session-Id этого marker; новый revision не означает локальный JWT.
export const runAuthOperation: ReturnType<
  typeof createBrowserSessionCoordinator
>["runAuthOperation"] = (...args) =>
  getBrowserSessionCoordinator().runAuthOperation(...args);
export const readSessionMarker = () =>
  getBrowserSessionCoordinator().readSessionMarker();
export const writeSessionMarker = (marker: BrowserSessionMarker) =>
  getBrowserSessionCoordinator().writeSessionMarker(marker);
