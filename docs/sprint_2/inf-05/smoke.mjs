import {
  editorReadback,
  isEditVersionMap,
} from "../../../infra/m4/editor-readback.mjs";
import { createRequire } from "node:module";
import path from "node:path";
import { writeFile } from "node:fs/promises";
import assert from "node:assert/strict";

const require = createRequire(
  new URL("../../../infra/m4/package.json", import.meta.url),
);
const { chromium, expect: baseExpect, selectors } = require("@playwright/test");
const expect = baseExpect.configure({ timeout: 20_000 });
selectors.setTestIdAttribute("data-test");
const workspaceResponse = (response) =>
  isEditVersionMap(response.url()) && response.status() === 200;

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
async function moveLine(page, workspace, evidenceDirectory) {
  const feature = workspace.workOrder.editVersion.features.features.find(
    (f) => f.properties.assetCode === "L-003",
  );
  expect(Boolean(feature)).toBe(true);
  const canvas = page.locator(".maplibregl-canvas");
  await expect(canvas).toBeVisible();
  // FE-02 показывает панель команд только после готовности карты. Её появление
  // меняет геометрию canvas; координаты нельзя вычислять по одному лишь GET.
  await expect(page.getByTestId("save-edit")).toBeVisible();
  const mercator = (lng, lat) => [
    lng / 360 + 0.5,
    0.5 -
      Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) / (2 * Math.PI),
  ];
  let selectionOffsetPixels;
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
    const target = [
      box.x + box.width / 2 + (x - (left + right) / 2) * scale,
      box.y + box.height / 2 + (y - (top + bottom) / 2) * scale,
    ];
    await writeFile(
      path.join(evidenceDirectory, "map-target.json"),
      JSON.stringify(
        {
          box,
          extent: [w, s, e, n],
          target,
          vertex: feature.geometry.coordinates[1],
        },
        null,
        2,
      ) + "\n",
    );
    const handle = page.getByLabel("Переместить внутреннюю вершину линии");
    // fitBounds мог выполниться до появления панели правки, затем canvas меняет
    // высоту без повторного fit. Ищем линию обычными кликами около оценки, а не
    // подменяем карту/store или вызываем selection программно.
    for (let radius = 0; radius <= 48; radius += 8) {
      for (let dx = -radius; dx <= radius; dx += 8) {
        for (let dy = -radius; dy <= radius; dy += 8) {
          if (Math.max(Math.abs(dx), Math.abs(dy)) !== radius) continue;
          await page.mouse.click(target[0] + dx, target[1] + dy);
          const option = page
            .getByTestId("line-option")
            .filter({ hasText: "L-003" });
          if (await option.isVisible()) await option.click();
          try {
            await handle.waitFor({ state: "visible", timeout: 100 });
            selectionOffsetPixels = [dx, dy];
            return;
          } catch {}
        }
      }
    }
    await expect(handle).toBeVisible({ timeout: 1000 });
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
  return { ...feature, selectionOffsetPixels };
}

