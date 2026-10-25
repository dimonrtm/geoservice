import { test, expect, chromium, type BrowserContext } from "@playwright/test";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
  openWorkspace,
  ordinaryRevert,
  moveLine,
  snapshot,
  storedRecoveries,
  workspaceResponse,
  project,
} from "./recovery-helpers";
import { compose } from "./recovery-helpers";

test("real assignment loss stops replay until explicit access confirmation", async ({
  page,
  context,
}) => {
  let workspace = await openWorkspace(page);
  if (workspace.workOrder.editVersion.hasPersistedChangeSet)
    workspace = await ordinaryRevert(page);
  const feature = await moveLine(page, workspace);
  const version = workspace.workOrder.editVersion.id;
  const workOrder = workspace.workOrder.id;
  expect(workOrder).toMatch(/^[a-f0-9-]{36}$/i);
  await compose(
    "exec",
    "-T",
    "db",
    "psql",
    "-U",
    "postgres",
    "-d",
    "m4_test",
    "-v",
    "ON_ERROR_STOP=1",
    "-c",
    `INSERT INTO "user".users(id,email,password_hash,role,is_active) SELECT gen_random_uuid(),'x01.assignee@example.local',password_hash,'editor',true FROM "user".users WHERE email='alexey.editor@example.local' ON CONFLICT(email) DO NOTHING`,
  );
  let firstBody: string | undefined;
  let denied = 0,
    replayed = 0,
    committed: any;
  const assignment = async (restore: boolean) =>
    compose(
      "exec",
      "-T",
      "db",
      "psql",
      "-U",
      "postgres",
      "-d",
      "m4_test",
      "-v",
      "ON_ERROR_STOP=1",
      "-c",
      `UPDATE work_order.work_orders SET assignee_user_id=(SELECT id FROM "user".users WHERE email='${restore ? "alexey.editor@example.local" : "x01.assignee@example.local"}') WHERE id='${workOrder}'`,
    );
  await context.route("**/features/*/geometry", async (route) => {
    if (!firstBody) {
      firstBody = route.request().postData()!;
      const response = await route.fetch();
      expect(response.status()).toBe(200);
      committed = await snapshot(version, feature.id);
      await assignment(false);
      await route.abort();
      return;
    }
    expect(route.request().postData()).toBe(firstBody);
    const response = await route.fetch();
    if (response.status() === 404) {
      expect((await response.json()).code).toBe("EDIT_VERSION_NOT_FOUND");
      denied++;
    } else {
      expect(response.status()).toBe(200);
      replayed++;
    }
    await route.fulfill({ response });
  });
  try {
    await page.getByTestId("save-edit").click();
    await expect.poll(() => denied).toBe(1);
    await expect
      .poll(
        async () =>
          (await storedRecoveries(page))[0]?.requiresAccessConfirmation,
      )
      .toBe(true);
    await assignment(true);
    await page.reload();
    await expect(page.getByTestId("resume-recovery")).toHaveCount(1);
    expect(replayed).toBe(0);
    await page.getByTestId("resume-recovery").click();
    await page.getByTestId("confirm-resume").click();
    await expect
      .poll(async () => (await storedRecoveries(page)).length)
      .toBe(0);
    expect(replayed).toBe(1);
    expect(await snapshot(version, feature.id)).toEqual(committed);
    const directory = fileURLToPath(
      new URL("../../docs/sprint_2/evidence/s2-x01/", import.meta.url),
    );
    await mkdir(directory, { recursive: true });
    await writeFile(
      directory + "access-restoration.json",
      JSON.stringify(
        {
          project,
          verifiedAt: new Date().toISOString(),
          workOrder,
          denied,
          replayed,
          committed,
          after: await snapshot(version, feature.id),
        },
        null,
        2,
      ) + "\n",
    );
  } finally {
    await assignment(true);
  }
});
for (const action of ["Save", "Revert"] as const)
  test(`${action}: recovery survives actual browser close and restart`, async ({}, testInfo) => {
    const root = fileURLToPath(new URL("./test-results/", import.meta.url));
    await mkdir(root, { recursive: true });
    const profile = await mkdtemp(root + "s2-x01-profile-");
    const launch = () =>
      chromium.launchPersistentContext(profile, {
        headless: true,
        baseURL: "http://127.0.0.1:15173",
        viewport: { width: 1440, height: 1000 },
        serviceWorkers: "block",
        args: ["--enable-unsafe-swiftshader"],
      });
    let context: BrowserContext = await launch();
    let firstBody: string | undefined,
      url: string | undefined,
      receipt: any,
      committed: any;
    let blocked = 0,
      replayed = 0;
    try {
      let page = await context.newPage();
      let w = await openWorkspace(page);
      if (w.workOrder.editVersion.hasPersistedChangeSet)
        w = await ordinaryRevert(page);
      const feature = await moveLine(page, w);
      if (action === "Revert") {
        const r = page.waitForResponse(workspaceResponse);
        await page.getByTestId("save-edit").click();
        w = await (await r).json();
        await expect(page.getByTestId("revert-edit")).toBeEnabled();
      }
      const version = w.workOrder.editVersion.id,
        before = await snapshot(version, feature.id);
      await context.route("**/features/*/geometry", async (route) => {
        if (firstBody) {
          blocked++;
          await route.abort();
          return;
        }
        firstBody = route.request().postData()!;
        url = route.request().url();
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        receipt = await response.json();
        committed = await snapshot(version, feature.id);
        await route.abort();
      });
      if (action === "Save") await page.getByTestId("save-edit").click();
      else {
        await page.getByTestId("revert-edit").click();
        await page.getByTestId("revert-proceed").click();
      }
      await expect.poll(() => blocked).toBeGreaterThan(0);
      const saved = (await storedRecoveries(page))[0];
      expect(saved.command.request).toEqual(JSON.parse(firstBody!));
      await context.close();
      const closedAt = new Date().toISOString();
      context = await launch();
      await context.route("**/features/*/geometry", async (route) => {
        expect(route.request().url()).toBe(url);
        expect(route.request().postData()).toBe(firstBody);
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        expect(await response.json()).toEqual(receipt);
        replayed++;
        await route.fulfill({ response });
      });
      page = await context.newPage();
      const currentRead = page.waitForResponse(
        (r) => workspaceResponse(r) && replayed > 0,
      );
      await page.goto("/");
      const current = await (await currentRead).json();
      await expect
        .poll(async () => (await storedRecoveries(page)).length)
        .toBe(0);
      expect(replayed).toBe(1);
      const after = await snapshot(version, feature.id);
      expect(after).toEqual(committed);
      expect(after.baselineBytes).toBe(before.baselineBytes);
      expect(current.workOrder.editVersion.draftVersionToken).toBe(
        receipt.draftVersionToken,
      );
      const directory = fileURLToPath(
        new URL("../../docs/sprint_2/evidence/s2-x01/", import.meta.url),
      );
      await mkdir(directory, { recursive: true });
      const evidence = {
        scenario: action,
        project,
        closedAt,
        restartedAt: new Date().toISOString(),
        command: JSON.parse(firstBody!),
        before,
        committed,
        after,
        replayed,
      };
      await writeFile(
        directory + action.toLowerCase() + "-browser-restart.json",
        JSON.stringify(evidence, null, 2) + "\n",
      );
      await testInfo.attach("Browser restart", {
        body: JSON.stringify(evidence),
        contentType: "application/json",
      });
    } finally {
      await context.close();
    }
  });

