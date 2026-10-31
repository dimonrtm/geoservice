// Приёмочные тесты используют настоящий backend. route.fetch/fulfill только задерживают
// неизменённый ответ сервера; abort моделирует потерю. Credentials живут в памяти.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import {
  recordAcceptanceResult,
  withAcceptanceSignals,
} from "./acceptanceResult.mjs";

const require = createRequire(
  new URL("../../../infra/m4/package.json", import.meta.url),
);
const {
  chromium,
  firefox,
  expect: baseExpect,
  selectors,
} = require("@playwright/test");
const expect = baseExpect.configure({ timeout: 15000 });
selectors.setTestIdAttribute("data-test");
const MARKER = "geoservice.auth.session.v1";
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const at = (r, suffix) => new URL(r.url()).pathname.endsWith(suffix);
const signedIn = (page) =>
  expect(page.getByTestId("logout-desktop")).toBeVisible();
const signedOut = (page) =>
  expect(page.getByTestId("login-submit")).toBeVisible();
const sessionCookie = async (context) =>
  (await context.cookies()).find((c) => c.name === "geoservice_session");
// route.fetch использует shared APIRequestContext и сам применяет Set-Cookie даже
// при последующем abort. Node proxy сохраняет ответ исключительно в памяти;
// cookie применяет только сам браузер после реальной доставки route.fulfill.
async function forward(route) {
  const request = route.request();
  const response = await fetch(request.url(), {
    method: request.method(),
    headers: await request.allHeaders(),
    body: request.postDataBuffer() ?? undefined,
    signal: AbortSignal.timeout(10000),
  });
  const body = Buffer.from(await response.arrayBuffer());
  const headers = Object.fromEntries(response.headers);
  delete headers["content-encoding"];
  delete headers["content-length"];
  return {
    status: () => response.status,
    json: async () => JSON.parse(body.toString()),
    options: { status: response.status, headers, body },
  };
}
const deliver = (route, response) => route.fulfill(response.options);

async function start(browser) {
  if (browser === "firefox")
    return firefox.launch(
      process.env.PLAYWRIGHT_BROWSERS_PATH
        ? {
            executablePath: path.join(
              process.env.PLAYWRIGHT_BROWSERS_PATH,
              "firefox-1555/firefox/firefox.exe",
            ),
          }
        : {},
    );
  assert.ok(["chrome", "msedge"].includes(browser));
  return chromium.launch({
    channel: browser,
    args: ["--enable-unsafe-swiftshader"],
  });
}

async function contextFor(browser, origin, options = {}) {
  const context = await browser.newContext({
    baseURL: origin,
    viewport: { width: 1440, height: 1000 },
    serviceWorkers: "block",
  });
  context.setDefaultTimeout(15000);
  // Потеря marker моделируется только на стороне конкретного потребителя.
  // Настоящие запись marker, rotation и status backend остаются без подмены.
  await context.addInitScript(
    ({ marker, noLocks, noChannel }) => {
      addEventListener("pageshow", (event) => {
        window.__ar01PageshowPersisted = event.persisted;
      });
      if (noChannel)
        Object.defineProperty(window, "BroadcastChannel", { value: undefined });
      if (noLocks)
        Object.defineProperty(navigator, "locks", { value: undefined });
      const read = Storage.prototype.getItem;
      Storage.prototype.getItem = function (key) {
        if (key === marker && window.__ar01LoseMarker)
          return window.__ar01FrozenMarker;
        return read.call(this, key);
      };
      addEventListener(
        "storage",
        (e) => {
          if (window.__ar01LoseMarker && (e.key === marker || e.key === null))
            e.stopImmediatePropagation();
        },
        true,
      );
    },
    { marker: MARKER, noLocks: options.noLocks, noChannel: options.noChannel },
  );
  return context;
}

