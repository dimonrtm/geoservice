import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(
  new URL("../../../infra/m4/package.json", import.meta.url),
);
const { chromium, expect: baseExpect, selectors } = require("@playwright/test");
const expect = baseExpect.configure({ timeout: 20_000 });
selectors.setTestIdAttribute("data-test");
const workspaceResponse = (response) =>
  response.url().endsWith("/workspace") && response.status() === 200;

async function launch(origin) {
  const browser = await chromium.launch({
    args: ["--enable-unsafe-swiftshader"],
  });
  const context = await browser.newContext({
    baseURL: origin,
    viewport: { width: 1440, height: 1000 },
    serviceWorkers: "block",
  });
  context.setDefaultTimeout(20_000);
  const page = await context.newPage();
  return { browser, context, page };
}

async function login(page) {
  await page.goto("/");
  await page
    .getByLabel("Электронная почта")
    .fill("alexey.editor@example.local");
  await page
    .getByLabel("Пароль", { exact: true })
    .fill("alexey-editor-password");
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/auth/login") && r.status() === 200,
  );
  await page.getByTestId("login-submit").click();
  // Используется только в памяти для дополнительных probes; не сохраняется в evidence.
  return (await (await response).json()).access_token;
}

// Сценарий выбора и drag перенесён из M4, без привязки к его Compose и портам.
async function moveLine(page, workspace) {
  const feature = workspace.workOrder.editVersion.features.features.find(
    (f) => f.properties.assetCode === "L-003",
  );
  expect(Boolean(feature)).toBe(true);
  const canvas = page.locator(".maplibregl-canvas");
  await expect(canvas).toBeVisible();
  const mercator = (lng, lat) => [
    lng / 360 + 0.5,
    0.5 -
      Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) / (2 * Math.PI),
  ];
  await expect(async () => {
    const box = await canvas.boundingBox();
    const [w, s, e, n] = workspace.workOrder.scope.aoi.extent;
    const [left, bottom] = mercator(w, s);
    const [right, top] = mercator(e, n);
    const [x, y] = mercator(...feature.geometry.coordinates[1]);
    const scale = Math.min(
      (box.width - 96) / (right - left),
      (box.height - 96) / (bottom - top),
    );
    await page.mouse.click(
      box.x + box.width / 2 + (x - (left + right) / 2) * scale,
      box.y + box.height / 2 + (y - (top + bottom) / 2) * scale,
    );
    const option = page.getByTestId("line-option").filter({ hasText: "L-003" });
    if (await option.isVisible()) await option.click();
    await expect(
      page.getByLabel("Переместить внутреннюю вершину линии"),
    ).toBeVisible({ timeout: 1000 });
  }).toPass({ timeout: 20_000 });
  const marker = await page
    .getByLabel("Переместить внутреннюю вершину линии")
    .boundingBox();
  const x = marker.x + marker.width / 2,
    y = marker.y + marker.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + 12, y + 8, { steps: 8 });
  await page.mouse.up();
  await expect(page.getByTestId("save-edit")).toBeEnabled();
  return feature;
}

