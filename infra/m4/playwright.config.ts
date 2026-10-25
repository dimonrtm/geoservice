import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  workers: 1,
  retries: 0,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:15173",
    viewport: { width: 1440, height: 1000 },
    browserName: "chromium",
    serviceWorkers: "block",
    trace: "off",
    screenshot: "only-on-failure",
    launchOptions: { args: ["--enable-unsafe-swiftshader"] },
    testIdAttribute: "data-test",
  },
});
