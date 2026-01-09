import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import { pinia } from "@/pinia";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  timeout: 30000,
});

http.interceptors.request.use((config) => {
  const auth = useAuthStore(pinia);
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
    if (status === 401) {
      auth.logout();
    }

    return Promise.reject(err);
  },
);