async function loseMarker(page) {
  await page.evaluate((key) => {
    window.__ar01FrozenMarker = localStorage.getItem(key);
    window.__ar01LoseMarker = true;
  }, MARKER);
}
async function login(page, credentials, navigate = true) {
  if (navigate) await page.goto("/");
  await signedOut(page);
  await page.getByLabel("Электронная почта").fill(credentials.email);
  await page.getByLabel("Пароль", { exact: true }).fill(credentials.password);
  const reply = page.waitForResponse(
    (r) => at(r, "/auth/login") && r.status() === 200,
  );
  await page.getByTestId("login-submit").click();
  const auth = await (await reply).json();
  await signedIn(page);
  return auth;
}
async function logout(page) {
  const reply = page.waitForResponse(
    (r) => at(r, "/auth/logout") && r.status() === 200,
  );
  await page.getByTestId("logout-desktop").click();
  if (await page.getByTestId("navigation-leave").isVisible())
    await page.getByTestId("navigation-leave").click();
  const response = await reply;
  assert.equal(response.headers()["set-cookie"], undefined);
  await signedOut(page);
  return Date.now();
}
async function server(
  origin,
  endpoint,
  { token, sid, cookie, method = "POST" } = {},
) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (cookie) headers.Cookie = `geoservice_session=${cookie}`;
  return fetch(`${origin}/api/v1/${endpoint}`, {
    method,
    headers,
    ...(method !== "GET" && sid
      ? { body: JSON.stringify({ session_id: sid }) }
      : {}),
    signal: AbortSignal.timeout(10000),
  });
}
function trackStatus(page) {
  const pending = new Set();
  const result = { maxConcurrent: 0, requests: 0 };
  page.on("request", (request) => {
    if (!at(request, "/auth/session/status")) return;
    pending.add(request);
    result.requests++;
    result.maxConcurrent = Math.max(result.maxConcurrent, pending.size);
  });
  const finish = (request) => {
    pending.delete(request);
  };
  page.on("requestfinished", finish);
  page.on("requestfailed", finish);
  return result;
}
async function assertStorageSafe(context, credentials) {
  for (const page of context.pages()) {
    if (page.isClosed() || !page.url().startsWith("http")) continue;
    const safe = await page.evaluate(
      (password) =>
        Object.entries(localStorage).every(
          ([k, v]) =>
            !v.includes(password) &&
            !/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/.test(v) &&
            !/access_token|refresh_token|password/i.test(k),
        ),
      credentials.password,
    );
    assert.equal(safe, true);
  }
}
async function openWorkOrder(page) {
  await page
    .locator("button.workOrderButton")
    .filter({ hasText: "WO-001" })
    .click();
  const readback = page.waitForResponse(
    (r) => at(r, "/workspace") && r.status() === 200,
  );
  await page.getByTestId("workspace-open-action").click();
  const workspace = await (await readback).json();
  await expect(page.getByTestId("workspace-edit-commands")).toBeVisible();
  return workspace;
}

async function moveLine(page, workspace, dx = 12) {
  const feature = workspace.workOrder.editVersion.features.features.find(
    (f) => f.properties.assetCode === "L-003",
  );
  assert.ok(feature);
  const canvas = page.locator(".maplibregl-canvas");
  const mercator = (lng, lat) => [
    lng / 360 + 0.5,
    0.5 -
      Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) / (2 * Math.PI),
  ];
  await expect(async () => {
    const box = await canvas.boundingBox();
    const [w, s, e, n] = workspace.workOrder.scope.aoi.extent;
    const [left, bottom] = mercator(w, s),
      [right, top] = mercator(e, n);
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
  }).toPass({ timeout: 15000 });
  const box = await page
    .getByLabel("Переместить внутреннюю вершину линии")
    .boundingBox();
  const x = box.x + box.width / 2,
    y = box.y + box.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + dx, y + 8, { steps: 8 });
  await page.mouse.up();
  await expect(page.getByTestId("save-edit")).toBeEnabled();
}