export async function checkWorkflow({ origin, fixture, evidenceDirectory }) {
  const { browser, context, page } = await launch(origin);
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  const commandResults = [];
  const geometryResponse = (response) =>
    response.request().method() === "PUT" &&
    response.url().endsWith("/geometry");
  const current = (workspace) =>
    workspace.workOrder.editVersion.features.features.find(
      (f) => f.id === fixture.featureId,
    ).geometry;
  const version = (workspace) => workspace.workOrder.editVersion;
  async function command(click) {
    const waiting = page.waitForResponse(geometryResponse);
    await click();
    const response = await waiting;
    const body = response.request().postDataBuffer();
    const result = await response.json();
    assert.equal(
      response.status(),
      200,
      `Save result: ${JSON.stringify(result).slice(0, 300)}`,
    );
    // Штатный UI поддерживает три вершины; большой запрос проверяется отдельно API smoke.
    assert.ok(body.length < 1_048_576);
    assert.equal(new URL(response.url()).origin, origin);
    commandResults.push({
      bytes: body.length,
      status: response.status(),
      commandId: JSON.parse(body).commandId,
      path: new URL(response.url()).pathname,
    });
    return result;
  }
  try {
    assert.equal(fixture.coordinates.length, 3);
    const token = await login(page);
    await page
      .locator("button.workOrderButton")
      .filter({ hasText: "WO-001" })
      .click();
    let readback = page.waitForResponse(workspaceResponse);
    await page.getByTestId("workspace-open-action").click();
    const initial = await editorReadback(page, await readback);
    assert.equal(initial.workOrder.id, fixture.workOrderId);
    const feature = await moveLine(page, initial, evidenceDirectory);
    assert.equal(feature.id, fixture.featureId);
    assert.deepEqual(feature.geometry.coordinates, fixture.coordinates);
    readback = page.waitForResponse(workspaceResponse);
    const savedResult = await command(() =>
      page.getByTestId("save-edit").click(),
    );
    const saved = await editorReadback(page, await readback);
    const changedIndices = current(saved).coordinates.flatMap((p, i) =>
      JSON.stringify(p) === JSON.stringify(feature.geometry.coordinates[i])
        ? []
        : [i],
    );
    assert.deepEqual(changedIndices, [1]);
    assert.deepEqual(current(saved), savedResult.updatedFeature.geometry);
    assert.deepEqual(
      version(saved).changeSet.baselineGeometry,
      feature.geometry,
    );
    assert.equal(version(saved).hasPersistedChangeSet, true);
    assert.notEqual(
      version(saved).draftVersionToken,
      version(initial).draftVersionToken,
    );
    readback = page.waitForResponse(workspaceResponse);
    await page.reload();
    const restored = await editorReadback(page, await readback);
    assert.deepEqual(current(restored), current(saved));
    assert.equal(
      version(restored).draftVersionToken,
      version(saved).draftVersionToken,
    );
    await expect(page.getByTestId("revert-edit")).toBeEnabled();
    await page.screenshot({
      path: path.join(evidenceDirectory, "saved-after-reload.png"),
    });
    await page.getByTestId("revert-edit").click();
    readback = page.waitForResponse(workspaceResponse);
    await command(() => page.getByTestId("revert-proceed").click());
    const reverted = await editorReadback(page, await readback);
    assert.deepEqual(current(reverted), feature.geometry);
    assert.equal(version(reverted).hasPersistedChangeSet, false);
    assert.notEqual(
      version(reverted).draftVersionToken,
      version(saved).draftVersionToken,
    );
    readback = page.waitForResponse(workspaceResponse);
    await page.reload();
    const final = await editorReadback(page, await readback);
    assert.deepEqual(current(final), feature.geometry);
    assert.equal(version(final).hasPersistedChangeSet, false);
    await expect(page.getByTestId("revert-edit")).toBeDisabled();
    const endpoint = commandResults[0].path;
    const unauth = await context.request.put(origin + endpoint, { data: {} });
    assert.equal(unauth.status(), 401);
    assert.match(unauth.headers()["content-type"], /application\/json/);
    const invalid = await context.request.put(origin + endpoint, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      data: "{broken",
    });
    assert.equal(invalid.status(), 422);
    assert.equal((await invalid.json()).code, "REQUEST_VALIDATION_ERROR");
    assert.deepEqual(pageErrors, []);
    return {
      browser: browser.version(),
      vertices: fixture.coordinates.length,
      commands: commandResults,
      saveReloadRevertReload: true,
      changedIndices,
      selectionOffsetPixels: feature.selectionOffsetPixels,
      baselineUnchanged: true,
      unauthorizedStatus: unauth.status(),
      malformedStatus: invalid.status(),
      pageErrors,
    };
  } catch (error) {
    await page
      .screenshot({ path: path.join(evidenceDirectory, "browser-failure.png") })
      .catch(() => {});
    await writeFile(
      path.join(evidenceDirectory, "browser-failure.txt"),
      (await page.locator("body").innerText()).slice(0, 12000) +
        "\n" +
        JSON.stringify(pageErrors),
    );
    throw error;
  } finally {
    await browser.close();
  }
}
