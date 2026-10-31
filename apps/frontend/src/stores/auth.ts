import { defineStore } from "pinia";
import { toRaw } from "vue";

import { parseApiError } from "@/api/parseApiError";
import {
  login,
  logoutSession,
  refreshSession,
  fetchSessionStatus,
  type AuthUser,
} from "@/api/auth";
import type { ErrorPresentation } from "@/contracts/api-error";
import {
  presentLogoutError,
  presentSessionError,
} from "@/errors/apiErrorPresentations";
import {
  AuthOperationSupersededError,
  getBrowserSessionCoordinator,
} from "@/auth/browserSessionCoordinator";
import { startSessionMonitor } from "@/auth/browserSessionMonitor";
import type { BrowserSessionMarker } from "@/auth/browserSessionTypes";
import {
  useWorkOrdersStore,
  type ResetWorkOrdersOptions,
} from "@/stores/workOrders";

import { useWorkspaceRecoveryStore } from "./workspaceRecovery";

type AuthState = {
  restoreGeneration: number;
  sessionEpoch: number;
  sessionId: string | null;
  token: string | null;
  user: AuthUser | null;
  isReady: boolean;
  isRestoring: boolean;
  sessionError: ErrorPresentation | null;
  logoutError: ErrorPresentation | null;
  isLoggingOut: boolean;
};

function authUserId(user: AuthUser | null): string | null {
  return user?.id ?? null;
}

function resetWorkOrdersIfUserIdChanged(
  previousUserId: string | null,
  nextUserId: string | null,
  options: ResetWorkOrdersOptions = {},
): void {
  if (previousUserId === nextUserId) {
    return;
  }

  useWorkOrdersStore().reset(options);
}

export type SetAuthOptions = {
  sessionId: string;
  preserveWorkOrderStateOnInitialUser?: boolean;
};

type ClearLocalSessionOptions = {
  forceWorkOrdersReset?: boolean;
};

type Runtime = {
  started: boolean;
  publishing: boolean;
  monitor?: ReturnType<typeof startSessionMonitor>;
  unsubscribe?: () => void;
};
const runtimes = new WeakMap<object, Runtime>();
function runtime(store: object): Runtime {
  // Pinia devtools создаёт новый Proxy для каждого action; ключ должен быть общим.
  store = toRaw(store);
  let value = runtimes.get(store);
  if (!value) {
    value = { started: false, publishing: false };
    runtimes.set(store, value);
  }
  return value;
}

function publish(store: object, sessionId: string, state: "active" | "ended") {
  const coordinator = getBrowserSessionCoordinator();
  const marker = coordinator.readSessionMarker();
  if (marker?.sessionId === sessionId && marker.state === state) return;
  const local = runtime(store);
  local.publishing = true;
  try {
    coordinator.writeSessionMarker({
      version: 1,
      revision: (marker?.revision ?? 0) + 1,
      sessionId,
      state,
    });
  } finally {
    local.publishing = false;
  }
}

