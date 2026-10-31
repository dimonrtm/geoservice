// Одноразовая production-среда AR-01: tmpfs DB, loopback, отдельный Compose project.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createHash, randomBytes, randomUUID } from "node:crypto";
import {
  cp,
  mkdir,
  mkdtemp,
  readFile,
  realpath,
  rm,
  writeFile,
} from "node:fs/promises";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { acceptance } from "./smoke.mjs";
import { failedAcceptanceResult } from "./acceptanceResult.mjs";

const repo = fileURLToPath(new URL("../../../", import.meta.url));
const project = `geoservice-ar01-${randomUUID().slice(0, 8)}`;
const evidence = path.join(repo, "docs/sprint_2/evidence/ar-01", project);
const temp = await mkdtemp(path.join(tmpdir(), "geoservice-ar01-"));
const configPath = path.join(temp, "compose.json");
const emptyEnv = path.join(temp, "empty.env");
const env = {
  ...process.env,
  AR01_PASSWORD: randomBytes(24).toString("hex"),
  AR01_DB_PASSWORD: randomBytes(24).toString("hex"),
  AR01_JWT_SECRET: randomBytes(48).toString("hex"),
  AR01_EMAIL: "ar01.editor@example.local",
  PLAYWRIGHT_BROWSERS_PATH: path.join(repo, ".tmp-tests/ar01-browsers"),
};
env.AR01_DATABASE_URL = `postgresql+asyncpg://postgres:${env.AR01_DB_PASSWORD}@postgis:5432/ar01`;
delete env.COMPOSE_FILE;
delete env.COMPOSE_PROFILES;
const manifest = {
  project,
  startedAt: new Date().toISOString(),
  status: "running",
  browsers: {},
};
manifest.runnerHashes = Object.fromEntries(
  await Promise.all(
    ["run.mjs", "smoke.mjs", "acceptanceResult.mjs"].map(async (name) => [
      name,
      createHash("sha256")
        .update(await readFile(new URL(name, import.meta.url)))
        .digest("hex"),
    ]),
  ),
);
await mkdir(evidence, { recursive: true });
await writeFile(emptyEnv, "");
function run(command, args, timeout = 180000) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: repo, env, windowsHide: true });
    let output = "";
    child.stdout.on("data", (d) => {
      output += d;
    });
    child.stderr.on("data", (d) => {
      output += d;
    });
    const timer = setTimeout(() => child.kill(), timeout);
    child.on("error", (e) => {
      clearTimeout(timer);
      reject(e);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      // Потенциально чувствительный Docker/SQL output не переносится в error/evidence.
      if (code === 0) resolve(output.trim());
      else {
        const error = new Error(`${command}: exit ${code}`);
        error.safeMessage = `${command} ${args.includes("build") ? "build" : args.includes("pytest") ? "pytest" : args[0]}: exit ${code}`;
        // Только диагностические строки без request/SQL/body и известных secrets.
        for (const line of output
          .split("\n")
          .filter((line) =>
            /error TS|ERROR \[|failed to solve|Cannot find|not found|FAILED|ERROR collecting|passed.*skipped|INTERNALERROR> (E|.*Error:)/.test(
              line,
            ),
          )) {
          let safe = line;
          for (const value of [
            env.AR01_PASSWORD,
            env.AR01_DB_PASSWORD,
            env.AR01_JWT_SECRET,
            env.AR01_DATABASE_URL,
          ])
            safe = safe.replaceAll(value, "[скрыто]");
          console.error(safe.slice(0, 300));
        }
        reject(error);
      }
    });
  });
}
const compose = (...args) =>
  run(
    "docker",
    [
      "compose",
      "--env-file",
      emptyEnv,
      "-p",
      project,
      "-f",
      configPath,
      ...args,
    ],
    args[0] === "build" ? 600000 : 180000,
  );
const sql = (query) =>
  compose(
    "exec",
    "-T",
    "postgis",
    "psql",
    "-U",
    "postgres",
    "-d",
    "ar01",
    "-At",
    "-v",
    "ON_ERROR_STOP=1",
    "-c",
    query,
  );
