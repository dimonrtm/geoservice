// Изолированная проверка frontend; auth API подменён явными тестовыми ответами.
import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { randomUUID } from "node:crypto";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { promisify } from "node:util";

const repoRoot = fileURLToPath(new URL("../../../", import.meta.url));
const frontendRoot = path.join(repoRoot, "apps/frontend");
const frontendRequire = createRequire(path.join(frontendRoot, "package.json"));
const { JSDOM } = frontendRequire("jsdom");
const { chromium, expect } = createRequire(
  path.join(repoRoot, "infra/m4/package.json"),
)("@playwright/test");
const run = promisify(execFile);
const project = `geoservice-fe04-${randomUUID().slice(0, 8)}`;
const scratch = await mkdtemp(path.join(os.tmpdir(), `${project}-`));
const evidence = path.join(repoRoot, "docs/sprint_2/evidence/fe-04", project);
await mkdir(evidence, { recursive: true });
const envFile = path.join(scratch, "compose.env");
await writeFile(
  envFile,
  [
    "DB_NAME=fe04_unused",
    "DB_USER=fe04_unused",
    "DB_PASSWORD=fe04_unused",
    "DATABASE_URL=postgresql+asyncpg://unused:unused@localhost/unused",
    "JWT_SECRET=fe04-public-unused-fixture",
  ].join("\n") + "\n",
);
const composeArgs = [
  "compose",
  "--env-file",
  envFile,
  "-f",
  "infra/docker-compose.yml",
  "--profile",
  "prod",
  "-p",
  project,
];
const imageName = `${project}-frontend-prod`;
const results = {
  project,
  backend: "mocked-auth-only",
  production: [],
  dev: [],
};

async function docker(args, environment = process.env) {
  return run("docker", args, {
    cwd: repoRoot,
    env: environment,
    maxBuffer: 16 * 1024 * 1024,
  });
}

function checkHtml(html, expectedName) {
  const dom = new JSDOM(html);
  try {
    assert.equal(dom.window.document.documentElement.lang, "ru");
    assert.equal(dom.window.document.querySelectorAll("title").length, 1);
    assert.equal(
      dom.window.document.querySelector("title").textContent,
      expectedName,
    );
    assert.equal(dom.window.document.querySelector("#injected"), null);
  } finally {
    dom.window.close();
  }
}

async function checkBrowser(origin, expectedName, screenshotPath) {
  const browser = await chromium.launch({ channel: "msedge" });
  try {
    const page = await browser.newPage({
      viewport: { width: 600, height: 900 },
    });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    let signedIn = false;
    const credentials = {
      access_token: "fe04-fixture-token",
      token_type: "bearer",
      session_id: "fe04-fixture-session",
      user: {
        id: "fe04-reviewer",
        email: "reviewer@example.local",
        role: "reviewer",
      },
    };
    await page.route("**/api/v1/**", async (route) => {
      const pathname = new URL(route.request().url()).pathname;
      if (pathname.endsWith("/auth/login")) {
        signedIn = true;
        await route.fulfill({ json: credentials });
      } else if (pathname.endsWith("/auth/logout")) {
        signedIn = false;
        await route.fulfill({
          json: { ok: true, session_id: credentials.session_id },
        });
      } else if (pathname.endsWith("/auth/session/status")) {
        await route.fulfill({
          json: {
            session_id: credentials.session_id,
            state: signedIn ? "active" : "ended",
          },
        });
      } else if (pathname.endsWith("/auth/session/refresh")) {
        await route.fulfill(
          signedIn
            ? { json: credentials }
            : {
                status: 401,
                json: {
                  code: "AUTH_REQUIRED",
                  message: "Нужен вход",
                  correlationId: "fe04",
                },
              },
        );
      } else {
        errors.push(`Неожиданный fixture-запрос: ${pathname}`);
        await route.fulfill({ status: 404, json: {} });
      }
    });
    await page.goto(origin);
    await expect(page.locator('[data-test="login-submit"]')).toBeVisible();
    await expect(page.locator(".eyebrow")).toHaveText(expectedName);
    assert.equal(await page.title(), expectedName);
    assert.equal(await page.locator("html").getAttribute("lang"), "ru");
    await page.getByLabel("Электронная почта").fill("reviewer@example.local");
    await page.getByLabel("Пароль", { exact: true }).fill("fixture-only");
    await page.locator('[data-test="login-submit"]').click();
    await expect(
      page.getByRole("heading", { name: "Проверка изменений" }),
    ).toBeVisible();
    const logout = page.locator('[data-test="logout-mobile"]');
    await logout.focus();
    await expect(page.getByRole("tooltip")).toHaveText(
      `Выйти из ${expectedName}`,
    );
    assert.equal(await page.title(), expectedName);
    if (screenshotPath) await page.screenshot({ path: screenshotPath });
    await logout.click();
    await expect(page.locator('[data-test="login-submit"]')).toBeVisible();
    await expect(page.locator(".eyebrow")).toHaveText(expectedName);
    assert.equal(await page.title(), expectedName);
    assert.equal(await page.locator("#injected").count(), 0);
    assert.deepEqual(errors, []);
  } finally {
    await browser.close();
  }
}

