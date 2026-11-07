import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";
import { createAppBrandingPlugin, resolveAppName } from "./build/appBranding";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const frontendRoot = fileURLToPath(new URL(".", import.meta.url));
  const environment = loadEnv(mode, frontendRoot, "VITE_");
  const appName = resolveAppName(environment.VITE_APP_NAME);

  return {
    plugins: [vue(), createAppBrandingPlugin(appName)],
    define: { __APP_NAME__: JSON.stringify(appName) },
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
    },
  };
});
