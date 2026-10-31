// Реальный Chromium/MapLibre, синтетические ответы API. Не backend acceptance.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
const require = createRequire(
  new URL("../../../infra/m4/package.json", import.meta.url),
);
const { chromium, expect } = require("@playwright/test");
const root = path.resolve(
  fileURLToPath(new URL("../../../apps/frontend/dist/", import.meta.url)),
);
const evidence = fileURLToPath(new URL("./evidence/", import.meta.url));
await mkdir(evidence, { recursive: true });
const mime = {
  ".js": "text/javascript",
  ".css": "text/css",
  ".html": "text/html",
  ".svg": "image/svg+xml",
};
const server = createServer(async (req, res) => {
  try {
    const pathname = new URL(req.url, "http://localhost").pathname;
    const file = path.resolve(
      root,
      `.${pathname === "/" ? "/index.html" : pathname}`,
    );
    if (!file.startsWith(root + path.sep)) {
      res.writeHead(403).end();
      return;
    }
    res
      .writeHead(200, {
        "Content-Type": mime[path.extname(file)] ?? "application/octet-stream",
      })
      .end(await readFile(file));
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const workOrder = {
  id: "wo-1",
  code: "WO-001",
  title: "Проверка участка сети",
  description: null,
  status: "in_progress",
};
const workspace = {
  workOrder: {
    ...workOrder,
    scope: {
      aoi: {
        id: "aoi",
        name: "AOI",
        description: null,
        extent: [65.5, 44.8, 65.54, 44.84],
        geometry: {
          type: "Polygon",
          coordinates: [
            [
              [65.5, 44.8],
              [65.54, 44.8],
              [65.54, 44.84],
              [65.5, 44.84],
              [65.5, 44.8],
            ],
          ],
        },
      },
    },
    editVersion: {
      id: "ev-1",
      status: "open",
      baseNetworkRevision: 1,
      draftVersionToken: "1",
      hasPersistedChangeSet: false,
      basicValidation: null,
      changeSet: null,
      features: {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            id: "line-1",
            properties: { assetCode: "L-003" },
            geometry: {
              type: "LineString",
              coordinates: [
                [65.52, 44.82],
                [65.525, 44.8205],
                [65.53, 44.82],
              ],
            },
          },
        ],
      },
      associations: [],
    },
  },
};
let browser;
const results = [];
try {
  browser = await chromium.launch({
    channel: "msedge",
    args: ["--enable-unsafe-swiftshader"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
  });
  const mutations = [];
  await context.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    let json;
    if (pathname.endsWith("/auth/session/refresh"))
      json = {
        access_token: "synthetic-fe02",
        token_type: "bearer",
        session_id: "fe02-session",
        user: { id: "actor", email: "editor@example.local", role: "editor" },
      };
    else if (pathname.endsWith("/auth/session/status"))
      json = { session_id: "fe02-session", state: "active" };
    else if (pathname.endsWith("/work-orders/assigned-to-me"))
      json = { workOrders: [workOrder] };
    else if (pathname.endsWith("/workspace")) json = workspace;
    else {
      mutations.push({ pathname, method: route.request().method() });
      await route.fulfill({ status: 404, json: {} });
      return;
    }
    await route.fulfill({ json });
  });
  // Подложка не зависит от сети в smoke; это не тест внешнего OSM.
  await context.route("https://tile.openstreetmap.org/**", (route) =>
    route.fulfill({
      contentType: "image/png",
      body: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=",
        "base64",
      ),
    }),
  );
  await context.addInitScript(() => {
    sessionStorage.setItem(
      "geoservice:opened-workspace",
      JSON.stringify({ workOrderId: "wo-1", editVersionId: "ev-1" }),
    );
    if (sessionStorage.getItem("fe02-webgl-enabled") === "yes") return;
    const getContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (kind, ...args) {
      if (String(kind).includes("webgl")) return null;
      return getContext.call(this, kind, ...args);
    };
  });
  const page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto(origin);
  await expect(
    page.locator('[data-test="workspace-details-title"]'),
  ).toContainText(workOrder.title);
  const alert = page.locator('.workspaceMap [role="alert"]');
  await expect(alert).toContainText("Не удалось запустить карту");
  await expect(alert).toContainText(
    "Обновите страницу с помощью кнопки обновления в браузере.",
  );
  await expect(alert.locator("button")).toHaveCount(0);
  await expect(
    page.locator('[data-test="workspace-edit-commands"]'),
  ).toHaveCount(0);
  await expect(page.locator('[data-test="work-order-wo-1"]')).toBeVisible();
  await page.screenshot({
    path: path.join(evidence, "startup-error-desktop.png"),
    fullPage: true,
  });
  results.push(
    "Реальный отказ WebGL: alert виден, команды скрыты, список нарядов доступен",
  );
  // Уменьшенный CSS viewport проверяет reflow при эквиваленте 200% от 1280x900.
  // Это не управление масштабом через browser toolbar.
  for (const [name, width, height] of [
    ["narrow", 390, 900],
    ["zoom-200", 640, 450],
  ]) {
    await page.setViewportSize({ width, height });
    await alert.locator("p").scrollIntoViewIfNeeded();
    await page.screenshot({
      path: path.join(evidence, `startup-error-${name}.png`),
      fullPage: true,
    });
    const dimensions = await alert.evaluate((el) => {
      const card = el.firstElementChild;
      const outer = el.getBoundingClientRect(),
        inner = card.getBoundingClientRect();
      return {
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        left: inner.left >= outer.left,
        right: inner.right <= outer.right + 1,
      };
    });
    assert.ok(
      dimensions.scrollWidth <= dimensions.clientWidth + 1 &&
        dimensions.left &&
        dimensions.right,
      `${name}: ${JSON.stringify(dimensions)}`,
    );
    await expect(alert.locator("h2")).toBeInViewport();
    await expect(alert.locator("p")).toBeInViewport();
    results.push(`${name}: карточка не выходит за область сообщения`);
  }
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.evaluate(() =>
    sessionStorage.setItem("fe02-webgl-enabled", "yes"),
  );
  await page.reload();
  await expect(
    page.locator('[data-test="workspace-edit-commands"]'),
  ).toBeVisible({ timeout: 20000 });
  await expect(page.locator('.workspaceMap [role="alert"]')).toHaveCount(0);
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await expect(page.locator('[data-test="save-edit"]')).toBeDisabled();
  await page.screenshot({
    path: path.join(evidence, "after-refresh.png"),
    fullPage: true,
  });
  assert.deepEqual(mutations, []);
  assert.deepEqual(pageErrors, []);
  results.push(
    "После reload без ограничения WebGL карта и команды доступны; Save без выбора заблокирован; mutations и pageerror отсутствуют",
  );
  await context.close();
  console.log(JSON.stringify({ passed: true, results }, null, 2));
} finally {
  await writeFile(
    path.join(evidence, "results.json"),
    JSON.stringify({ results }, null, 2) + "\n",
  );
  await browser?.close();
  await new Promise((resolve) => server.close(resolve));
}