async function serveBuild(directory) {
  const mime = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
  };
  const server = createServer(async (request, response) => {
    const pathname = new URL(request.url, "http://localhost").pathname;
    const file = path.resolve(
      directory,
      `.${pathname === "/" ? "/index.html" : pathname}`,
    );
    if (!file.startsWith(directory + path.sep)) {
      response.writeHead(403).end();
      return;
    }
    try {
      const bytes = await readFile(file);
      response
        .writeHead(200, {
          "Content-Type":
            mime[path.extname(file)] ?? "application/octet-stream",
        })
        .end(bytes);
    } catch {
      response.writeHead(404).end();
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  return { server, origin: `http://127.0.0.1:${server.address().port}` };
}

try {
  for (const [index, configuredName] of [
    undefined,
    "  Сети Уфы  ",
    'Сети & "Уфа" </title><div id="injected"> %MODE%',
  ].entries()) {
    const environment = { ...process.env };
    delete environment.VITE_APP_NAME;
    if (configuredName !== undefined)
      environment.VITE_APP_NAME = configuredName;
    const expectedName = configuredName?.trim() || "GeoService";
    const config = JSON.parse(
      (
        await docker(
          [...composeArgs, "config", "--format", "json"],
          environment,
        )
      ).stdout,
    );
    assert.equal(
      config.services["frontend-prod"].build.args.VITE_APP_NAME,
      configuredName ?? "GeoService",
    );
    const demoConfig = JSON.parse(
      (
        await docker(
          [
            "compose",
            "--env-file",
            envFile,
            "-f",
            "infra/docker-compose.yml",
            "-f",
            "infra/docker-compose.demo.yml",
            "--profile",
            "dev",
            "-p",
            project,
            "config",
            "--format",
            "json",
          ],
          environment,
        )
      ).stdout,
    );
    assert.equal(
      demoConfig.services["frontend-dev"].environment.VITE_APP_NAME,
      configuredName ?? "GeoService",
    );
    console.log(
      `Production ${index + 1}/3: сборка и проверка ${JSON.stringify(expectedName)}`,
    );
    const buildLog = await docker(
      [...composeArgs, "build", "frontend-prod"],
      environment,
    );
    await writeFile(
      path.join(scratch, `build-${index}.log`),
      buildLog.stdout + buildLog.stderr,
    );
    const containerId = (
      await docker(["create", "--network", "none", imageName])
    ).stdout.trim();
    const directory = path.join(scratch, `dist-${index}`);
    await mkdir(directory);
    try {
      await docker(["cp", `${containerId}:/usr/share/nginx/html/.`, directory]);
    } finally {
      await docker(["rm", containerId]);
    }
    const { server, origin } = await serveBuild(directory);
    try {
      const html = await (await fetch(origin)).text();
      checkHtml(html, expectedName);
      await checkBrowser(
        origin,
        expectedName,
        path.join(evidence, `production-${index}.png`),
      );
      results.production.push({
        configuredName: configuredName ?? null,
        expectedName,
        html: true,
        browser: true,
        compose: true,
      });
    } finally {
      await new Promise((resolve) => server.close(resolve));
    }
  }
  const { createServer: createViteServer } = await import(
    pathToFileURL(
      path.join(frontendRoot, "node_modules/vite/dist/node/index.js"),
    )
  );
  for (const configuredName of ["   ", "  Дев-сети Уфы  "]) {
    process.env.VITE_APP_NAME = configuredName;
    const server = await createViteServer({
      root: frontendRoot,
      server: { host: "127.0.0.1", port: 0 },
    });
    try {
      await server.listen();
      const origin = `http://127.0.0.1:${server.httpServer.address().port}`;
      const expectedName = configuredName.trim() || "GeoService";
      checkHtml(await (await fetch(origin)).text(), expectedName);
      await checkBrowser(origin, expectedName);
      results.dev.push({
        configuredName,
        expectedName,
        html: true,
        browser: true,
      });
    } finally {
      await server.close();
    }
  }
  results.screenReader = "not-run";
  await writeFile(
    path.join(evidence, "verification.json"),
    JSON.stringify(results, null, 2) + "\n",
  );
  console.log(JSON.stringify(results, null, 2));
} finally {
  await docker(["image", "rm", imageName]).catch(() => {});
  console.log(`Временные логи: ${scratch}`);
}
