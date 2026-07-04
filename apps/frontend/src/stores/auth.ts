import { defineStore } from "pinia";
import axios from "axios";

import {
  login,
  logoutSession,
  refreshSession,
  type AuthUser,
} from "@/api/auth";
import {
  useWorkOrdersStore,
  type ResetWorkOrdersOptions,
} from "@/stores/workOrders";

type AuthState = {
  token: string | null;
  user: AuthUser | null;
  isReady: boolean;
  isRestoring: boolean;
  sessionError: string | null;
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
  preserveOpenedWorkspaceOnInitialUser?: boolean;
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
        resetWorkOrdersIfUserIdChanged(previousUserId, user.id, {
          preserveOpenedWorkspace:
            options.preserveOpenedWorkspaceOnInitialUser === true &&
            previousUserId === null,
        });
      },
      setUser(user: AuthUser | null) {
        const previousUserId = authUserId(this.user);

        this.user = user;
        resetWorkOrdersIfUserIdChanged(previousUserId, authUserId(user));
      },
      clearLocalSession() {
        const previousUserId = authUserId(this.user);

        this.token = null;
        this.user = null;
        this.sessionError = null;
        this.isReady = true;
        this.isRestoring = false;
        resetWorkOrdersIfUserIdChanged(previousUserId, null);
      },
      async loginWithPassword(email: string, password: string) {
        const result = await login(email, password);
        this.setAuth(result.access_token, result.user);
        this.isReady = true;
        this.isRestoring = false;
        return result;
      },
      async restoreSession() {
        this.sessionError = null;
        this.isRestoring = true;

        try {
          const result = await refreshSession();
          this.setAuth(result.access_token, result.user, {
            preserveOpenedWorkspaceOnInitialUser: true,
          });
        } catch (error: unknown) {
          if (axios.isAxiosError(error)) {
            const status = error.response?.status;
            if (status === 401) {
              this.clearLocalSession();
              return;
            }
          }

          this.clearLocalSession();
          this.sessionError =
            "Сейчас не удалось восстановить сессию. Попробуйте ещё раз.";
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
