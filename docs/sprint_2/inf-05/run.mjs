import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import {
  mkdir,
  mkdtemp,
  readFile,
  realpath,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { checkProxy } from "./proxy-probe.mjs";

const repo = fileURLToPath(new URL("../../../", import.meta.url));
const project = `geoservice-inf05-${randomUUID().slice(0, 8)}`;
const evidence = path.join(repo, "docs/sprint_2/evidence/inf-05", project);
const args = new Set(process.argv.slice(2));
for (const arg of args)
  assert.ok(
    [
      "--proxy-only",
      "--browser-only",
      "--fail-after-proxy",
      "--fail-after-db",
    ].includes(arg),
    `Unknown argument: ${arg}`,
  );
const manifest = {
  project,
  startedAt: new Date().toISOString(),
  status: "running",
};
const temp = await mkdtemp(path.join(tmpdir(), "geoservice-inf05-"));
const configPath = path.join(temp, "compose.json");
const emptyEnv = path.join(temp, "empty.env");
const env = { ...process.env };
delete env.COMPOSE_FILE;
delete env.COMPOSE_PROFILES;
await mkdir(evidence, { recursive: true });
await writeFile(emptyEnv, "");

function run(command, argv, { timeout = 180_000, input } = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, argv, {
      cwd: repo,
      env,
      windowsHide: true,
      detached: process.platform !== "win32",
    });
    let stdout = "",
      stderr = "",
      timedOut = false;
    child.stdout.on("data", (data) => {
      stdout += data;
    });
    child.stderr.on("data", (data) => {
      stderr += data;
    });
    child.stdin.on("error", () => {});
    child.stdin.end(input);
    const timer = setTimeout(() => {
      timedOut = true;
      if (process.platform === "win32")
        spawn("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
          windowsHide: true,
          stdio: "ignore",
        });
      else {
        try {
          process.kill(-child.pid, "SIGKILL");
        } catch {}
      }
    }, timeout);
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code === 0 && !timedOut) resolve(stdout.trim());
      else
        reject(
          new Error(
            `${command}: ${timedOut ? "timeout" : code}; ${stderr.slice(-1800)}`,
          ),
        );
    });
  });
}
const compose = (argv, options) =>
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
      ...argv,
    ],
    options,
  );
let configured = false;
const geometryPath =
  "/api/v1/work-orders/11111111-1111-4111-8111-111111111111/edit-versions/22222222-2222-4222-8222-222222222222/features/33333333-3333-4333-8333-333333333333/geometry";

async function ready(origin) {
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const response = await fetch(origin + "/api/v1/probe", {
        signal: AbortSignal.timeout(1000),
      });
      await response.arrayBuffer();
      if (response.status === 200) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("nginx/upstream readiness timeout");
}