export async function acceptance({
  browser: browserName,
  origin,
  output,
  email = process.env.AR01_EMAIL,
  password = process.env.AR01_PASSWORD,
  layerId = process.env.AR01_LAYER_ID,
  env = process.env,
}) {
  assert.ok(
    email && password && layerId,
    "Нужны credential/layer fixture в process env",
  );
  if (env.PLAYWRIGHT_BROWSERS_PATH)
    process.env.PLAYWRIGHT_BROWSERS_PATH = env.PLAYWRIGHT_BROWSERS_PATH;
  await mkdir(output, { recursive: true });
  const browser = await start(browserName);
  const credentials = { email, password };
  const result = {
    browser: browserName,
    version: browser.version(),
    executable:
      browserName === "firefox"
        ? path.join(
            process.env.PLAYWRIGHT_BROWSERS_PATH,
            "firefox-1555/firefox/firefox.exe",
          )
        : browserName === "chrome"
          ? "C:/Program Files/Google/Chrome/Application/chrome.exe (channel chrome)"
          : "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe (channel msedge)",
    distribution:
      browserName === "firefox"
        ? "Playwright patched Firefox (revision1555), не stock binary"
        : "installed branded channel",
    startedAt: new Date().toISOString(),
    cases: {},
  };
  async function scenario(name, action, options = {}) {
    if (
      process.env.AR01_CASE &&
      !process.env.AR01_CASE.split(",").some((part) => name.includes(part))
    )
      return;
    const context = await contextFor(browser, origin, options);
    const started = Date.now();
    try {
      const evidence = await withAcceptanceSignals((signals) =>
        action(context, signals),
      );
      await assertStorageSafe(context, credentials);
      result.cases[name] = {
        passed: true,
        durationMs: Date.now() - started,
        ...evidence,
      };
      console.log(`${browserName}: ${name} PASS`);
    } catch (error) {
      result.cases[name] = {
        passed: false,
        durationMs: Date.now() - started,
        failure:
          error.safeMessage ??
          "Assertion/timeout; детали без secrets доступны воспроизведением case",
        sourceFrame: error.stack
          ?.split("\n")
          .find((line) => /smoke\.mjs:\d/.test(line))
          ?.trim(),
      };
      console.error(`${browserName}: ${name} FAIL`);
      // Не печатаем Playwright call log, тела, headers или credentials.
    } finally {
      await context.close();
      await writeFile(
        path.join(output, "browser.json"),
        JSON.stringify(result, null, 2) + "\n",
      );
    }
  }
  const execute = async () => {
    await scenario(
      "parallel_restore_new_tab_close_initiator",
      async (context, signals) => {
        const a = await context.newPage(),
          b = await context.newPage();
        const initial = await login(a, credentials);
        await b.goto("/");
        await signedIn(b);
        const cookieBefore = (await sessionCookie(context)).value;
        const pendingRefresh = [a, b].map((page) =>
          page.waitForResponse(
            (r) => at(r, "/auth/session/refresh") && r.status() === 200,
          ),
        );
        await Promise.all([a.reload(), b.reload()]);
        const replies = await Promise.all(
          (await Promise.all(pendingRefresh)).map(
            async (response) => (await response.json()).session_id,
          ),
        );
        await Promise.all([signedIn(a), signedIn(b)]);
        if (
          replies.length < 2 ||
          !replies.every((sid) => sid === initial.session_id)
        ) {
          const error = new Error("parallel restore assertion");
          error.safeMessage = `realRotations=${replies.length}, sameSid=${replies.every((sid) => sid === initial.session_id)}`;
          throw error;
        }
        assert.notEqual((await sessionCookie(context)).value, cookieBefore);
        const entered = signals.signal(),
          release = signals.barrier();
        await a.route("**/auth/session/refresh", async (route) => {
          const response = await forward(route);
          entered.resolve();
          await release.promise;
          try {
            await deliver(route, response);
          } catch {}
        });
        await a.reload();
        await entered.wait();
        await a.close();
        release.resolve();
        const c = await context.newPage();
        await c.goto("/");
        // Закрытие инициатора после server rotation может потерять credential: допустим явный login.
        await expect(
          c.getByTestId("logout-desktop").or(c.getByTestId("login-submit")),
        ).toBeVisible();
        const restored = await c.getByTestId("logout-desktop").isVisible();
        if (!restored) await login(c, credentials, false);
        await logout(c);
        await signedOut(b);
        return {
          realRotations: replies.length,
          sameSid: true,
          newTab: true,
          closedInitiator: true,
          restoredAfterClose: restored,
          explicitLoginIfCredentialLost: !restored,
        };
      },
    );

    await scenario(
      "logout_revokes_copied_access_refresh_ticket_and_preserves_other_contexts",
      async (context, signals) => {
        const a = await context.newPage(),
          b = await context.newPage();
        const auth = await login(a, credentials);
        await b.goto("/");
        await signedIn(b);
        const cookie = await sessionCookie(context);
        assert.equal(
          Boolean(
            cookie.secure &&
            cookie.httpOnly &&
            cookie.sameSite === "Lax" &&
            cookie.path === "/api/v1/auth",
          ),
          true,
        );
        const survivor = await contextFor(browser, origin);
        const other = await survivor.newPage();
        const otherAuth = await login(other, credentials);
        const secondaryName = browserName === "msedge" ? "chrome" : "msedge";
        const secondary = await start(secondaryName),
          secondaryContext = await contextFor(secondary, origin);
        try {
          const otherBrowserPage = await secondaryContext.newPage();
          const independent = await login(otherBrowserPage, credentials);
          const ticketResponse = await server(
            origin,
            `ws/layers/${layerId}/ticket`,
            { token: auth.access_token },
          );
          assert.equal(ticketResponse.status, 200);
          const { ticket } = await ticketResponse.json();
          const committed = signals.signal();
          a.on("response", (r) => {
            if (at(r, "/auth/logout") && r.status() === 200)
              committed.resolve(Date.now());
          });
          const logoutDispatchStarted = Date.now();
          await a.getByTestId("logout-desktop").click();
          const commitObserved = await committed.wait();
          await Promise.all([signedOut(a), signedOut(b)]);
          const convergenceMs = Date.now() - commitObserved;
          const dispatchToLoginMs = Date.now() - logoutDispatchStarted;
          assert.ok(dispatchToLoginMs <= 5000);
          assert.equal((await sessionCookie(context)).value, cookie.value);
          const access = await server(origin, "auth/me", {
            token: auth.access_token,
            method: "GET",
          });
          const refresh = await server(origin, "auth/session/refresh", {
            cookie: cookie.value,
          });
          assert.equal(access.status, 401);
          assert.equal(refresh.status, 401);
          const ticketRejected = await a.evaluate(
            async ({ ticket, layerId }) => {
              const url = new URL(
                `/api/v1/ws/layers/${layerId}`,
                location.origin,
              );
              url.protocol = "ws:";
              url.searchParams.set("ticket", ticket);
              return new Promise((resolve, reject) => {
                const ws = new WebSocket(url);
                const timer = setTimeout(() => {
                  ws.close();
                  reject(new Error("ws timeout"));
                }, 5000);
                ws.onopen = () => {
                  clearTimeout(timer);
                  ws.close();
                  resolve(false);
                };
                ws.onerror = () => {};
                ws.onclose = () => {
                  clearTimeout(timer);
                  resolve(true);
                };
              });
            },
            { ticket, layerId },
          );
          assert.equal(ticketRejected, true);
          assert.equal(
            (
              await server(origin, "auth/me", {
                token: otherAuth.access_token,
                method: "GET",
              })
            ).status,
            200,
          );
          assert.equal(
            (
              await server(origin, "auth/me", {
                token: independent.access_token,
                method: "GET",
              })
            ).status,
            200,
          );
          await signedIn(other);
          await signedIn(otherBrowserPage);
          return {
            convergenceMs,
            dispatchToLoginMs,
            accessStatus: access.status,
            refreshStatus: refresh.status,
            ticketRejected,
            cookieUnchanged: true,
            independentContext: true,
            independentBrowser: secondaryName,
            secondaryVersion: secondary.version(),
          };
        } finally {
          await survivor.close();
          await secondary.close();
        }
      },
    );

    await scenario(
      "lost_marker_old_active_status_polling_sla",
      async (context, signals) => {
        const a = await context.newPage(),
          b = await context.newPage();
        await login(a, credentials);
        await b.goto("/");
        await signedIn(b);
        await loseMarker(b);
        const status = trackStatus(b),
          entered = signals.signal(),
          release = signals.barrier();
        let held = false;
        await b.route("**/auth/session/status", async (route) => {
          const response = await forward(route);
          if (!held) {
            held = true;
            assert.equal((await response.json()).state, "active");
            entered.resolve();
            await release.promise;
          }
          await deliver(route, response);
        });
        await entered.wait();
        const observed = signals.signal();
        a.on("response", (r) => {
          if (at(r, "/auth/logout") && r.status() === 200)
            observed.resolve(Date.now());
        });
        const logoutDispatchStarted = Date.now();
        await a.getByTestId("logout-desktop").click();
        const commit = await observed.wait();
        await sleep(1100);
        release.resolve();
        await signedOut(b);
        const convergenceMs = Date.now() - commit;
        const dispatchToLoginMs = Date.now() - logoutDispatchStarted;
        assert.ok(dispatchToLoginMs <= 5000);
        assert.equal(status.maxConcurrent, 1);
        return {
          convergenceMs,
          dispatchToLoginMs,
          oldActiveDelayedMs: 1100,
          markerLost: true,
          broadcastUnavailable: true,
          ...status,
        };
      },
      { noChannel: true },
    );

    await scenario(
      "resume_requires_post_resume_status_before_protected_action",
      async (context, signals) => {
        const a = await context.newPage();
        const auth = await login(a, credentials);
        await loseMarker(a);
        const entered = signals.signal(),
          release = signals.barrier();
        let held = false,
          protectedRequests = 0,
          statusAfterResume = 0,
          resumed = false;
        const stats = trackStatus(a);
        await a.route("**/auth/session/status", async (route) => {
          if (resumed) statusAfterResume++;
          const response = await forward(route);
          if (!held) {
            held = true;
            assert.equal((await response.json()).state, "active");
            entered.resolve();
            await release.promise;
          }
          await deliver(route, response);
        });
        await entered.wait();
        a.on("request", (r) => {
          if (at(r, "/work-orders/assigned-to-me")) protectedRequests++;
        });
        resumed = true;
        await a.evaluate(() =>
          dispatchEvent(
            new PageTransitionEvent("pageshow", { persisted: true }),
          ),
        );
        await a.getByTestId("refresh-work-orders").click();
        assert.equal(protectedRequests, 0);
        assert.equal(
          (
            await server(origin, "auth/logout", {
              token: auth.access_token,
              sid: auth.session_id,
            })
          ).status,
          200,
        );
        release.resolve();
        await signedOut(a);
        assert.ok(statusAfterResume >= 1);
        assert.equal(protectedRequests, 0);
        assert.equal(stats.maxConcurrent, 1);
        return {
          freshStatusAfterResume: true,
          lifecycleSignal: "pageshow persisted injected into real document",
          protectedRequests,
          statusAfterResume,
          ...stats,
        };
      },
      { noChannel: true },
    );

    await scenario(
      "real_history_resume_after_remote_logout",
      async (context) => {
        const a = await context.newPage(),
          b = await context.newPage();
        await login(a, credentials);
        await b.goto("/");
        await signedIn(b);
        await b.goto("about:blank");
        await logout(a);
        let protectedRequests = 0;
        b.on("request", (r) => {
          if (at(r, "/work-orders/assigned-to-me")) protectedRequests++;
        });
        await b.goBack();
        await signedOut(b);
        assert.equal(protectedRequests, 0);
        return {
          historyResume: true,
          bfcacheRestored: await b.evaluate(
            () => window.__ar01PageshowPersisted === true,
          ),
          protectedRequests,
        };
      },
    );

    await scenario(
      "undelivered_logout_preserves_workspace",
      async (context) => {
        const page = await context.newPage();
        const auth = await login(page, credentials);
        await openWorkOrder(page);
        let calls = 0;
        await page.route("**/auth/logout", async (route) => {
          calls++;
          await route.abort("internetdisconnected");
        });
        await page.getByTestId("logout-desktop").click();
        await expect(
          page.getByText("Не удалось подтвердить выход", { exact: true }),
        ).toBeVisible();
        await signedIn(page);
        await expect(page.getByTestId("workspace-edit-commands")).toBeVisible();
        assert.equal(calls, 1);
        assert.equal(
          (
            await server(origin, "auth/me", {
              token: auth.access_token,
              method: "GET",
            })
          ).status,
          200,
        );
        return {
          logoutRequests: calls,
          serverNotReached: true,
          sessionRetained: true,
          workspaceRetained: true,
          message: "Не удалось подтвердить выход (network outcome)",
        };
      },
    );

    await scenario(
      "committed_logout_response_lost_reconciles_without_retry",
      async (context) => {
        const page = await context.newPage();
        await login(page, credentials);
        let calls = 0,
          committed = false;
        await page.route("**/auth/logout", async (route) => {
          calls++;
          const response = await forward(route);
          assert.equal(response.status(), 200);
          committed = true;
          await route.abort("failed");
        });
        await page.getByTestId("logout-desktop").click();
        await signedOut(page);
        await sleep(1100);
        assert.equal(calls, 1);
        return { committed, reconciled: true, logoutRequests: calls };
      },
    );

    await scenario(
      "auth_lock_timeout_known_undelivered_logout",
      async (context) => {
        const page = await context.newPage(),
          holder = await context.newPage();
        await login(page, credentials);
        await holder.goto("/");
        await signedIn(holder);
        await holder.evaluate(() => {
          window.__ar01LockEntered = false;
          window.__ar01LockPromise = navigator.locks.request(
            "geoservice.auth.cookie.v1",
            () => {
              window.__ar01LockEntered = true;
              return new Promise((resolve) => {
                window.__ar01ReleaseLock = resolve;
              });
            },
          );
        });
        await holder.waitForFunction(() => window.__ar01LockEntered);
        let calls = 0;
        page.on("request", (r) => {
          if (at(r, "/auth/logout")) calls++;
        });
        const start = Date.now();
        await page.getByTestId("logout-desktop").click();
        try {
          await expect(
            page.getByText("Не удалось выйти, попробуйте ещё раз", {
              exact: true,
            }),
          ).toBeVisible({ timeout: 33000 });
          await signedIn(page);
          assert.equal(calls, 0);
          return {
            logoutRequests: calls,
            lockWaitMs: Date.now() - start,
            sessionRetained: true,
            knownUndelivered: true,
          };
        } catch (error) {
          const uncertain = await page
            .getByText("Не удалось подтвердить выход", { exact: true })
            .isVisible();
          error.safeMessage = `known-undelivered lock timeout: requests=${calls}, uncertainMessage=${uncertain}, authRetained=${await page.getByTestId("logout-desktop").isVisible()}`;
          throw error;
        } finally {
          await holder.evaluate(() => window.__ar01ReleaseLock());
        }
      },
    );

    await scenario(
      "late_old_logout_after_new_login_does_not_touch_new_cookie",
      async (context) => {
        const page = await context.newPage();
        const old = await login(page, credentials);
        const oldCookie = await sessionCookie(context);
        await logout(page);
        const newer = await login(page, credentials, false);
        const newCookie = await sessionCookie(context);
        const late = await server(origin, "auth/logout", {
          token: old.access_token,
          sid: old.session_id,
          cookie: oldCookie.value,
        });
        assert.equal(late.status, 200);
        assert.equal(late.headers.get("set-cookie"), null);
        assert.equal((await sessionCookie(context)).value, newCookie.value);
        await signedIn(page);
        assert.equal(
          (
            await server(origin, "auth/me", {
              token: newer.access_token,
              method: "GET",
            })
          ).status,
          200,
        );
        await page.reload();
        await signedIn(page);
        return {
          lateLogoutStatus: 200,
          newSidDifferent: old.session_id !== newer.session_id,
          cookieUnchanged: true,
          newSessionRestores: true,
        };
      },
    );

    await scenario(
      "lost_rotated_response_requires_explicit_login",
      async (context) => {
        const page = await context.newPage();
        await login(page, credentials);
        let lost = false;
        await page.route("**/auth/session/refresh", async (route) => {
          const response = await forward(route);
          assert.equal(response.status(), 200);
          lost = true;
          await route.abort("failed");
        });
        await page.reload();
        await expect(
          page.getByText("Не удалось восстановить сессию", { exact: true }),
        ).toBeVisible();
        await page.unroute("**/auth/session/refresh");
        await page
          .getByRole("button", { name: "Повторить", exact: true })
          .click();
        await signedOut(page);
        await login(page, credentials, false);
        assert.equal(lost, true);
        return {
          serverRotated: true,
          responseLost: true,
          replayRejected: true,
          explicitLoginRecovered: true,
        };
      },
    );

    await scenario(
      "fe01_retry_waits_and_late_refresh_cookie_never_installs_other_sid",
      async (context, signals) => {
        const page = await context.newPage();
        await login(page, credentials);
        await page.route("**/auth/session/refresh", (route) =>
          route.abort("failed"),
        );
        await page.reload();
        await expect(
          page.getByText("Не удалось восстановить сессию", { exact: true }),
        ).toBeVisible();
        await page.unroute("**/auth/session/refresh");
        const entered = signals.signal(),
          release = signals.barrier();
        await page.route("**/auth/session/refresh", async (route) => {
          const response = await forward(route);
          entered.resolve();
          await release.promise;
          await deliver(route, response);
        });
        await page
          .getByRole("button", { name: "Повторить", exact: true })
          .click();
        await entered.wait();
        await expect(
          page.getByText("Восстановление сессии", { exact: true }),
        ).toBeVisible();
        await expect(page.getByTestId("login-submit")).toHaveCount(0);
        release.resolve();
        await signedIn(page);
        await page.unroute("**/auth/session/refresh");
        // Браузерный fetch уже допущен до нового login; поздний настоящий Set-Cookie
        // может заменить cookie. Приложение не должно принять revoked sid/другого actor.
        const pending = signals.signal(),
          late = signals.barrier();
        await page.route("**/auth/session/refresh", async (route) => {
          const response = await forward(route);
          assert.equal(response.status(), 200);
          pending.resolve();
          await late.promise;
          await deliver(route, response);
        });
        const fetchPending = page.evaluate(async () => {
          const r = await fetch("/api/v1/auth/session/refresh", {
            method: "POST",
            credentials: "include",
          });
          return r.status;
        });
        await pending.wait();
        await logout(page);
        const newer = await login(page, credentials, false);
        const currentCookie = (await sessionCookie(context)).value;
        late.resolve();
        assert.equal(await fetchPending, 200);
        const overwritten =
          (await sessionCookie(context)).value !== currentCookie;
        await signedIn(page);
        assert.equal(
          (
            await server(origin, "auth/me", {
              token: newer.access_token,
              method: "GET",
            })
          ).status,
          200,
        );
        await page.unroute("**/auth/session/refresh");
        await page.reload();
        await signedOut(page);
        await login(page, credentials, false);
        return {
          retryWaitScreen: true,
          lateRealSetCookie: true,
          cookieOverwritten: overwritten,
          newAccessStayedValid: true,
          revokedRefreshNeverInstalled: true,
          explicitLoginRecovered: true,
        };
      },
    );

    await scenario(
      "web_locks_unavailable_blocks_uncoordinated_refresh",
      async (context) => {
        let calls = 0;
        const page = await context.newPage();
        page.on("request", (r) => {
          if (at(r, "/auth/session/refresh")) calls++;
        });
        await page.goto("/");
        await expect(
          page.getByText("Не удалось восстановить сессию", { exact: true }),
        ).toBeVisible();
        assert.equal(calls, 0);
        return { refreshRequests: calls, explicitError: true };
      },
      { noLocks: true },
    );

    await scenario(
      "same_workorder_two_tabs_stale_guard_without_lock",
      async (context) => {
        const a = await context.newPage(),
          b = await context.newPage();
        await login(a, credentials);
        await b.goto("/");
        await signedIn(b);
        const [wa, wb] = await Promise.all([
          openWorkOrder(a),
          openWorkOrder(b),
        ]);
        await moveLine(a, wa, 12);
        await moveLine(b, wb, -12);
        const saved = a.waitForResponse(
          (r) => at(r, "/workspace") && r.status() === 200,
        );
        await a.getByTestId("save-edit").click();
        await saved;
        const stale = b.waitForResponse(
          (r) => r.request().method() === "PUT" && r.status() === 409,
        );
        await b.getByTestId("save-edit").click();
        const response = await stale;
        const body = await response.json();
        assert.equal(body.code, "DRAFT_VERSION_STALE");
        await expect(b.getByTestId("save-edit")).toBeDisabled();
        // Возвращаем fixture в baseline существующим Revert, без SQL обхода.
        await a.getByTestId("revert-edit").click();
        const reverted = a.waitForResponse(
          (r) => at(r, "/workspace") && r.status() === 200,
        );
        await a.getByTestId("revert-proceed").click();
        await reverted;
        return {
          sameWorkOrderOpenedTwice: true,
          independentDrafts: true,
          staleStatus: response.status(),
          staleCode: body.code,
          newWorkOrderLock: false,
        };
      },
    );
  };
  await recordAcceptanceResult(result, execute, {
    scope: process.env.AR01_CASE ?? "all",
    close: () => browser.close(),
    persist: (value) =>
      writeFile(
        path.join(output, "browser.json"),
        JSON.stringify(value, null, 2) + "\n",
      ),
  });
  if (!result.passed) {
    const error = new Error("browser acceptance failed");
    error.safeMessage = `${browserName}: failed cases: ${Object.entries(
      result.cases,
    )
      .filter(([, v]) => !v.passed)
      .map(([k]) => k)
      .join(", ")}`;
    throw error;
  }
  return result;
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  const args = {};
  for (let i = 2; i < process.argv.length; i += 2)
    args[process.argv[i].replace(/^--/, "")] = process.argv[i + 1];
  try {
    await acceptance(args);
  } catch (error) {
    console.error(
      error.safeMessage ??
        "Ошибка browser runner; credentials и raw output не выводятся",
    );
    process.exitCode = 1;
  }
}
