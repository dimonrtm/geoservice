export const appConfig = {
  enableDevAuth: import.meta.env.VITE_ENABLE_DEV_AUTH === "true",
} as const;
