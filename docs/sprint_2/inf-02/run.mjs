import { spawn } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import {
  cp,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  realpath,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { createServer } from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import { workflow, websocket } from "./smoke.mjs";

const repo = fileURLToPath(new URL("../../../", import.meta.url));
const project = `geoservice-inf02-${randomUUID().slice(0, 8)}`;
const evidence = path.join(repo, "docs/sprint_2/evidence/inf-02", project);
const temp = await mkdtemp(path.join(tmpdir(), "geoservice-inf02-"));
const configPath = path.join(temp, "compose.json");
const emptyEnv = path.join(temp, "empty.env");
const manifest = {
  project,
  startedAt: new Date().toISOString(),
  status: "running",
};
await mkdir(evidence, { recursive: true });
await writeFile(emptyEnv, "");
const env = {
  ...process.env,
  DB_NAME: "inf02",
  DB_USER: "postgres",
  DB_PASSWORD: "isolated-inf02",
  DATABASE_URL:
    "postgresql+asyncpg://postgres:isolated-inf02@postgis:5432/inf02",
  JWT_SECRET: "isolated-inf02-not-for-production",
  JWT_ALG: "HS256",
  ACCESS_TOKEN_TTL_MIN: "30",
  UTILITY_GEOMETRY_XY_RESOLUTION: "0.0000001",
  UTILITY_GEOMETRY_ROUNDING_MODE: "ROUND_HALF_AWAY_FROM_ZERO",
  CORS_ORIGINS: "http://localhost:8080",
};
delete env.COMPOSE_FILE;
delete env.COMPOSE_PROFILES;

async function run(command, args, timeout = 120_000) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: repo, env, windowsHide: true });
    let output = "";
    child.stdout.on("data", (data) => {
      output += data;
    });
    child.stderr.on("data", (data) => {
      output += data;
    });
    const timer = setTimeout(() => {
      child.kill();
    }, timeout);
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code === 0) resolve(output.trim());
      else reject(new Error(`${command}: код ${code}. ${output.slice(-3000)}`));
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
      "--profile",
      "prod",
      ...args,
    ],
    args[0] === "build" ? 600_000 : 180_000,
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
    "inf02",
    "-At",
    "-v",
    "ON_ERROR_STOP=1",
    "-c",
    query,
  );
const baseline = () =>
  sql(
    "SELECT md5(string_agg(encode(ST_AsEWKB(geometry), 'hex'), '' ORDER BY default_state_id, feature_id)) FROM utility_network.default_state_features",
  );
const excluded =
  /^(\.env(?:\..*)?|node_modules|dist|build|\.git|\.venv|venv|__pycache__|\.pytest_cache|\.ruff_cache|\.mypy_cache|htmlcov|.*\.py[co])$/;
