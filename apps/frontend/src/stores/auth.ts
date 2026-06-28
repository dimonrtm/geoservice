import { defineStore } from "pinia";
import axios from "axios";

import { fetchMe, login, type AuthUser } from "@/api/auth";
import { useWorkOrdersStore } from "@/stores/workOrders";

const ACCESS_TOKEN_KEY = "access_token";
const AUTH_USER_KEY = "auth_user";

type AuthState = {
  token: string | null;
  user: AuthUser | null;
  isReady: boolean;
  isRestoring: boolean;
  sessionError: string | null;
};

function readStoredToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function readStoredUser(): AuthUser | null {
  const rawValue = localStorage.getItem(AUTH_USER_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as AuthUser;
  } catch {
    localStorage.removeItem(AUTH_USER_KEY);
    return null;
  }
}

function authUserId(user: AuthUser | null): string | null {
  return user?.id ?? null;
}

function resetWorkOrdersIfUserIdChanged(
  previousUserId: string | null,
  nextUserId: string | null,
): void {
  if (previousUserId === nextUserId) {
    return;
  }

  useWorkOrdersStore().reset();
}

export const useAuthStore = defineStore(
  "auth",

  {
    state: (): AuthState => ({
      token: readStoredToken(),
      user: readStoredUser(),
      isReady: false,
      isRestoring: false,
      sessionError: null,
    }),
    getters: {
      isAuthenticated: (state) => Boolean(state.token && state.user),
    },
    actions: {
      setAuth(token: string, user: AuthUser) {
        const previousUserId = authUserId(this.user);

        this.token = token;
        this.user = user;
        this.sessionError = null;
        localStorage.setItem(ACCESS_TOKEN_KEY, token);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
        resetWorkOrdersIfUserIdChanged(previousUserId, user.id);
      },
      setUser(user: AuthUser | null) {
        const previousUserId = authUserId(this.user);

        this.user = user;
        if (user) {
          localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
        } else {
          localStorage.removeItem(AUTH_USER_KEY);
        }

        resetWorkOrdersIfUserIdChanged(previousUserId, authUserId(user));
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

        if (!this.token) {
          this.setUser(null);
          this.isReady = true;
          this.isRestoring = false;
          return;
        }

        try {
          const result = await fetchMe();
          this.setUser(result.user);
        } catch (error: unknown) {
          if (axios.isAxiosError(error)) {
            const status = error.response?.status;
            if (status === 401) {
              this.logout();
              return;
            }
          }

          this.sessionError =
            "Сейчас не удалось восстановить сессию. Попробуйте ещё раз.";
        } finally {
          this.isReady = true;
          this.isRestoring = false;
        }
      },
      logout() {
        const previousUserId = authUserId(this.user);

        this.token = null;
        this.user = null;
        this.sessionError = null;
        this.isReady = true;
        this.isRestoring = false;
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(AUTH_USER_KEY);
        resetWorkOrdersIfUserIdChanged(previousUserId, null);
      },
    },
  },
);
