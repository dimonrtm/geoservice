import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import { pinia } from "@/pinia";

declare module "axios" {
  interface InternalAxiosRequestConfig {
    sessionEpoch?: number;
    sessionActorId?: string | null;
  }
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  timeout: 30000,
});

http.interceptors.request.use((config) => {
  const auth = useAuthStore(pinia);
  config.sessionEpoch = auth.sessionEpoch;
  config.sessionActorId = auth.user?.id ?? null;
  if (auth.token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${auth.token}`;
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
      status === 401 ||
      (status === 403 && ["ROLE_NOT_ALLOWED", "USER_INACTIVE"].includes(code))
    ) {
      auth.handleUnauthorizedResponse(err, err?.config?.sessionEpoch);
    }

    return Promise.reject(err);
  },
);
