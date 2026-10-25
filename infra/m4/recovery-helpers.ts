import { expect, type Page } from "@playwright/test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";

const exec = promisify(execFile);
const cwd = fileURLToPath(new URL(".", import.meta.url));
export const project = process.env.M4_PROJECT;
if (!project || !/^geoservice-m4-[a-f0-9]{8}$/.test(project)) {
  throw new Error(
    "Запускайте M4 через npm test: требуется отдельный Compose-проект",
  );
}
export async function compose(...args: string[]) {
  return (
    await exec(
      "docker",
      ["compose", "-p", project!, "-f", "compose.yml", ...args],
      { cwd, windowsHide: true, timeout: 60_000 },
    )
  ).stdout.trim();
}
export async function processStartedAt() {
  const id = await compose("ps", "-q", "api");
  return (
    await exec("docker", ["inspect", "--format", "{{.State.StartedAt}}", id], {
      windowsHide: true,
    })
  ).stdout.trim();
}
export async function snapshot(version: string, feature: string) {
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
export const workspaceResponse = (r: { url(): string; status(): number }) =>
  r.url().endsWith("/workspace") && r.status() === 200;
export async function openWorkspace(page: Page) {
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
export async function ordinaryRevert(page: Page) {
  await page.getByTestId("revert-edit").click();
  const response = page.waitForResponse(workspaceResponse);
  await page.getByTestId("revert-proceed").click();
  const workspace = await (await response).json();
  await expect(page.getByTestId("revert-edit")).toBeDisabled();
  return workspace;
}
export async function moveLine(page: Page, workspace: any) {
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

export async function storedRecoveries(page: Page) {
  return page.evaluate(
    () =>
      new Promise<any[]>((resolve, reject) => {
        const req = indexedDB.open("geoservice-workspace-recovery", 1);
        req.onerror = () => reject(req.error);
        req.onsuccess = () => {
          const db = req.result;
          const tx = db.transaction("recoveries", "readonly");
          const rows = tx.objectStore("recoveries").getAll();
          rows.onsuccess = () => resolve(rows.result);
          rows.onerror = () => reject(rows.error);
          tx.oncomplete = () => db.close();
        };
      }),
  );
}
