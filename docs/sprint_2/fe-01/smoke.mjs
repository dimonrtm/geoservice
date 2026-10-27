import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(
  new URL("../../../infra/m4/package.json", import.meta.url),
);
const { chromium, expect } = require("@playwright/test");
const root = fileURLToPath(
  new URL("../../../apps/frontend/dist/", import.meta.url),
);
const evidence = fileURLToPath(new URL("../evidence/fe-01/", import.meta.url));
await mkdir(evidence, { recursive: true });
const mime = {
  ".js": "text/javascript",
  ".css": "text/css",
  ".html": "text/html",
  ".svg": "image/svg+xml",
};
const server = createServer(async (req, res) => {
  try {
    const name = new URL(req.url, "http://localhost").pathname;
    const file = path.resolve(root, `.${name === "/" ? "/index.html" : name}`);
    if (!file.startsWith(root)) {
      res.writeHead(403).end();
      return;
    }
    const body = await readFile(file);
    res
      .writeHead(200, {
        "Content-Type": mime[path.extname(file)] ?? "application/octet-stream",
      })
      .end(body);
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
const results = [];
try {
  browser = await chromium.launch();
  for (const outcome of [200, 401, 503, "timeout"]) {
    const context = await browser.newContext({
      viewport: { width: 1024, height: 768 },
    });
    const page = await context.newPage();
    let refreshes = 0;
    let logins = 0;
    let release;
    let arrived;
    const started = new Promise((resolve) => {
      arrived = resolve;
    });
    const gate = new Promise((resolve) => {
      release = resolve;
    });
    await context.route("**/api/**", async (route) => {
      const url = route.request().url();
      if (url.endsWith("/auth/login")) logins++;
      if (!url.endsWith("/auth/session/refresh")) {
        await route.fulfill({ status: 404, json: {} });
        return;
      }
      refreshes++;
      if (refreshes === 1) {
        await route.fulfill({ status: 503, json: {} });
        return;
      }
      arrived();
      await gate;
      if (outcome === "timeout") {
        await route.abort().catch(() => {});
        return;
      }
      await route.fulfill({
        status: outcome,
        json:
          outcome === 200
            ? {
                access_token: "synthetic-browser-fixture",
                user: {
                  id: "reviewer-fixture",
                  email: "reviewer@example.local",
                  role: "reviewer",
                },
              }
            : {},
      });
    });
    await page.goto(origin);
    await page.locator('[data-test="error-action"]').click();
    await started;
    await expect(
      page.getByText("Восстановление сессии", { exact: true }),
    ).toBeVisible();
    await expect(page.locator('[data-test="login-submit"]')).toHaveCount(0);
    await expect(page.locator('[data-test="error-action"]')).toHaveCount(0);
    await expect(page.locator('[data-test="session-logout"]')).toHaveCount(0);
    if (outcome === 200)
      await page.screenshot({ path: path.join(evidence, "retry-waiting.png") });
    const began = Date.now();
    if (outcome !== "timeout") release();
    if (outcome === 200)
      await expect(
        page.getByText("Выполнен вход", { exact: true }),
      ).toBeVisible();
    else if (outcome === 401)
      await expect(page.locator('[data-test="login-submit"]')).toBeVisible();
    else
      await expect(page.locator('[data-test="error-action"]')).toBeVisible({
        timeout: 35000,
      });
    if (logins !== 0 || refreshes !== 2)
      throw new Error("Неожиданное число auth-запросов");
    results.push({
      outcome,
      refreshes,
      logins,
      waitMs: Date.now() - began,
      passed: true,
    });
    if (outcome === "timeout") release();
    await context.close();
  }
  await writeFile(
    path.join(evidence, "verification.json"),
    JSON.stringify(
      {
        mode: "production bundle with mock API; no backend cookie validation",
        results,
      },
      null,
      2,
    ) + "\n",
  );
  console.log(JSON.stringify(results));
} finally {
  await browser?.close();
  await new Promise((resolve) => server.close(resolve));
}
