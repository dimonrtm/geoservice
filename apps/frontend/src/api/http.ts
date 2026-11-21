import axios from "axios";
import { getApiBaseUrl } from "@/api/baseUrl";
import { SessionNotConfirmedError } from "./sessionNotConfirmedError";

declare module "axios" {
  interface AxiosRequestConfig {
    authErrorHandling?: "caller";
    /** undefined: текущий store; null: без bearer; string: явный bearer запроса. */
    authToken?: string | null;
  }
  interface InternalAxiosRequestConfig {
    sessionEpoch?: number;
    sessionActorId?: string | null;
  }
}

export const http = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
});

export interface HttpSession {
  readonly token: string | null;
  readonly sessionId: string | null;
  readonly sessionEpoch: number;
  readonly user: { readonly id: string } | null;
  ensureSessionReady(): Promise<boolean>;
  handleUnauthorizedResponse(error: unknown, requestEpoch?: number): void;
}

export function installHttpSession(auth: HttpSession): () => void {
  let installed = true;
  const requestId = http.interceptors.request.use(async (config) => {
    if (!installed) throw new axios.CanceledError("Приложение закрыто");
    const epoch = auth.sessionEpoch;
    const authMutationOrStatus =
      /\/api\/v1\/auth\/(?:login|logout|session\/(?:refresh|status))$/.test(
        config.url ?? "",
      );
    if (auth.sessionId && !authMutationOrStatus) {
      const ready = await auth.ensureSessionReady();
      if (!installed || epoch !== auth.sessionEpoch)
        throw new axios.CanceledError("Сессия пользователя изменилась");
      if (!ready)
        throw new SessionNotConfirmedError("Состояние сессии не подтверждено");
    }
    config.sessionEpoch = auth.sessionEpoch;
    config.sessionActorId = auth.user?.id ?? null;
    const token =
      config.authToken === undefined ? auth.token : config.authToken;
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    } else if (config.authToken === null) {
      config.headers.delete("Authorization");
    }
    return config;
  });

  const responseId = http.interceptors.response.use(
    (r) => r,
    (err) => {
      const status = err?.response?.status;
      const code = err?.response?.data?.code;
      if (
        installed &&
        err?.config?.authErrorHandling !== "caller" &&
        (status === 401 ||
          (status === 403 &&
            ["ROLE_NOT_ALLOWED", "USER_INACTIVE"].includes(code)))
      ) {
        auth.handleUnauthorizedResponse(err, err?.config?.sessionEpoch);
      }

      return Promise.reject(err);
    },
  );

  return () => {
    if (!installed) return;
    installed = false;
    http.interceptors.request.eject(requestId);
    http.interceptors.response.eject(responseId);
  };
}