const hashes = {};
async function hashFiles(directory, prefix) {
  for (const item of await readdir(directory, { withFileTypes: true })) {
    const filename = path.join(directory, item.name);
    const key = `${prefix}/${item.name}`;
    if (item.isDirectory()) await hashFiles(filename, key);
    else
      hashes[key] = createHash("sha256")
        .update(await readFile(filename))
        .digest("hex");
  }
}
let config;
let configured = false;
try {
  console.log(
    `${project}: подготовка чистого контекста и production-конфигурации`,
  );
  manifest.docker = await run("docker", [
    "version",
    "--format",
    "{{.Server.Version}}",
  ]);
  manifest.compose = await run("docker", ["compose", "version", "--short"]);
  for (const app of ["frontend", "backend"]) {
    const dest = path.join(temp, app);
    await cp(path.join(repo, "apps", app), dest, {
      recursive: true,
      filter: (source) => !excluded.test(path.basename(source)),
    });
    await hashFiles(dest, app);
  }
  await writeFile(
    path.join(evidence, "source-hashes.json"),
    JSON.stringify(hashes, null, 2) + "\n",
  );
  config = JSON.parse(
    await run("docker", [
      "compose",
      "--env-file",
      emptyEnv,
      "-p",
      project,
      "-f",
      path.join(repo, "infra/docker-compose.yml"),
      "--profile",
      "prod",
      "config",
      "--format",
      "json",
    ]),
  );
  const api = config.services.utility_service;
  const frontend = config.services["frontend-prod"];
  assert.equal(api.environment.DEV_MODE, "false");
  assert.equal(api.environment.AUTH_SESSION_COOKIE_SECURE, "true");
  assert.equal(api.build.target, "prod");
  assert.equal(frontend.build.target, "prod");
  assert.equal(api.ports, undefined);
  delete config.services.migrate;
  for (const [name, service] of Object.entries(config.services)) {
    service.container_name = `${project}-${name}`;
    service.restart = "no";
    if (service.build)
      service.build.context = path.join(
        temp,
        name === "frontend-prod" ? "frontend" : "backend",
      );
  }
  const portProbe = createServer();
  await new Promise((resolve, reject) => {
    portProbe.once("error", reject);
    portProbe.listen(0, "127.0.0.1", resolve);
  });
  const frontendPort = portProbe.address().port;
  await new Promise((resolve, reject) =>
    portProbe.close((error) => (error ? reject(error) : resolve())),
  );
  frontend.ports = [
    {
      target: 80,
      published: String(frontendPort),
      host_ip: "127.0.0.1",
      protocol: "tcp",
    },
  ];
  await writeFile(configPath, JSON.stringify(config, null, 2) + "\n");
  configured = true;
  console.log("Сборка frontend/API target prod (лимит 10 минут)...");
  await compose("build", "utility_service", "frontend-prod");
  await compose("up", "-d", "--wait", "--wait-timeout", "90", "postgis");
  console.log("Отдельная подготовка disposable БД...");
  await compose(
    "run",
    "--rm",
    "--no-deps",
    "utility_service",
    "bash",
    "-lc",
    "set -euo pipefail; alembic upgrade head; python -m seeds.runners.seed_demo_users; python -m seeds.runners.seed_utility_dataset; python -m seeds.runners.seed_work_orders; python -m seeds.runners.upgrade_demo_fixture",
  );
  const layerId = randomUUID();
  await sql(
    `INSERT INTO layers (id, name, title, geometry_type, srid, storage_table) VALUES ('${layerId}', 'inf02', 'INF-02', 'Point', 4326, 'feature_points')`,
  );
  const before = await baseline();
  assert.match(before, /^[a-f0-9]{32}$/);
  await compose(
    "up",
    "-d",
    "--wait",
    "--wait-timeout",
    "90",
    "utility_service",
    "frontend-prod",
  );
  const address = await compose("port", "frontend-prod", "80");
  const origin = `http://localhost:${address.split(":").at(-1)}`;
  manifest.origin = origin;
  const settings = await compose(
    "exec",
    "-T",
    "utility_service",
    "python",
    "-c",
    "from utility_service.utils.settings import settings; import json; print(json.dumps([settings.dev_auth_enabled, settings.auth_session_cookie_secure, settings.legacy_gis_api_enabled]))",
  );
  assert.deepEqual(JSON.parse(settings), [false, true, false]);
  manifest.settings = {
    devMode: false,
    secureCookie: true,
    legacyDefault: false,
  };
  manifest.nginx = await compose("exec", "-T", "frontend-prod", "nginx", "-t");
  for (const service of ["utility_service", "frontend-prod"]) {
    const id = await compose("ps", "-q", service);
    manifest[`${service}Image`] = await run("docker", [
      "inspect",
      "--format",
      "{{.Image}}",
      id,
    ]);
  }
  console.log(
    `Браузерная проверка login → Save → reload → Revert → logout через ${origin}`,
  );
  manifest.workflow = await workflow(origin, layerId, evidence);
  assert.equal(await baseline(), before);
  manifest.baselineUnchanged = true;
  console.log(
    "Отдельная фаза legacy WebSocket: включение flag и restart nginx...",
  );
  api.environment.LEGACY_GIS_API_ENABLED = "true";
  await writeFile(configPath, JSON.stringify(config, null, 2) + "\n");
  await compose(
    "up",
    "-d",
    "--wait",
    "--wait-timeout",
    "90",
    "utility_service",
  );
  await compose("restart", "frontend-prod");
  const readyDeadline = Date.now() + 30_000;
  let ready = false;
  while (Date.now() < readyDeadline && !ready) {
    try {
      const response = await fetch(
        `${origin}/api/v1/work-orders/assigned-to-me`,
        { signal: AbortSignal.timeout(2000) },
      );
      ready = response.status === 401;
      await response.arrayBuffer();
    } catch {
      /* nginx ещё запускается */
    }
    if (!ready) await new Promise((resolve) => setTimeout(resolve, 500));
  }
  assert.ok(ready, "Маршрут API не восстановился после restart nginx");
  console.log("Проверка WebSocket, включая 65 секунд соединения...");
  manifest.websocket = await websocket(origin, layerId);
  const logs = await compose("logs", "--no-color", "frontend-prod");
  assert.ok(
    !logs.includes("ticket="),
    "Ticket не должен попадать в frontend logs",
  );
  await writeFile(path.join(evidence, "frontend.log"), logs + "\n");
  manifest.status = "passed";
} catch (error) {
  manifest.status = "failed";
  // Не сохраняем текст ошибок Playwright с возможными cookie/ticket/headers.
  manifest.error = String(error.message).replace(
    /ticket=[^\s"&]+/g,
    "ticket=[скрыто]",
  );
  console.error(manifest.error);
  process.exitCode = 1;
} finally {
  try {
    if (configured) {
      const ids = (await compose("ps", "-aq")).split(/\s+/).filter(Boolean);
      for (const id of ids) {
        const owner = await run("docker", [
          "inspect",
          "--format",
          '{{index .Config.Labels "com.docker.compose.project"}}',
          id,
        ]);
        assert.equal(owner, project);
      }
      for (const kind of ["network", "volume"]) {
        const ids = (
          await run("docker", [
            kind,
            "ls",
            "-q",
            "--filter",
            `label=com.docker.compose.project=${project}`,
          ])
        )
          .split(/\s+/)
          .filter(Boolean);
        for (const id of ids) {
          const owner = await run("docker", [
            kind,
            "inspect",
            "--format",
            '{{index .Labels "com.docker.compose.project"}}',
            id,
          ]);
          assert.equal(owner, project);
        }
      }
      await compose("down", "--volumes", "--remove-orphans", "--timeout", "10");
      for (const kind of ["container", "network", "volume"]) {
        const args = kind === "container" ? ["ps", "-aq"] : [kind, "ls", "-q"];
        assert.equal(
          await run("docker", [
            ...args,
            "--filter",
            `label=com.docker.compose.project=${project}`,
          ]),
          "",
        );
      }
    }
    const resolvedTemp = await realpath(temp);
    assert.equal(
      path.dirname(resolvedTemp).toLowerCase(),
      (await realpath(tmpdir())).toLowerCase(),
    );
    assert.ok(path.basename(resolvedTemp).startsWith("geoservice-inf02-"));
    await rm(resolvedTemp, { recursive: true });
    manifest.cleanup = "passed";
  } catch (error) {
    manifest.cleanup = "failed";
    manifest.status = "failed";
    console.error(`Ошибка очистки: ${error.message}`);
    process.exitCode = 1;
  }
  manifest.finishedAt = new Date().toISOString();
  await writeFile(
    path.join(evidence, "verification.json"),
    JSON.stringify(manifest, null, 2) + "\n",
  );
  console.log(
    `Результат: ${manifest.status}; cleanup: ${manifest.cleanup}; ${evidence}`,
  );
}
