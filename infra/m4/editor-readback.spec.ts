import { expect, test } from "@playwright/test";
import { openWorkspace, moveLine, ordinaryRevert } from "./recovery-helpers";
import { randomUUID } from "node:crypto";

test("map remains visible during a change-set outage and recovers without reopening", async ({
  page,
}) => {
  let changes = 0;
  let unavailable = true;
  await page.route("**/change-set", async (route) => {
    changes++;
    if (unavailable)
      await route.fulfill({ status: 503, json: { code: "UNAVAILABLE" } });
    else await route.continue();
  });
  const map = await openWorkspace(page);
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await expect(page.getByTestId("save-edit")).toBeDisabled();
  const retry = page.getByRole("button", { name: "Повторить", exact: true });
  await expect(retry).toBeVisible({ timeout: 55_000 });
  expect(changes).toBe(5);
  unavailable = false;
  await retry.click();
  await expect(retry).toBeHidden();
  if (map.workOrder.editVersion.hasPersistedChangeSet)
    await ordinaryRevert(page);
  await moveLine(page, map);
  await page.getByTestId("save-edit").click();
  await expect(page.getByTestId("revert-edit")).toBeEnabled();
  await page.reload();
  await expect(page.getByTestId("revert-edit")).toBeEnabled();
  await ordinaryRevert(page);
});

test("a concurrent Save between map and ChangeSet forces a fresh map", async ({
  page,
  request,
}) => {
  const initial = await openWorkspace(page);
  if (initial.workOrder.editVersion.hasPersistedChangeSet)
    await ordinaryRevert(page);
  const order = initial.workOrder;
  const feature = order.editVersion.features.features.find(
    (item: { properties: { assetCode: string } }) =>
      item.properties.assetCode === "L-003",
  );
  const geometry = structuredClone(feature.geometry);
  geometry.coordinates[1][1] = Number(
    (geometry.coordinates[1][1] + 0.00001).toFixed(7),
  );
  // An independently authenticated client saves after the browser receives its first snapshot.
  const login = await request.post("http://127.0.0.1:18180/api/v1/auth/login", {
    data: {
      email: "alexey.editor@example.local",
      password: "alexey-editor-password",
    },
  });
  const authorization = "Bearer " + (await login.json()).access_token;
  const root = `http://127.0.0.1:18180/api/v1/work-orders/${order.id}/edit-versions/${order.editVersion.id}`;
  const maps: string[] = [];
  let savedToken: string | undefined;
  page.on("response", async (response) => {
    if (response.url() === root && response.ok())
      maps.push(
        (await response.json()).workOrder.editVersion.draftVersionToken,
      );
  });
  await page.route("**/change-set", async (route) => {
    if (!savedToken) {
      const snapshot = await request.get(root, {
        headers: { Authorization: authorization },
      });
      const { draftVersionToken } = (await snapshot.json()).workOrder
        .editVersion;
      const result = await request.put(
        root + `/features/${feature.id}/geometry`,
        {
          headers: { Authorization: authorization },
          data: { geometry, commandId: randomUUID(), draftVersionToken },
        },
      );
      expect(result.status()).toBe(200);
      savedToken = (await result.json()).draftVersionToken;
    }
    await route.continue();
  });
  await page.reload();
  await expect(page.getByTestId("revert-edit")).toBeEnabled();
  expect(maps.length).toBeGreaterThanOrEqual(2);
  expect(maps[0]).not.toBe(savedToken);
  expect(maps.at(-1)).toBe(savedToken);
  await ordinaryRevert(page);
});