async function fullWorkflow() {
  const { prepareFixture } = await import("./fixture.mjs");
  const { checkWorkflow } = await import("./smoke.mjs");
  const { checkLargeApi } = await import("./api-smoke.mjs");
  await compose(["down", "--volumes", "--remove-orphans", "--timeout", "10"]);
  Object.assign(env, {
    DB_NAME: "inf05",
    DB_USER: "postgres",
    DB_PASSWORD: "isolated-inf05",
    DATABASE_URL:
      "postgresql+asyncpg://postgres:isolated-inf05@postgis:5432/inf05",
    JWT_SECRET: "isolated-inf05-not-for-production",
    JWT_ALG: "HS256",
    ACCESS_TOKEN_TTL_MIN: "30",
    UTILITY_GEOMETRY_XY_RESOLUTION: "0.0000001",
    UTILITY_GEOMETRY_ROUNDING_MODE: "ROUND_HALF_AWAY_FROM_ZERO",
    CORS_ORIGINS: "http://localhost:8080",
  });
  const config = JSON.parse(
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
  delete config.services.migrate;
  for (const [name, service] of Object.entries(config.services)) {
    service.container_name = `${project}-${name}`;
    service.restart = "no";
    delete service.profiles;
    if (service.build)
      service.build.context = path.join(
        repo,
        "apps",
        name === "frontend-prod" ? "frontend" : "backend",
      );
  }
  const api = config.services.utility_service;
  const frontend = config.services["frontend-prod"];
  assert.equal(api.environment.DEV_MODE, "false");
  assert.equal(api.environment.AUTH_SESSION_COOKIE_SECURE, "true");
  assert.equal(api.build.target, "prod");
  assert.equal(frontend.build.target, "prod");
  assert.equal(api.ports, undefined);
  frontend.ports = [{ target: 80, host_ip: "127.0.0.1", published: "0" }];
  await writeFile(configPath, JSON.stringify(config));
  console.log(`${project}: build production targets from current checkout`);
  await compose(["build", "utility_service", "frontend-prod"], {
    timeout: 600_000,
  });
  async function seedDatabase() {
    await compose(["up", "-d", "--wait", "--wait-timeout", "90", "postgis"]);
    console.log(`${project}: seed disposable DB`);
    await compose([
      "run",
      "--rm",
      "--no-deps",
      "utility_service",
      "bash",
      "-lc",
      "set -euo pipefail; alembic upgrade head; python -m seeds.runners.seed_demo_users; python -m seeds.runners.seed_utility_dataset; python -m seeds.runners.seed_work_orders; python -m seeds.runners.upgrade_demo_fixture",
    ]);
  }
  await seedDatabase();
  const sql = (query) =>
    compose(
      [
        "exec",
        "-T",
        "postgis",
        "psql",
        "-X",
        "-qAt",
        "-U",
        "postgres",
        "-d",
        "inf05",
        "-v",
        "ON_ERROR_STOP=1",
      ],
      { input: query + ";\n" },
    );
  const fixture = args.has("--browser-only") ? null : await prepareFixture(sql);
  if (fixture)
    manifest.fixture = {
      workOrderId: fixture.workOrderId,
      featureId: fixture.featureId,
      checks: fixture.checks,
    };
  assert.ok(!args.has("--fail-after-db"), "Injected failure after DB fixture");
  const baseline = () =>
    sql(
      "SELECT md5(string_agg(encode(ST_AsEWKB(geometry),'hex'),'' ORDER BY default_state_id,feature_id)) FROM utility_network.default_state_features",
    );
  const network = () =>
    sql(
      "SELECT md5(string_agg(encode(ST_AsEWKB(geometry),'hex'),'' ORDER BY id)) FROM utility_network.network_features",
    );
  const before = await baseline(),
    networkBefore = await network();
  await compose([
    "up",
    "-d",
    "--wait",
    "--wait-timeout",
    "120",
    "utility_service",
    "frontend-prod",
  ]);
  await compose(["exec", "-T", "frontend-prod", "nginx", "-t"]);
  const installed = await compose([
    "exec",
    "-T",
    "frontend-prod",
    "cat",
    "/etc/nginx/conf.d/default.conf",
  ]);
  assert.equal(
    installed,
    (
      await readFile(path.join(repo, "apps/frontend/nginx.conf"), "utf8")
    ).trim(),
  );
  for (const name of ["utility_service", "frontend-prod"]) {
    const id = await compose(["ps", "-q", name]);
    manifest[`${name}Image`] = await run("docker", [
      "inspect",
      "--format",
      "{{.Image}}",
      id,
    ]);
  }
  const address = await compose(["port", "frontend-prod", "80"]);
  const origin = `http://localhost:${address.split(":").at(-1)}`;
  if (fixture) {
    console.log(`${project}: large API Save/readback/Revert at ${origin}`);
    manifest.largeApi = await checkLargeApi({ origin, fixture });
  }
  assert.equal(await baseline(), before);
  assert.equal(await network(), networkBefore);
  manifest.baselineUnchanged = true;
  manifest.networkUnchanged = true;

  // Независимая фаза на свежей БД: UI не поддерживает большие линии.
  if (fixture) {
    await compose(["down", "--volumes", "--remove-orphans", "--timeout", "10"]);
    await seedDatabase();
  }
  const small = JSON.parse(
    await sql(`SELECT json_build_object('workOrderId',d.work_order_id,
    'featureId',f.feature_id,'coordinates',(ST_AsGeoJSON(f.geometry)::json)->'coordinates')
    FROM utility_network.default_state_features f JOIN utility_network.default_states d ON d.id=f.default_state_id
    JOIN work_order.work_orders w ON w.id=d.work_order_id WHERE w.code='WO-001' AND f.asset_code='L-003'`),
  );
  const smallBefore = await baseline(),
    smallNetworkBefore = await network();
  await compose([
    "up",
    "-d",
    "--wait",
    "--wait-timeout",
    "120",
    "utility_service",
    "frontend-prod",
  ]);
  const smallAddress = await compose(["port", "frontend-prod", "80"]);
  const smallOrigin = `http://localhost:${smallAddress.split(":").at(-1)}`;
  console.log(
    `${project}: ordinary browser Save/reload/Revert/reload at ${smallOrigin}`,
  );
  manifest.workflow = await checkWorkflow({
    origin: smallOrigin,
    fixture: small,
    evidenceDirectory: evidence,
  });
  assert.equal(await baseline(), smallBefore);
  assert.equal(await network(), smallNetworkBefore);
  manifest.browserBaselineUnchanged = true;
  manifest.browserNetworkUnchanged = true;
}

try {
  manifest.docker = await run("docker", [
    "version",
    "--format",
    "{{.Server.Version}}",
  ]);
  const nginx = await readFile(path.join(repo, "apps/frontend/nginx.conf"));
  manifest.nginxSha256 = createHash("sha256").update(nginx).digest("hex");
  const config = {
    services: {
      utility_service: {
        image: "node:20-alpine",
        command: ["node", "/probe/proxy-probe.mjs", "--server"],
        volumes: [
          {
            type: "bind",
            source: path.join(repo, "docs/sprint_2/inf-05"),
            target: "/probe",
            read_only: true,
          },
        ],
      },
      proxy: {
        image: "nginx:1.27-alpine",
        depends_on: ["utility_service"],
        ports: [{ target: 80, host_ip: "127.0.0.1", published: "0" }],
        volumes: [
          {
            type: "bind",
            source: path.join(repo, "apps/frontend/nginx.conf"),
            target: "/etc/nginx/conf.d/default.conf",
            read_only: true,
          },
        ],
      },
    },
  };
  await writeFile(configPath, JSON.stringify(config));
  configured = true;
  console.log(`${project}: proxy probe`);
  await compose(["up", "-d", "--wait", "--wait-timeout", "40"]);
  const address = await compose(["port", "proxy", "80"]);
  const origin = `http://127.0.0.1:${address.split(":").at(-1)}`;
  await ready(origin);
  await compose(["exec", "-T", "proxy", "nginx", "-t"]);
  await writeFile(
    path.join(evidence, "nginx-effective.conf"),
    (await compose(["exec", "-T", "proxy", "nginx", "-T"])) + "\n",
  );
  manifest.proxy = await checkProxy(origin, geometryPath);
  assert.ok(
    manifest.proxy.passed,
    "Proxy matrix failed; see verification.json (expected geometry 200, other large paths 413)",
  );
  assert.ok(!args.has("--fail-after-proxy"), "Injected failure after proxy");
  if (!args.has("--proxy-only")) await fullWorkflow();
  manifest.status = "passed";
} catch (error) {
  manifest.status = "failed";
  manifest.error = error.message;
  console.error(error.message);
  process.exitCode = 1;
} finally {
  try {
    if (configured) {
      await compose([
        "down",
        "--volumes",
        "--remove-orphans",
        "--timeout",
        "10",
      ]);
      for (const kind of ["container", "network", "volume"]) {
        const command =
          kind === "container" ? ["ps", "-aq"] : [kind, "ls", "-q"];
        assert.equal(
          await run("docker", [
            ...command,
            "--filter",
            `label=com.docker.compose.project=${project}`,
          ]),
          "",
        );
      }
    }
    const resolved = await realpath(temp);
    assert.equal(
      path.dirname(resolved).toLowerCase(),
      (await realpath(tmpdir())).toLowerCase(),
    );
    assert.ok(path.basename(resolved).startsWith("geoservice-inf05-"));
    await rm(resolved, { recursive: true });
    manifest.cleanup = "passed";
  } catch (error) {
    manifest.cleanup = "failed";
    manifest.cleanupError = error.message;
    manifest.status = "failed";
    process.exitCode = 1;
  }
  manifest.finishedAt = new Date().toISOString();
  await writeFile(
    path.join(evidence, "verification.json"),
    JSON.stringify(manifest, null, 2) + "\n",
  );
  console.log(`${manifest.status}; cleanup ${manifest.cleanup}; ${evidence}`);
}
