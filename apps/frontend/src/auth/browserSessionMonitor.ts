import { fetchSessionStatus } from "@/api/auth";
import {
  sessionClock,
  type BrowserSessionCredentials,
  type BrowserSessionStatus,
  type SessionClock,
  type SessionStatusOptions,
} from "./browserSessionTypes";
import {
  getBrowserSessionCoordinator,
  type createBrowserSessionCoordinator,
} from "./browserSessionCoordinator";

export type MonitorPorts = {
  coordinator: ReturnType<typeof createBrowserSessionCoordinator>;
  fetchStatus: (
    sessionId: string,
    accessToken?: string,
    options?: SessionStatusOptions,
  ) => Promise<BrowserSessionStatus>;
  events: Pick<EventTarget, "addEventListener" | "removeEventListener">;
  visibility: Pick<
    Document,
    "addEventListener" | "removeEventListener" | "visibilityState"
  >;
  clock?: SessionClock;
};

export function createSessionMonitor(ports: MonitorPorts) {
  const clock = ports.clock ?? sessionClock;
  return function startSessionMonitor(
    getCurrentSessionCredentials: () => BrowserSessionCredentials | null,
    onEnded: (sessionId: string) => void,
  ) {
    let disposed = false;
    let ended = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let inFlight: Promise<boolean> | null = null;
    let checkAfterFlight = false;
    let resumeGeneration = 0;
    let needsFreshStatus = false;

    function cancelTimer() {
      if (timer !== undefined) clock.clearTimeout(timer);
      timer = undefined;
    }

    function finishSession(sessionId: string, publish: boolean) {
      if (
        disposed ||
        ended ||
        getCurrentSessionCredentials()?.sessionId !== sessionId
      )
        return;
      let marker: ReturnType<typeof ports.coordinator.readSessionMarker> = null;
      try {
        marker = ports.coordinator.readSessionMarker();
      } catch {
        /* локальный выход не ждёт storage */
      }
      ended = true;
      cancelTimer();
      onEnded(sessionId);
      // Локальный UI очищен до ожидания auth lock. Новую ревизию/другой sid
      // не перезаписываем; ошибка публикации не отменяет подтверждённый ended.
      if (
        publish &&
        !disposed &&
        (!marker || marker.sessionId === sessionId) &&
        marker?.state !== "ended"
      ) {
        void ports.coordinator
          .runAuthOperation("logout", marker?.revision ?? null, async () => {
            if (disposed) return;
            ports.coordinator.writeSessionMarker({
              version: 1,
              revision: (marker?.revision ?? 0) + 1,
              sessionId,
              state: "ended",
            });
          })
          .catch(() => {});
      }
    }

    function schedule() {
      cancelTimer();
      if (!disposed && !ended && getCurrentSessionCredentials()) {
        timer = clock.setTimeout(() => {
          void checkNow();
        }, 1000);
      }
    }

    function checkNow(): Promise<boolean> {
      cancelTimer();
      if (disposed || ended) return Promise.resolve(false);
      if (inFlight) return inFlight;
      const currentSessionCredentials = getCurrentSessionCredentials();
      if (!currentSessionCredentials) return Promise.resolve(false);
      const generation = resumeGeneration;
      const options = needsFreshStatus
        ? { requireFreshRequest: true }
        : undefined;
      // Promise boundary гарантирует single-flight даже для синхронных ports.
      inFlight = Promise.resolve()
        .then(async () => {
          if (disposed || ended) return false;
          try {
            const marker = ports.coordinator.readSessionMarker();
            if (
              marker &&
              ((marker.sessionId === currentSessionCredentials.sessionId &&
                marker.state === "ended") ||
                marker.sessionId !== currentSessionCredentials.sessionId)
            ) {
              finishSession(currentSessionCredentials.sessionId, false);
              return false;
            }
          } catch {
            /* status остаётся источником подтверждения */
          }
          try {
            const status = await ports.fetchStatus(
              currentSessionCredentials.sessionId,
              currentSessionCredentials.accessToken,
              options,
            );
            if (
              disposed ||
              ended ||
              getCurrentSessionCredentials()?.sessionId !==
                currentSessionCredentials.sessionId ||
              status.session_id !== currentSessionCredentials.sessionId
            )
              return false;
            if (status.state === "ended") {
              finishSession(currentSessionCredentials.sessionId, true);
              return false;
            }
            const active =
              status.state === "active" && generation === resumeGeneration;
            if (active) needsFreshStatus = false;
            return active;
          } catch {
            return false;
          }
        })
        .finally(() => {
          inFlight = null;
          if (checkAfterFlight && !disposed && !ended) {
            checkAfterFlight = false;
            void checkNow();
          } else schedule();
        });
      return inFlight;
    }

    const onResume = () => {
      if (disposed || ended || ports.visibility.visibilityState === "hidden")
        return;
      resumeGeneration++;
      needsFreshStatus = true;
      if (inFlight) checkAfterFlight = true;
      else void checkNow();
    };
    const unsubscribe = ports.coordinator.subscribe((marker) => {
      const currentSessionCredentials = getCurrentSessionCredentials();
      if (
        currentSessionCredentials &&
        ((marker.sessionId === currentSessionCredentials.sessionId &&
          marker.state === "ended") ||
          marker.sessionId !== currentSessionCredentials.sessionId)
      )
        finishSession(currentSessionCredentials.sessionId, false);
    });
    ports.events.addEventListener("pageshow", onResume);
    ports.visibility.addEventListener("visibilitychange", onResume);
    void checkNow();

    return Object.assign(
      () => {
        disposed = true;
        cancelTimer();
        unsubscribe();
        ports.events.removeEventListener("pageshow", onResume);
        ports.visibility.removeEventListener("visibilitychange", onResume);
      },
      {
        /** false означает: действия пока нельзя допускать, включая сетевую ошибку. */
        checkNow,
        isChecking: () => inFlight !== null,
      },
    );
  };
}

export function startSessionMonitor(
  getCurrentSessionCredentials: () => BrowserSessionCredentials | null,
  onEnded: (sessionId: string) => void,
) {
  return createSessionMonitor({
    coordinator: getBrowserSessionCoordinator(),
    fetchStatus: fetchSessionStatus,
    events: window,
    visibility: document,
  })(getCurrentSessionCredentials, onEnded);
}
