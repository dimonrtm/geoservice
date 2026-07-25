import { defineStore } from "pinia";

import { parseApiError } from "@/api/parseApiError";
import {
  login,
  logoutSession,
  refreshSession,
  type AuthUser,
} from "@/api/auth";
import type { ErrorPresentation } from "@/contracts/api-error";
import { presentSessionError } from "@/errors/apiErrorPresentations";
import {
  useWorkOrdersStore,
  type ResetWorkOrdersOptions,
} from "@/stores/workOrders";

type AuthState = {
  token: string | null;
  user: AuthUser | null;
  isReady: boolean;
  isRestoring: boolean;
  sessionError: ErrorPresentation | null;
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

type SetAuthOptions = {
  preserveWorkOrderStateOnInitialUser?: boolean;
};

type ClearLocalSessionOptions = {
  forceWorkOrdersReset?: boolean;
};

export const useAuthStore = defineStore(
  "auth",

  {
    state: (): AuthState => ({
      token: null,
      user: null,
      isReady: false,
      isRestoring: false,
      sessionError: null,
    }),
    getters: {
      isAuthenticated: (state) => Boolean(state.token && state.user),
    },
    actions: {
      setAuth(token: string, user: AuthUser, options: SetAuthOptions = {}) {
        const previousUserId = authUserId(this.user);

        this.token = token;
        this.user = user;
        this.sessionError = null;
        const preserveWorkOrderState =
          options.preserveWorkOrderStateOnInitialUser === true &&
          previousUserId === null;
        resetWorkOrdersIfUserIdChanged(previousUserId, user.id, {
          preserveOpenedWorkspace: preserveWorkOrderState,
          preserveSelectedWorkOrder: preserveWorkOrderState,
        });
      },
      setUser(user: AuthUser | null) {
        const previousUserId = authUserId(this.user);

        this.user = user;
        resetWorkOrdersIfUserIdChanged(previousUserId, authUserId(user));
      },
      clearLocalSession(options: ClearLocalSessionOptions = {}) {
        const previousUserId = authUserId(this.user);

        this.token = null;
        this.user = null;
        this.sessionError = null;
        this.isReady = true;
        this.isRestoring = false;
        if (options.forceWorkOrdersReset) {
          useWorkOrdersStore().reset();
        } else {
          resetWorkOrdersIfUserIdChanged(previousUserId, null);
        }
      },
      handleUnauthorizedResponse(error: unknown): void {
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
      async loginWithPassword(email: string, password: string) {
        const result = await login(email, password);
        this.setAuth(result.access_token, result.user);
        this.isReady = true;
        this.isRestoring = false;
        return result;
      },
      async restoreSession() {
        const restoreMode = this.isAuthenticated ? "runtime" : "initial";
        this.sessionError = null;
        this.isRestoring = true;

        try {
          const result = await refreshSession();
          this.setAuth(result.access_token, result.user, {
            preserveWorkOrderStateOnInitialUser: true,
          });
        } catch (error: unknown) {
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
          this.isReady = true;
          this.isRestoring = false;
        }
      },
      async logout() {
        this.clearLocalSession();
        this.isReady = false;

        try {
          await logoutSession();
        } catch {
          // Local logout must still complete if the server is unavailable.
        } finally {
          this.isReady = true;
          this.isRestoring = false;
        }
      },
    },
  },
);
