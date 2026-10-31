import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import { pinia } from "@/pinia";
import { getApiBaseUrl } from "@/api/baseUrl";

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

http.interceptors.request.use(async (config) => {
  const auth = useAuthStore(pinia);
  const epoch = auth.sessionEpoch;
  const authMutationOrStatus =
    /\/api\/v1\/auth\/(?:login|logout|session\/(?:refresh|status))$/.test(
      config.url ?? "",
    );
  if (
    auth.sessionId &&
    !authMutationOrStatus &&
    (!(await auth.ensureSessionReady()) || epoch !== auth.sessionEpoch)
  ) {
    throw new axios.CanceledError("Состояние сессии не подтверждено");
  }
  config.sessionEpoch = auth.sessionEpoch;
  config.sessionActorId = auth.user?.id ?? null;
  const token = config.authToken === undefined ? auth.token : config.authToken;
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  } else if (config.authToken === null) {
    config.headers.delete("Authorization");
  }
  return config;
});

http.interceptors.response.use(
  (r) => r,
  (err) => {
    const auth = useAuthStore(pinia);
    const status = err?.response?.status;
    const code = err?.response?.data?.code;
    if (
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