let configured = false;
try {
  console.log(`${project}: изолированный tmpfs production harness`);
  const excluded =
    /^(\.env(?:\..*)?|node_modules|dist|build|\.git|\.venv|venv|__pycache__|\.pytest_cache|\.ruff_cache|\.mypy_cache|htmlcov|.*\.py[co])$/;
  const frontend = path.join(temp, "frontend");
  await cp(path.join(repo, "apps/frontend"), frontend, {
    recursive: true,
    filter: (p) => !excluded.test(path.basename(p)),
  });
  const probe = createServer();
  await new Promise((yes, no) => {
    probe.once("error", no);
    probe.listen(0, "127.0.0.1", yes);
  });
  const port = probe.address().port;
  await new Promise((yes, no) => probe.close((e) => (e ? no(e) : yes())));
  const config = {
    services: {
      postgis: {
        image: "postgis/postgis:16-3.4",
        environment: {
          POSTGRES_DB: "ar01",
          POSTGRES_USER: "postgres",
          POSTGRES_PASSWORD: "${AR01_DB_PASSWORD}",
        },
        tmpfs: ["/var/lib/postgresql/data"],
        volumes: [
          `${path.join(repo, "infra/docker/postgis/init").replaceAll("\\", "/")}:/docker-entrypoint-initdb.d:ro`,
        ],
        healthcheck: {
          test: ["CMD-SHELL", "pg_isready -U postgres -d ar01"],
          interval: "2s",
          timeout: "3s",
          retries: 30,
        },
      },
      utility_service: {
        image: "geoservice-ar01-backend-prod",
        environment: {
          DATABASE_URL: "${AR01_DATABASE_URL}",
          DEV_MODE: "false",
          AUTH_SESSION_COOKIE_SECURE: "true",
          JWT_SECRET: "${AR01_JWT_SECRET}",
          LEGACY_GIS_API_ENABLED: "true",
          UTILITY_GEOMETRY_XY_RESOLUTION: "0.0000001",
          UTILITY_GEOMETRY_ROUNDING_MODE: "ROUND_HALF_AWAY_FROM_ZERO",
          HOST: "0.0.0.0",
          PORT: "8000",
        },
        command: ["bash", "-lc", "bash scripts/start_api.sh"],
        depends_on: { postgis: { condition: "service_healthy" } },
        healthcheck: {
          test: [
            "CMD-SHELL",
            "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)\"",
          ],
          interval: "2s",
          timeout: "3s",
          retries: 30,
        },
      },
      frontend: {
        build: { context: frontend, target: "prod" },
        ports: [`127.0.0.1:${port}:80`],
        depends_on: { utility_service: { condition: "service_healthy" } },
      },
    },
  };
  await writeFile(configPath, JSON.stringify(config, null, 2) + "\n");
  configured = true;
  manifest.docker = await run("docker", [
    "version",
    "--format",
    "{{.Server.Version}}",
  ]);
  manifest.compose = await run("docker", ["compose", "version", "--short"]);
  manifest.backendImage = await run("docker", [
    "image",
    "inspect",
    "geoservice-ar01-backend-prod",
    "--format",
    "{{.Id}}",
  ]);
  console.log(
    "Сборка чистого frontend context; backend использует проверенный production image...",
  );
  await compose("build", "frontend");
  await compose("up", "-d", "--wait", "postgis");
  await compose(
    "run",
    "--rm",
    "--no-deps",
    "utility_service",
    "bash",
    "-lc",
    "set -euo pipefail; alembic upgrade head; python -m seeds.runners.seed_demo_users; python -m seeds.runners.seed_utility_dataset; python -m seeds.runners.seed_work_orders; python -m seeds.runners.upgrade_demo_fixture",
  );
  // Сохраняем назначение WO-001, заменяем только fixture credential на случайный в памяти.
  await compose(
    "run",
    "--rm",
    "--no-deps",
    "-e",
    "AR01_PASSWORD",
    "-e",
    "AR01_EMAIL",
    "utility_service",
    "python",
    "-c",
    `import asyncio, os
from sqlalchemy import update
from utility_service.infrastructure.postgresql.models.user import User
from utility_service.infrastructure.postgresql.session import SessionFactory
from utility_service.utils.passwords import hash_password
async def main():
 async with SessionFactory() as s, s.begin():
  await s.execute(update(User).where(User.email == 'alexey.editor@example.local').values(email=os.environ['AR01_EMAIL'], password_hash=hash_password(os.environ['AR01_PASSWORD'])))
asyncio.run(main())`,
  );
  const layerId = randomUUID();
  await sql(
    `INSERT INTO layers (id, name, title, geometry_type, srid, storage_table) VALUES ('${layerId}', 'ar01', 'AR-01', 'Point', 4326, 'feature_points')`,
  );
  await compose("up", "-d", "--wait", "utility_service", "frontend");
  const databaseId = await compose("ps", "-q", "postgis");
  const tmpfsMounts = JSON.parse(
    await run("docker", [
      "inspect",
      "--format",
      "{{json .HostConfig.Tmpfs}}",
      databaseId,
    ]),
  );
  assert.ok(Object.hasOwn(tmpfsMounts, "/var/lib/postgresql/data"));
  const origin = `http://localhost:${port}`;
  manifest.origin = origin;
  // Тестовый schema lane отдельно от application DB; корневые full suites не повторяем.
  await sql("CREATE DATABASE ar01_targeted_test");
  await compose(
    "exec",
    "-T",
    "postgis",
    "psql",
    "-U",
    "postgres",
    "-d",
    "ar01_targeted_test",
    "-v",
    "ON_ERROR_STOP=1",
    "-c",
    "CREATE EXTENSION IF NOT EXISTS postgis",
  );
  const targeted = await run("docker", [
    "run",
    "--rm",
    "--network",
    `${project}_default`,
    "-v",
    `${path.join(repo, "apps/backend")}:/app`,
    "-e",
    "RUN_DB_TESTS=1",
    "-e",
    `TEST_DATABASE_URL=postgresql+asyncpg://postgres:${env.AR01_DB_PASSWORD}@postgis:5432/ar01_targeted_test`,
    "geoservice-db-tests-backend_db_tests",
    "python",
    "-m",
    "pytest",
    "tests/integration_tests/test_browser_auth_session_repository.py",
    "tests/integration_tests/test_browser_auth_session_races.py",
    "--tb=short",
  ]);
  manifest.targetedDB = targeted
    .split("\n")
    .filter((line) => /passed|skipped|warning/.test(line))
    .map((line) => line.trim());
  for (const browser of process.argv.slice(2).length
    ? process.argv.slice(2)
    : ["chrome", "msedge", "firefox"]) {
    console.log(`${browser}: настоящие browser flows на ${origin}`);
    try {
      manifest.browsers[browser] = await acceptance({
        browser,
        origin,
        output: path.join(evidence, browser),
        email: env.AR01_EMAIL,
        password: env.AR01_PASSWORD,
        layerId,
        env,
      });
    } catch (error) {
      try {
        manifest.browsers[browser] = failedAcceptanceResult(
          JSON.parse(
            await readFile(
              path.join(evidence, browser, "browser.json"),
              "utf8",
            ),
          ),
        );
      } catch {
        manifest.browsers[browser] = failedAcceptanceResult({
          passed: false,
          error: "Браузер не запущен; gate не закрыт",
        });
      }
      console.error(error.safeMessage ?? `${browser}: launch failed`);
    }
  }
  manifest.sql = JSON.parse(
    await sql(
      `SELECT json_build_object('parents', count(*), 'revoked', count(*) FILTER (WHERE revoked_at IS NOT NULL)) FROM "user".browser_auth_sessions`,
    ),
  );
  manifest.tmpfs = true;
  manifest.demoVolumesUsed = false;
  manifest.status = Object.values(manifest.browsers).every((b) => b.passed)
    ? "passed"
    : "failed";
  if (manifest.status !== "passed") process.exitCode = 1;
} catch (error) {
  manifest.status = "failed";
  manifest.error =
    error.safeMessage ??
    `Ошибка harness (${error.code ?? error.name}); чувствительный output не сохранён`;
  console.error(manifest.error);
  process.exitCode = 1;
} finally {
  try {
    if (configured) {
      for (const id of (await compose("ps", "-aq"))
        .split(/\s+/)
        .filter(Boolean))
        assert.equal(
          await run("docker", [
            "inspect",
            "--format",
            '{{index .Config.Labels "com.docker.compose.project"}}',
            id,
          ]),
          project,
        );
      await compose("down", "--volumes", "--remove-orphans", "--timeout", "10");
      for (const kind of ["container", "network", "volume"])
        assert.equal(
          await run("docker", [
            ...(kind === "container" ? ["ps", "-aq"] : [kind, "ls", "-q"]),
            "--filter",
            `label=com.docker.compose.project=${project}`,
          ]),
          "",
        );
    }
    const resolved = await realpath(temp);
    assert.equal(
      path.dirname(resolved).toLowerCase(),
      (await realpath(tmpdir())).toLowerCase(),
    );
    assert.ok(path.basename(resolved).startsWith("geoservice-ar01-"));
    await rm(resolved, { recursive: true });
    manifest.cleanup = "passed";
  } catch {
    manifest.cleanup = "failed";
    manifest.status = "failed";
    process.exitCode = 1;
  }
  manifest.finishedAt = new Date().toISOString();
  await writeFile(
    path.join(evidence, "verification.json"),
    JSON.stringify(manifest, null, 2) + "\n",
  );
  console.log(`${manifest.status}; cleanup=${manifest.cleanup}; ${evidence}`);
}