export const useAuthStore = defineStore(
  "auth",

  {
    state: (): AuthState => ({
      restoreGeneration: 0,
      sessionEpoch: 0,
      sessionId: null,
      token: null,
      user: null,
      isReady: false,
      isRestoring: false,
      sessionError: null,
      logoutError: null,
      isLoggingOut: false,
    }),
    getters: {
      isAuthenticated: (state) => Boolean(state.token && state.user),
    },
    actions: {
      setAuth(token: string, user: AuthUser, options: SetAuthOptions) {
        const previousUserId = authUserId(this.user);
        const sessionChanged = this.sessionId !== options.sessionId;
        if (
          previousUserId &&
          (sessionChanged ||
            previousUserId !== user.id ||
            this.user?.role !== user.role)
        )
          useWorkOrdersStore().suspendWorkspaceRecoveryForAccessLoss(
            previousUserId,
          );

        if (
          sessionChanged ||
          previousUserId !== user.id ||
          this.user?.role !== user.role
        ) {
          this.sessionEpoch++;
          useWorkspaceRecoveryStore().hideActor();
        }
        this.token = token;
        this.sessionId = options.sessionId;
        this.user = user;
        this.sessionError = null;
        this.logoutError = null;
        const preserveWorkOrderState =
          options.preserveWorkOrderStateOnInitialUser === true &&
          previousUserId === null;
        const resetOptions = {
          preserveOpenedWorkspace: preserveWorkOrderState,
          preserveSelectedWorkOrder: preserveWorkOrderState,
        };
        if (sessionChanged && previousUserId === user.id)
          useWorkOrdersStore().reset(resetOptions);
        else
          resetWorkOrdersIfUserIdChanged(previousUserId, user.id, resetOptions);
        if (sessionChanged && runtime(this).started)
          this.restartSessionMonitor();
      },
      setUser(user: AuthUser | null) {
        const previousUserId = authUserId(this.user);
        if (
          previousUserId &&
          (previousUserId !== authUserId(user) ||
            this.user?.role !== user?.role)
        )
          useWorkOrdersStore().suspendWorkspaceRecoveryForAccessLoss(
            previousUserId,
          );

        if (
          previousUserId !== authUserId(user) ||
          this.user?.role !== user?.role
        ) {
          this.sessionEpoch++;
          useWorkspaceRecoveryStore().hideActor();
        }
        this.user = user;
        resetWorkOrdersIfUserIdChanged(previousUserId, authUserId(user));
      },
      clearLocalSession(options: ClearLocalSessionOptions = {}) {
        this.restoreGeneration++;
        runtime(this).monitor?.();
        runtime(this).monitor = undefined;
        const previousUserId = authUserId(this.user);
        if (previousUserId || options.forceWorkOrdersReset)
          useWorkOrdersStore().suspendWorkspaceRecoveryForAccessLoss(
            previousUserId ?? undefined,
          );

        this.sessionEpoch++;
        useWorkspaceRecoveryStore().hideActor();
        this.token = null;
        this.sessionId = null;
        this.user = null;
        this.sessionError = null;
        this.logoutError = null;
        this.isReady = true;
        this.isRestoring = false;
        if (options.forceWorkOrdersReset) {
          useWorkOrdersStore().reset();
        } else {
          resetWorkOrdersIfUserIdChanged(previousUserId, null);
        }
      },
      handleUnauthorizedResponse(error: unknown, requestEpoch?: number): void {
        if (requestEpoch !== undefined && requestEpoch !== this.sessionEpoch)
          return;
        const hadActiveSession = this.isAuthenticated;
        const parsed = parseApiError(error);
        this.clearLocalSession();
        if (hadActiveSession) {
          this.sessionError = presentSessionError(parsed, "runtime");
        }
      },
      dismissSessionError(): void {
        this.sessionError = null;
      },
      restartSessionMonitor(): void {
        const local = runtime(this);
        local.monitor?.();
        local.monitor = undefined;
        if (!this.sessionId || !this.token) return;
        local.monitor = startSessionMonitor(
          () =>
            this.sessionId && this.token
              ? { sessionId: this.sessionId, accessToken: this.token }
              : null,
          (sid) => {
            if (local.publishing || sid !== this.sessionId) return;
            const coordinator = getBrowserSessionCoordinator();
            let marker: BrowserSessionMarker | null = null;
            try {
              marker = coordinator.readSessionMarker();
            } catch {
              /* status достаточен */
            }
            this.clearLocalSession();
            if (marker?.state === "active" && marker.sessionId !== sid) {
              void this.restoreSession();
            } else if (
              !marker ||
              (marker.sessionId === sid && marker.state !== "ended")
            ) {
              void coordinator
                .runAuthOperation(
                  "logout",
                  marker?.revision ?? null,
                  async () => {
                    publish(this, sid, "ended");
                  },
                )
                .catch(() => {});
            }
          },
        );
      },
      startBrowserSessionSync(): void {
        const local = runtime(this);
        if (local.started) return;
        local.started = true;
        local.unsubscribe = getBrowserSessionCoordinator().subscribe(
          (marker) => {
            if (local.publishing) return;
            if (marker.state === "ended") {
              if (marker.sessionId === this.sessionId) this.clearLocalSession();
            } else if (marker.sessionId !== this.sessionId) {
              this.clearLocalSession();
              void this.restoreSession();
            }
          },
        );
        this.restartSessionMonitor();
      },
      stopBrowserSessionSync(): void {
        const local = runtime(this);
        local.monitor?.();
        local.unsubscribe?.();
        local.monitor = undefined;
        local.unsubscribe = undefined;
        local.started = false;
      },
      async ensureSessionReady(): Promise<boolean> {
        if (!this.isAuthenticated || !this.sessionId) return false;
        this.startBrowserSessionSync();
        const local = runtime(this);
        const sid = this.sessionId;
        const epoch = this.sessionEpoch;
        const monitor = local.monitor;
        if (!monitor) return false;
        let active = await monitor.checkNow();
        // Resume мог обесценить старый in-flight ответ и уже запустить свежий gate.
        if (!active && local.monitor === monitor && monitor.isChecking())
          active = await monitor.checkNow();
        return (
          active &&
          sid === this.sessionId &&
          epoch === this.sessionEpoch &&
          local.monitor === monitor
        );
      },
      async loginWithPassword(email: string, password: string) {
        // Новый вход забирает управление у ожидающего восстановления.
        const generation = ++this.restoreGeneration;
        this.isRestoring = false;
        this.isReady = true;
        const coordinator = getBrowserSessionCoordinator();
        const marker = coordinator.readSessionMarker();
        const result = await coordinator.runAuthOperation(
          "login",
          marker?.revision ?? null,
          async () => {
            if (generation !== this.restoreGeneration)
              throw new AuthOperationSupersededError(
                coordinator.readSessionMarker(),
              );
            const response = await login(email, password);
            if (generation !== this.restoreGeneration)
              throw new AuthOperationSupersededError(
                coordinator.readSessionMarker(),
              );
            if (!response.session_id)
              throw new Error("Сервер не вернул идентификатор сессии");
            publish(this, response.session_id, "active");
            return response;
          },
        );
        await useWorkspaceRecoveryStore().suspendActor(result.user.id);
        if (generation !== this.restoreGeneration) return result;
        const current = coordinator.readSessionMarker();
        if (
          current?.state !== "active" ||
          current.sessionId !== result.session_id
        )
          return result;
        this.setAuth(result.access_token, result.user, {
          sessionId: result.session_id,
        });
        this.isReady = true;
        this.isRestoring = false;
        return result;
      },
      async restoreSession() {
        const generation = ++this.restoreGeneration;
        const restoreMode = this.isAuthenticated ? "runtime" : "initial";
        this.sessionError = null;
        this.isRestoring = true;

        try {
          const coordinator = getBrowserSessionCoordinator();
          let marker = coordinator.readSessionMarker();
          let result;
          // Только superseded намерение повторяется; каждый HTTP остаётся под lock.
          while (generation === this.restoreGeneration) {
            if (marker?.state === "ended") {
              this.clearLocalSession({
                forceWorkOrdersReset: restoreMode === "initial",
              });
              return;
            }
            const expectedSid =
              marker?.sessionId ?? this.sessionId ?? undefined;
            try {
              result = await coordinator.runAuthOperation(
                "refresh",
                marker?.revision ?? null,
                async () => {
                  if (generation !== this.restoreGeneration) return undefined;
                  const response = await refreshSession(expectedSid);
                  if (generation !== this.restoreGeneration) return undefined;
                  if (
                    !response.session_id ||
                    (expectedSid && response.session_id !== expectedSid)
                  )
                    throw new Error("Сессия ответа не совпадает с ожидаемой");
                  publish(this, response.session_id, "active");
                  return response;
                },
              );
              if (generation !== this.restoreGeneration) return;
              const current = coordinator.readSessionMarker();
              if (
                current &&
                (current.state === "ended" ||
                  current.sessionId !== result?.session_id)
              ) {
                marker = current;
                continue;
              }
              break;
            } catch (error) {
              if (!(error instanceof AuthOperationSupersededError)) throw error;
              marker = error.currentMarker;
              if (!marker) throw error;
            }
          }
          if (generation !== this.restoreGeneration) return;
          if (!result) return;
          this.setAuth(result.access_token, result.user, {
            sessionId: result.session_id,
            preserveWorkOrderStateOnInitialUser: true,
          });
        } catch (error: unknown) {
          if (generation !== this.restoreGeneration) return;
          const parsed = parseApiError(error);
          const sessionError = presentSessionError(parsed, restoreMode);
          const initialSessionEnded =
            restoreMode === "initial" &&
            (parsed.kind === "api" || parsed.kind === "http") &&
            parsed.status === 401;
          this.clearLocalSession({
            forceWorkOrdersReset: initialSessionEnded,
          });
          this.sessionError = sessionError;
        } finally {
          if (generation === this.restoreGeneration) {
            this.isReady = true;
            this.isRestoring = false;
          }
        }
      },
      async logout(): Promise<boolean> {
        const sid = this.sessionId;
        if (!sid) return false;
        const generation = ++this.restoreGeneration;
        const token = this.token ?? undefined;
        this.isRestoring = false;
        this.isLoggingOut = true;
        this.logoutError = null;
        const coordinator = getBrowserSessionCoordinator();
        let logoutStarted = false;
        try {
          const marker = coordinator.readSessionMarker();
          return await coordinator.runAuthOperation(
            "logout",
            marker?.revision ?? null,
            async () => {
              if (
                generation !== this.restoreGeneration ||
                sid !== this.sessionId
              )
                return false;
              logoutStarted = true;
              const result = await logoutSession(sid);
              if (!result.ok || result.session_id !== sid)
                throw new Error("Не подтверждён выход из ожидаемой сессии");
              if (
                sid === this.sessionId &&
                generation === this.restoreGeneration
              )
                this.clearLocalSession();
              try {
                publish(this, sid, "ended");
              } catch {
                /* Подтверждённый ended не ждёт durable публикации. */
              }
              return true;
            },
          );
        } catch (error) {
          if (sid !== this.sessionId || generation !== this.restoreGeneration)
            return false;
          const parsed = parseApiError(error);
          const uncertain =
            logoutStarted &&
            (parsed.kind === "network" ||
              parsed.kind === "timeout" ||
              parsed.kind === "unknown" ||
              ((parsed.kind === "http" || parsed.kind === "api") &&
                parsed.status === 401));
          if (uncertain) {
            try {
              const status = await fetchSessionStatus(sid, token);
              if (status.session_id === sid && status.state === "ended") {
                if (
                  sid === this.sessionId &&
                  generation === this.restoreGeneration
                )
                  this.clearLocalSession();
                try {
                  const marker = coordinator.readSessionMarker();
                  if (!marker || marker.sessionId === sid) {
                    // UI уже очищен; публикация не задерживает подтверждение выхода.
                    void coordinator
                      .runAuthOperation(
                        "logout",
                        marker?.revision ?? null,
                        async () => publish(this, sid, "ended"),
                      )
                      .catch(() => {});
                  }
                } catch {
                  /* Status подтвердил ended независимо от storage. */
                }
                return true;
              }
            } catch {
              /* Неизвестный исход сохраняет вход и доступен для повторной проверки. */
            }
          }
          if (sid === this.sessionId && generation === this.restoreGeneration)
            this.logoutError = presentLogoutError(uncertain);
          return false;
        } finally {
          this.isLoggingOut = false;
        }
      },
    },
  },
);