export async function workflow(origin, layerId, evidence) {
  const { browser, context, page } = await launch(origin);
  const requests = [];
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.pathname.startsWith("/api/v1/"))
      requests.push({
        method: request.method(),
        origin: url.origin,
        path: url.pathname,
      });
  });
  try {
    const token = await login(page);
    const cookie = (await context.cookies()).find(
      (c) => c.name === "geoservice_session",
    );
    expect(
      Boolean(
        cookie?.secure &&
        cookie?.httpOnly &&
        cookie?.path === "/api/v1/auth" &&
        cookie?.sameSite === "Lax",
      ),
    ).toBe(true);
    await page
      .locator("button.workOrderButton")
      .filter({ hasText: "WO-001" })
      .click();
    let readback = page.waitForResponse(workspaceResponse);
    await page.getByTestId("workspace-open-action").click();
    const initial = await (await readback).json();
    const feature = await moveLine(page, initial);
    readback = page.waitForResponse(workspaceResponse);
    await page.getByTestId("save-edit").click();
    const saved = await (await readback).json();
    const currentGeometry = (workspace) =>
      workspace.workOrder.editVersion.features.features.find(
        (f) => f.id === feature.id,
      ).geometry;
    expect(currentGeometry(saved)).not.toEqual(feature.geometry);
    expect(saved.workOrder.editVersion.changeSet.baselineGeometry).toEqual(
      feature.geometry,
    );
    const refresh = page.waitForResponse(
      (r) => r.url().endsWith("/auth/session/refresh") && r.status() === 200,
    );
    readback = page.waitForResponse(workspaceResponse);
    await page.reload();
    await refresh;
    const restored = await (await readback).json();
    expect(currentGeometry(restored)).toEqual(currentGeometry(saved));
    await expect(page.getByTestId("revert-edit")).toBeEnabled();
    await page.screenshot({
      path: path.join(evidence, "saved-after-reload.png"),
    });
    await page.getByTestId("revert-edit").click();
    readback = page.waitForResponse(workspaceResponse);
    await page.getByTestId("revert-proceed").click();
    const reverted = await (await readback).json();
    expect(currentGeometry(reverted)).toEqual(feature.geometry);
    expect(reverted.workOrder.editVersion.hasPersistedChangeSet).toBe(false);
    await expect(page.getByTestId("revert-edit")).toBeDisabled();
    const disabled = await context.request.post(
      `${origin}/api/v1/ws/layers/${layerId}/ticket`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    expect(disabled.status()).toBe(403);
    const disabledCode = (await disabled.json()).code;
    expect(disabledCode).toBe("LEGACY_GIS_API_DISABLED");
    const logout = page.waitForResponse(
      (r) => r.url().endsWith("/auth/logout") && r.status() === 200,
    );
    await page.getByTestId("logout-desktop").click();
    await logout;
    await expect(page.getByTestId("login-submit")).toBeVisible();
    expect(
      (await context.cookies()).some((c) => c.name === "geoservice_session"),
    ).toBe(false);
    const negative = await page.evaluate(async () => {
      const refresh = await fetch("/api/v1/auth/session/refresh", {
        method: "POST",
        credentials: "include",
      });
      const protectedResponse = await fetch(
        "/api/v1/work-orders/assigned-to-me",
      );
      const unknown = await fetch("/api/v1/inf02-missing");
      return {
        refresh: refresh.status,
        protected: protectedResponse.status,
        missing: unknown.status,
        missingType: unknown.headers.get("content-type"),
      };
    });
    expect(negative.refresh).toBe(401);
    expect(negative.protected).toBe(401);
    expect(negative.missing).toBe(404);
    expect(negative.missingType).toContain("application/json");
    expect(requests.length).toBeGreaterThan(10);
    expect(requests.every((r) => r.origin === origin)).toBe(true);
    expect(pageErrors).toEqual([]);
    return {
      browser: browser.version(),
      secureCookie: true,
      refresh: true,
      saveReadbackRevert: true,
      legacyDisabledCode: disabledCode,
      negative,
      requests,
      pageErrors,
    };
  } finally {
    await browser.close();
  }
}

export async function websocket(origin, layerId) {
  const { browser, page } = await launch(origin);
  try {
    const token = await login(page);
    return await page.evaluate(
      async ({ layerId, token }) => {
        const response = await fetch(`/api/v1/ws/layers/${layerId}/ticket`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.status !== 200)
          throw new Error(`Выдача ticket: ${response.status}`);
        const { ticket } = await response.json();
        const url = new URL(`/api/v1/ws/layers/${layerId}`, location.origin);
        url.protocol = location.protocol === "https:" ? "wss:" : "ws:";
        url.searchParams.set("ticket", ticket);
        const socket = new WebSocket(url);
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            socket.close();
            reject(new Error("Нет connected за 10 секунд"));
          }, 10_000);
          socket.onerror = () => {
            clearTimeout(timeout);
            reject(new Error("Ошибка WebSocket"));
          };
          socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === "connected" && message.layerId === layerId) {
              clearTimeout(timeout);
              resolve();
            }
          };
        });
        const rejected = (address) =>
          new Promise((resolve, reject) => {
            const probe = new WebSocket(address);
            const timeout = setTimeout(() => {
              probe.close();
              reject(new Error("Нет отказа WebSocket за 10 секунд"));
            }, 10_000);
            probe.onopen = () => {
              clearTimeout(timeout);
              probe.close();
              reject(new Error("Недопустимое WebSocket-соединение разрешено"));
            };
            probe.onerror = () => {};
            probe.onclose = () => {
              clearTimeout(timeout);
              resolve(true);
            };
          });
        const replayRejected = await rejected(url);
        url.search = "";
        const missingRejected = await rejected(url);
        const start = performance.now();
        await new Promise((resolve) => setTimeout(resolve, 65_000));
        const durationMs = Math.round(performance.now() - start);
        if (socket.readyState !== WebSocket.OPEN)
          throw new Error("Соединение закрылось до окончания проверки");
        // Дождаться close, чтобы nginx записал запрос в access log до его проверки.
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(
            () => reject(new Error("WebSocket не закрылся")),
            5000,
          );
          socket.onclose = () => {
            clearTimeout(timeout);
            resolve();
          };
          socket.close();
        });
        return {
          connected: true,
          durationMs,
          replayRejected,
          missingRejected,
          origin: url.origin,
        };
      },
      { layerId, token },
    );
  } finally {
    await browser.close();
  }
}
