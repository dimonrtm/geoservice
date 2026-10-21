import { test, expect, type Page } from "@playwright/test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const exec = promisify(execFile);
const cwd = fileURLToPath(new URL(".", import.meta.url));
const project = process.env.M4_PROJECT;
if (!project || !/^geoservice-m4-[a-f0-9]{8}$/.test(project)) {
  throw new Error(
    "Запускайте M4 через npm test: требуется отдельный Compose-проект",
  );
}
async function compose(...args: string[]) {
  return (
    await exec(
      "docker",
      ["compose", "-p", project!, "-f", "compose.yml", ...args],
      { cwd, windowsHide: true, timeout: 60_000 },
    )
  ).stdout.trim();
}
async function processStartedAt() {
  const id = await compose("ps", "-q", "api");
  return (
    await exec("docker", ["inspect", "--format", "{{.State.StartedAt}}", id], {
      windowsHide: true,
    })
  ).stdout.trim();
}
async function snapshot(version: string, feature: string) {
  for (const id of [version, feature]) expect(id).toMatch(/^[a-f0-9-]{36}$/i);
  const sql = `SELECT json_build_object(
    'revision', ev.draft_revision,
    'owner', ev.owner_user_id,
    'events', (SELECT count(*) FROM work_order.edit_version_change_events WHERE edit_version_id=ev.id),
    'commands', (SELECT count(*) FROM work_order.edit_version_commands WHERE edit_version_id=ev.id),
    'operation', f.operation,
    'geometry', ST_AsGeoJSON(f.geometry)::json,
    'baseline', ST_AsGeoJSON(b.geometry)::json,
    'baselineBytes', encode(ST_AsEWKB(b.geometry), 'hex')
  ) FROM work_order.edit_versions ev
  JOIN work_order.edit_version_features f ON f.edit_version_id=ev.id AND f.feature_id='${feature}'
  JOIN utility_network.default_state_features b ON b.default_state_id=ev.default_state_id AND b.feature_id=f.feature_id
  WHERE ev.id='${version}'`;
  return JSON.parse(
    await compose(
      "exec",
      "-T",
      "db",
      "psql",
      "-U",
      "postgres",
      "-d",
      "m4_test",
      "-At",
      "-v",
      "ON_ERROR_STOP=1",
      "-c",
      sql,
    ),
  );
}
const workspaceResponse = (r: { url(): string; status(): number }) =>
  r.url().endsWith("/workspace") && r.status() === 200;
async function openWorkspace(page: Page) {
  await page.goto("/");
  await page
    .getByLabel("Электронная почта")
    .fill("alexey.editor@example.local");
  await page
    .getByLabel("Пароль", { exact: true })
    .fill("alexey-editor-password");
  await page.getByTestId("login-submit").click();
  await page
    .locator("button.workOrderButton")
    .filter({ hasText: "WO-001" })
    .click();
  const response = page.waitForResponse(workspaceResponse);
  await page.getByTestId("workspace-open-action").click();
  return (await response).json();
}
async function ordinaryRevert(page: Page) {
  await page.getByTestId("revert-edit").click();
  const response = page.waitForResponse(workspaceResponse);
  await page.getByTestId("revert-proceed").click();
  const workspace = await (await response).json();
  await expect(page.getByTestId("revert-edit")).toBeDisabled();
  return workspace;
}
async function moveLine(page: Page, workspace: any) {
  const feature = workspace.workOrder.editVersion.features.features.find(
    (f: any) => f.properties.assetCode === "L-003",
  );
  expect(feature).toBeTruthy();
  const canvas = page.locator(".maplibregl-canvas");
  await expect(canvas).toBeVisible();
  // Географическую точку переводим в пиксели по реальному AOI и размеру canvas.
  // В приложении fitBounds использует padding=48, без поворота и наклона.
  const mercator = (lng: number, lat: number) => [
    lng / 360 + 0.5,
    0.5 -
      Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) / (2 * Math.PI),
  ];
  await expect(async () => {
    const box = (await canvas.boundingBox())!;
    const [w, s, e, n] = workspace.workOrder.scope.aoi.extent;
    const [left, bottom] = mercator(w, s),
      [right, top] = mercator(e, n);
    const [x, y] = mercator(
      ...(feature.geometry.coordinates[1] as [number, number]),
    );
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
  const marker = (await page
    .getByLabel("Переместить внутреннюю вершину линии")
    .boundingBox())!;
  const x = marker.x + marker.width / 2,
    y = marker.y + marker.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + 12, y + 8, { steps: 8 });
  await page.mouse.up();
  await expect(page.getByTestId("save-edit")).toBeEnabled();
  return feature;
}

