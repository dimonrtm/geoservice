import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { workspaceResponse } from "./recovery-helpers";

async function login(page: Page) {
  await page.goto("/");
  await page
    .getByLabel("Электронная почта")
    .fill("alexey.editor@example.local");
  await page
    .getByLabel("Пароль", { exact: true })
    .fill("alexey-editor-password");
  await page.getByTestId("login-submit").click();
}

test("damaged display fields stay visible and a valid identity still opens", async ({
  page,
}) => {
  await page.route("**/work-orders/assigned-to-me", async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    const order = body.workOrders.find(
      (row: { code: string }) => row.code === "WO-001",
    );
    order.title = 7;
    order.status = "invalid";
    body.workOrders.push(null);
    await route.fulfill({ response, json: body });
  });
  await login(page);
  const card = page.locator(".workOrderCard").filter({ hasText: "WO-001" });
  await expect(card).toContainText("Некорректное название наряда");
  await expect(card).toContainText("Некорректный статус наряда");
  const invalid = page
    .locator(".workOrderCard")
    .filter({ hasText: "Некорректные данные наряда" });
  await expect(invalid).toBeVisible();
  await expect(invalid.locator("button")).toHaveCount(0);
  const evidence = fileURLToPath(
    new URL("../../docs/full_refactoring/evidence/", import.meta.url),
  );
  await mkdir(evidence, { recursive: true });
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await card.scrollIntoViewIfNeeded();
    await expect(card.getByTestId("work-order-data-issues")).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: `${evidence}/work-orders-errors-${width}.png`,
      fullPage: true,
    });
  }
  await card.locator("button.workOrderButton").click();
  await expect(page.getByTestId("workspace-open-action")).toContainText(
    "Открыть",
  );
  const loaded = page.waitForResponse(workspaceResponse);
  await page.getByTestId("workspace-open-action").click();
  expect((await loaded).status()).toBe(200);
  await expect(page.getByTestId("workspace-details-grid")).toBeVisible();
  await expect(page.getByTestId("workspace-details-panel")).toContainText(
    "Некорректное название наряда",
  );
});

test("invalid Open context stops before GET and offers no retry", async ({
  page,
}) => {
  let mapReads = 0;
  page.on("request", (request) => {
    if (
      request.method() === "GET" &&
      /\/edit-versions\/[^/?]+$/.test(request.url())
    )
      mapReads++;
  });
  await page.route("**/work-orders/*/edit-versions", async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    body.editVersion.workOrderId = "ffffffff-1111-4111-8111-111111111111";
    await route.fulfill({ response, json: body });
  });
  await login(page);
  await page
    .locator("button.workOrderButton")
    .filter({ hasText: "WO-001" })
    .click();
  await page.getByTestId("workspace-open-action").click();
  const panel = page.getByTestId("workspace-details-panel");
  await expect(panel).toContainText(
    "Некорректный идентификатор наряда рабочей версии",
  );
  await expect(panel.getByTestId("error-action")).toHaveCount(0);
  await expect(panel.getByTestId("workspace-details-grid")).toHaveCount(0);
  expect(mapReads).toBe(0);
});