test("independent A/B/C, old replay, account isolation and each recovery consent", async ({
  page,
  context,
}) => {
  const { createIndependentWorkOrders } = await import("./s2-x01-fixture");
  await createIndependentWorkOrders();
  await openWorkspace(page);
  const commands = new Map<
    string,
    {
      body: any;
      url: string;
      authorization: string;
      receipt: any;
      committed: any;
      feature: string;
      version: string;
    }
  >();
  let release = false;
  const replays: string[] = [];
  await context.route("**/features/*/geometry", async (route) => {
    const request = route.request(),
      wo = request.url().split("/work-orders/")[1]!.split("/")[0]!;
    if (commands.has(wo)) {
      if (!release) {
        await route.abort();
        return;
      }
      const saved = commands.get(wo)!;
      expect(request.postDataJSON()).toEqual(saved.body);
      const response = await route.fetch();
      expect(await response.json()).toEqual(saved.receipt);
      replays.push(wo);
      await route.fulfill({ response });
      return;
    }
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    const receipt = await response.json();
    const parts = request.url().split("/");
    const version = parts[parts.indexOf("edit-versions") + 1]!,
      feature = parts[parts.indexOf("features") + 1]!;
    commands.set(wo, {
      body: request.postDataJSON(),
      url: request.url(),
      authorization: request.headers().authorization!,
      receipt,
      committed: await snapshot(version, feature),
      feature,
      version,
    });
    if (commands.size <= 2) await route.abort();
    else await route.fulfill({ response });
  });
  async function select(code: string) {
    await page
      .locator("button.workOrderButton")
      .filter({ hasText: code })
      .click();
    const leave = page.getByTestId("navigation-leave");
    if (await leave.isVisible()) await leave.click();
    const response = page.waitForResponse(workspaceResponse);
    await page.getByTestId("workspace-open-action").click();
    return (await response).json();
  }
  const ids: string[] = [];
  for (const code of ["X01-A", "X01-B", "X01-C"]) {
    const w = await select(code);
    ids.push(w.workOrder.id);
    await moveLine(page, w);
    await page.getByTestId("save-edit").click();
    await expect.poll(() => commands.has(w.workOrder.id)).toBe(true);
  }
  await expect(
    page.getByText("Правка сохранена в рабочей версии", { exact: true }),
  ).toBeVisible();
  expect((await storedRecoveries(page)).length).toBe(2);
  // A newer command through the public HTTP contract: UI deliberately forbids another Save while A is unknown.
  const a = commands.get(ids[0]!)!;
  const nextGeometry = structuredClone(a.body.geometry);
  nextGeometry.coordinates[1][0] += 0.00001;
  const newer = await context.request.put(a.url, {
    headers: { Authorization: a.authorization },
    data: {
      ...a.body,
      commandId: crypto.randomUUID(),
      draftVersionToken: a.receipt.draftVersionToken,
      geometry: nextGeometry,
    },
  });
  expect(newer.status()).toBe(200);
  const newReceipt = await newer.json();
  const newerSnapshot = await snapshot(a.version, a.feature);
  await page.getByTestId("logout-desktop").click();
  await expect(page.getByTestId("navigation-stay")).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(page.getByTestId("navigation-leave")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByTestId("navigation-stay")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("navigation-stay")).toHaveCount(0);
  await expect(page.getByTestId("logout-desktop")).toBeFocused();
  await page.getByTestId("logout-desktop").click();
  await page.getByTestId("navigation-leave").click();
  await expect(page.getByTestId("login-submit")).toBeVisible();
  async function login(email: string) {
    await page.getByLabel("Электронная почта").fill(email);
    await page
      .getByLabel("Пароль", { exact: true })
      .fill("alexey-editor-password");
    await page.getByTestId("login-submit").click();
    await expect(page.getByTestId("logout-desktop")).toBeVisible();
  }
  await login("x01.other@example.local");
  await expect(
    page.getByRole("heading", { name: "Восстановление команд" }),
  ).toHaveCount(0);
  expect(replays).toEqual([]);
  await page.getByTestId("logout-desktop").click();
  await expect(page.getByTestId("login-submit")).toBeVisible();
  await login("alexey.editor@example.local");
  await expect(page.getByTestId("resume-recovery")).toHaveCount(2);
  expect(replays).toEqual([]);
  release = true;
  const b = commands.get(ids[1]!)!;
  await page
    .getByTestId(`recovery-${ids[1]}`)
    .getByTestId("resume-recovery")
    .click();
  await page.getByTestId("confirm-resume").click();
  await expect.poll(() => replays).toEqual([ids[1]]);
  await expect(page.getByTestId("resume-recovery")).toHaveCount(1);
  expect(await snapshot(b.version, b.feature)).toEqual(b.committed);
  await page
    .getByTestId(`recovery-${ids[0]}`)
    .getByTestId("resume-recovery")
    .click();
  await page.getByTestId("confirm-resume").click();
  await expect.poll(async () => (await storedRecoveries(page)).length).toBe(0);
  expect(replays).toEqual([ids[1], ids[0]]);
  expect(await snapshot(a.version, a.feature)).toEqual(newerSnapshot);
  const current = await select("X01-A");
  expect(current.workOrder.editVersion.draftVersionToken).toBe(
    newReceipt.draftVersionToken,
  );
  expect(
    current.workOrder.editVersion.features.features.find(
      (f: any) => f.id === a.feature,
    ).geometry,
  ).toEqual(newerSnapshot.geometry);
  const directory = fileURLToPath(
    new URL("../../docs/sprint_2/evidence/s2-x01/", import.meta.url),
  );
  await mkdir(directory, { recursive: true });
  await writeFile(
    directory + "multi-context.json",
    JSON.stringify(
      {
        project,
        verifiedAt: new Date().toISOString(),
        ids,
        replays,
        newerSnapshot,
        after: await snapshot(a.version, a.feature),
        commands: [...commands.values()].map(
          ({ body, committed, version, feature }) => ({
            body,
            committed,
            version,
            feature,
          }),
        ),
      },
      null,
      2,
    ) + "\n",
  );
  await context.unroute("**/features/*/geometry");
  await moveLine(page, current);
  let injected = false;
  await context.route("**/features/*/geometry", async (route) => {
    const request = route.request();
    if (!injected) {
      injected = true;
      const body = request.postDataJSON();
      const geometry = structuredClone(body.geometry);
      geometry.coordinates[1][0] += 0.00001;
      const concurrent = await context.request.put(request.url(), {
        headers: { Authorization: request.headers().authorization! },
        data: { ...body, commandId: crypto.randomUUID(), geometry },
      });
      expect(concurrent.status()).toBe(200);
    }
    const response = await route.fetch();
    expect(response.status()).toBe(409);
    await route.fulfill({ response });
  });
  await page.getByTestId("save-edit").click();
  await expect(page.getByTestId("stale-comparison")).toBeVisible();
  const comparison = page.getByTestId("stale-comparison");
  await comparison
    .getByRole("button", { name: "Попытка", exact: true })
    .click();
  await expect(
    page.getByLabel("Переместить внутреннюю вершину линии"),
  ).toHaveCount(0);
  for (const [width, height] of [
    [1440, 900],
    [1024, 768],
    [768, 1024],
    [720, 450],
    [512, 384],
    [384, 512],
  ]) {
    await page.setViewportSize({ width: width!, height: height! });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await comparison.scrollIntoViewIfNeeded();
    await page.screenshot({
      path: directory + `comparison-${width}x${height}.png`,
      fullPage: true,
    });
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByTestId("comparison-discard").click();
  await expect(comparison).toHaveCount(0);
  await expect(page.getByTestId("save-edit")).toBeDisabled();
});