for (const action of ["Save", "Revert"] as const) {
  test(`${action}: commit → потеря ответа → restart → refresh → replay`, async ({
    page,
    context,
  }, testInfo) => {
    let workspace = await openWorkspace(page);
    if (workspace.workOrder.editVersion.hasPersistedChangeSet)
      workspace = await ordinaryRevert(page);
    const feature = await moveLine(page, workspace);
    if (action === "Revert") {
      const response = page.waitForResponse(workspaceResponse);
      await page.getByTestId("save-edit").click();
      workspace = await (await response).json();
      await expect(page.getByTestId("revert-edit")).toBeEnabled();
      expect(
        workspace.workOrder.editVersion.changeSet.baselineGeometry,
      ).toEqual(feature.geometry);
    }
    const version = workspace.workOrder.editVersion.id;
    const before = await snapshot(version, feature.id);
    const startedBefore = await processStartedAt();
    const log: any[] = [];
    const errors: string[] = [];
    let command: any, originalBody: string, originalUrl: string;
    let committed: any, serverResult: any;
    let reloaded = false,
      blocked = 0,
      replayed = 0;
    let commitResolve!: () => void, commitReject!: (reason: any) => void;
    const commitReady = new Promise<void>((resolve, reject) => {
      commitResolve = resolve;
      commitReject = reject;
    });
    page.on("request", (request) => {
      if (request.url().endsWith("/workspace"))
        log.push({ event: "GET", afterReload: reloaded });
    });
    await context.route("**/features/*/geometry", async (route) => {
      try {
        const request = route.request();
        if (request.method() !== "PUT") return route.continue();
        // Refresh обновляет access token; неизменным должен остаться actor.
        const token = request.headers().authorization?.split(" ")[1];
        if (!token) throw new Error("Отсутствует авторизация команды");
        const subject = JSON.parse(
          Buffer.from(token.split(".")[1], "base64url").toString(),
        ).sub;
        expect(subject).toBe(before.owner);
        if (!command) {
          command = request.postDataJSON();
          originalBody = request.postData()!;
          originalUrl = request.url();
          log.push({ event: "first PUT", command, url: originalUrl });
          const response = await route.fetch({
            maxRetries: 0,
            maxRedirects: 0,
          });
          expect(response.status()).toBe(200);
          serverResult = await response.json();
          committed = await snapshot(version, feature.id);
          expect(committed.revision).toBe(before.revision + 1);
          expect(committed.events).toBe(before.events + 1);
          expect(committed.commands).toBe(before.commands + 1);
          expect(committed.baselineBytes).toBe(before.baselineBytes);
          expect(committed.geometry).not.toEqual(before.geometry);
          log.push({ event: "committed; response withheld" });
          await route.abort("failed");
          commitResolve();
        } else {
          expect(request.url()).toBe(originalUrl);
          expect(request.postData()).toBe(originalBody);
          if (!reloaded) {
            blocked++;
            log.push({ event: "retry blocked before backend" });
            return route.abort("failed");
          }
          replayed++;
          const response = await route.fetch({
            maxRetries: 0,
            maxRedirects: 0,
          });
          expect(response.status()).toBe(200);
          expect(await response.json()).toEqual(serverResult);
          log.push({ event: "replay success" });
          await route.fulfill({ response });
        }
      } catch (error) {
        errors.push(String(error));
        commitReject(error);
        await route.abort("failed").catch(() => {});
      }
    });
    if (action === "Save") await page.getByTestId("save-edit").click();
    else {
      await page.getByTestId("revert-edit").click();
      await page.getByTestId("revert-proceed").click();
    }
    await commitReady;
    await expect.poll(() => blocked).toBeGreaterThan(0);
    const stored = await page.evaluate(() => {
      const key = Object.keys(sessionStorage).find((k) =>
        k.startsWith("geoservice:workspace-recovery:v1:"),
      );
      return key ? JSON.parse(sessionStorage.getItem(key)!) : null;
    });
    expect(stored.state).toBe("unknown");
    expect(stored.command.request).toEqual(command);
    expect(stored.command.actorId).toBe(before.owner);
    expect(stored.command.target.editVersionId).toBe(version);
    if (action === "Revert")
      expect(command.geometry).toEqual(
        workspace.workOrder.editVersion.changeSet.baselineGeometry,
      );
    await compose("restart", "api");
    await expect
      .poll(
        async () => {
          try {
            return (await fetch("http://127.0.0.1:18180/health")).ok;
          } catch {
            return false;
          }
        },
        { timeout: 40_000 },
      )
      .toBe(true);
    const startedAfter = await processStartedAt();
    expect(startedAfter).not.toBe(startedBefore);
    expect(await snapshot(version, feature.id)).toEqual(committed);
    log.push({ event: "backend restarted", startedBefore, startedAfter });
    // Открываем барьер только после commit новой навигации той же вкладки.
    page.on("framenavigated", (frame) => {
      if (frame === page.mainFrame()) reloaded = true;
    });
    const finalReadback = page.waitForResponse(
      (r) => workspaceResponse(r) && replayed > 0,
      { timeout: 30_000 },
    );
    await page.reload();
    const current = (await (await finalReadback).json()).workOrder.editVersion;
    expect(errors).toEqual([]);
    expect(replayed).toBe(1);
    expect(log.findLastIndex((e) => e.event === "GET")).toBeGreaterThan(
      log.findIndex((e) => e.event === "replay success"),
    );
    expect(current.draftVersionToken).toBe(serverResult.draftVersionToken);
    expect(current.hasPersistedChangeSet).toBe(action === "Save");
    expect(
      current.features.features.find((f: any) => f.id === feature.id).geometry,
    ).toEqual(committed.geometry);
    if (action === "Save")
      expect(current.changeSet.baselineGeometry).toEqual(before.baseline);
    else {
      expect(current.changeSet).toBeNull();
      expect(committed.geometry).toEqual(before.baseline);
    }
    await expect(
      page.getByLabel("Переместить внутреннюю вершину линии"),
    ).toHaveCount(0);
    await expect(
      page.getByText("Выберите линию на карте для редактирования"),
    ).toBeVisible();
    await expect
      .poll(() =>
        page.evaluate(
          () =>
            Object.keys(sessionStorage).filter((key) =>
              key.startsWith("geoservice:workspace-recovery:v1:"),
            ).length,
        ),
      )
      .toBe(0);
    await expect(page.getByTestId("revert-edit"))[
      action === "Save" ? "toBeEnabled" : "toBeDisabled"
    ]();
    const after = await snapshot(version, feature.id);
    expect(after).toEqual(committed);
    const directory = fileURLToPath(
      new URL("../../docs/sprint_2/evidence/day-12/m4/", import.meta.url),
    );
    await mkdir(directory, { recursive: true });
    const evidence = {
      scenario: action,
      project,
      command,
      actorId: stored.command.actorId,
      target: stored.command.target,
      before,
      committed,
      after,
      log,
      replayed,
      blocked,
      current: {
        draftVersionToken: current.draftVersionToken,
        changeSet: current.changeSet,
      },
      verifiedAt: new Date().toISOString(),
    };
    await writeFile(
      `${directory}/${action.toLowerCase()}.json`,
      JSON.stringify(evidence, null, 2) + "\n",
    );
    await page.screenshot({ path: `${directory}/${action.toLowerCase()}.png` });
    await testInfo.attach("Результат M4", {
      body: JSON.stringify(evidence),
      contentType: "application/json",
    });
  });
}
