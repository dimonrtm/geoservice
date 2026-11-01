import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { randomUUID, createHash } from "node:crypto";
import {
  access,
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  realpath,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { prepareContext, assertFixturesPresent } from "./fixtures.mjs";
import { readHttpResponse } from "./http-probe.mjs";

const repo = fileURLToPath(new URL("../../../", import.meta.url));

export function runCommand(command, args, timeout = 120000) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      shell: false,
      windowsHide: true,
      detached: process.platform !== "win32",
    });
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    child.stdout.on("data", (data) => {
      stdout = (stdout + data).slice(-65536);
    });
    child.stderr.on("data", (data) => {
      stderr = (stderr + data).slice(-65536);
    });
    const timer = setTimeout(() => {
      timedOut = true;
      if (process.platform === "win32") {
        // Docker CLI запускает buildx-плагин: завершаем всё собственное дерево.
        const killer = spawn(
          "taskkill.exe",
          ["/PID", String(child.pid), "/T", "/F"],
          {
            shell: false,
            windowsHide: true,
            stdio: "ignore",
          },
        );
        killer.on("error", () => child.kill("SIGKILL"));
        killer.on("close", (code) => {
          if (code !== 0) child.kill("SIGKILL");
        });
      } else {
        try {
          process.kill(-child.pid, "SIGKILL");
        } catch (error) {
          if (error.code !== "ESRCH") child.kill("SIGKILL");
        }
      }
    }, timeout);
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (timedOut) reject(new Error(`${command}: таймаут ${timeout} мс`));
      else if (code !== 0)
        reject(new Error(`${command}: код ${code}. ${stderr.slice(-4000)}`));
      else resolve(stdout.trim());
    });
  });
}

export async function runVerification({
  sourceDir = path.join(repo, "apps/frontend"),
  evidenceDir,
  acceptance = false,
} = {}) {
  const id = `geoservice-inf03-${randomUUID().slice(0, 12)}`;
  const evidence = path.resolve(
    evidenceDir ?? path.join(repo, "docs/sprint_2/evidence/inf-03", id),
  );
  await mkdir(evidence, { recursive: true });
  const temp = await mkdtemp(path.join(tmpdir(), `${id}-`));
  const ownedTemp = await realpath(temp);
  const containers = new Set();
  const images = new Set();
  const summary = {
    id,
    status: "running",
    acceptance,
    node: process.version,
    checks: [],
    cleanupErrors: [],
  };
  const docker = (args, timeout) => runCommand("docker", args, timeout);
  let workspaceMode = false;
  const check = (name, details = {}) => {
    summary.checks.push({ name, status: "passed", ...details });
    console.log(`${id}: ${name} — пройдено`);
  };
  async function build(context, mode, target) {
    const tag = `${id}:${mode}-${target}`;
    images.add(tag);
    console.log(`${id}: сборка ${mode}/${target}`);
    await docker(
      [
        "buildx",
        "build",
        "--load",
        "--progress=plain",
        "--target",
        target,
        "-t",
        tag,
        context,
      ],
      600000,
    );
    return tag;
  }
  async function inspectBase(tag, fixturePaths, mode) {
    const name = `${id}-${mode}-inspect`;
    containers.add(name);
    const script = `const fs=require('node:fs'); const input=JSON.parse(process.argv[1]); console.log(JSON.stringify({present:input.fixtures.filter(p=>fs.existsSync('/app/'+p)),missing:input.required.filter(p=>!fs.existsSync('/app/'+p))}));`;
    const required = [
      "node_modules/vite/package.json",
      "src/api/baseUrl.ts",
      "public",
      "package.json",
      "package-lock.json",
      "index.html",
      "vite.config.ts",
      "tsconfig.json",
      "nginx.conf",
    ];
    const result = JSON.parse(
      await docker([
        "run",
        "--name",
        name,
        "--entrypoint",
        "node",
        tag,
        "-e",
        script,
        JSON.stringify({ fixtures: fixturePaths, required }),
      ]),
    );
    assert.deepEqual(
      result.missing,
      [],
      "Необходимые входы сборки отсутствуют",
    );
    return result.present;
  }
  async function inspectStatic(tag, mode) {
    const name = `${id}-${mode}-static`;
    containers.add(name);
    await docker(["create", "--name", name, tag]);
    const output = path.join(temp, `${mode}-html`);
    await mkdir(output);
    await docker(["cp", `${name}:/usr/share/nginx/html/.`, output]);
    assert.ok((await lstat(path.join(output, "index.html"))).isFile());
    assert.ok(
      (await readdir(path.join(output, "assets"))).length > 0,
      "Нет собранных assets",
    );
    async function inspect(directory) {
      for (const entry of await readdir(directory, { withFileTypes: true })) {
        const file = path.join(directory, entry.name);
        assert.ok(!entry.isSymbolicLink(), "Ссылка в итоговой статике");
        if (entry.isDirectory()) await inspect(file);
        else {
          assert.notEqual(
            entry.name,
            "inf03-stale.txt",
            "Старый dist попал в сайт",
          );
          const bytes = await readFile(file);
          assert.ok(
            !bytes.includes("https://inf03-build.invalid"),
            "Посторонний API URL встроен в сайт",
          );
          assert.ok(
            !bytes.includes("INF03_SYNTHETIC_MARKER"),
            "Маркер попал в сайт",
          );
        }
      }
    }
    await inspect(output);
    check(`${mode}:prod-static`);
  }
  async function inspectDev(tag, mode) {
    console.log(`${id}: проверка ${mode}/dev-runtime`);
    const name = `${id}-${mode}-dev`;
    containers.add(name);
    await docker([
      "run",
      "-d",
      "--name",
      name,
      "-p",
      "127.0.0.1::5173",
      "-e",
      "VITE_API_BASE_URL=https://inf03-runtime.invalid",
      tag,
    ]);
    const ports = JSON.parse(
      await docker([
        "inspect",
        "--format",
        "{{json .NetworkSettings.Ports}}",
        name,
      ]),
    );
    const port = ports["5173/tcp"].find(
      (item) => item.HostIp === "127.0.0.1",
    ).HostPort;
    const origin = `http://127.0.0.1:${port}`;
    const deadline = Date.now() + 60000;
    let ready = false;
    while (Date.now() < deadline) {
      try {
        const response = await readHttpResponse(origin, 2000);
        if (response.status === 200) {
          ready = true;
          break;
        }
      } catch {
        /* Vite ещё запускается. */
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    assert.ok(ready, "Vite не ответил за 60 секунд");
    const response = await readHttpResponse(
      `${origin}/src/api/baseUrl.ts`,
      10000,
    );
    assert.equal(response.status, 200);
    assert.match(
      response.text,
      /"VITE_API_BASE_URL"\s*:\s*"https:\/\/inf03-runtime\.invalid"/,
      "Vite не подставил явный runtime API URL",
    );
    check(`${mode}:dev-runtime`);
  }
  async function scenario(context, fixtures, mode) {
    const dev = await build(context, mode, "dev");
    const present = await inspectBase(dev, fixtures, mode);
    assert.deepEqual(
      present,
      [],
      `Локальные файлы попали в общий слой: ${present.join(", ")}`,
    );
    check(`${mode}:base-isolation`, { fixtureCount: fixtures.length });
    const prod = await build(context, mode, "prod");
    await inspectStatic(prod, mode);
    await inspectDev(dev, mode);
  }
  try {
    summary.docker = await docker([
      "version",
      "--format",
      "{{.Server.Version}}",
    ]);
    summary.buildx = await docker(["buildx", "version"]);
    const dirty = path.join(temp, "dirty");
    const fixtures = await prepareContext(sourceDir, dirty, {
      contaminated: true,
    });
    await assertFixturesPresent(dirty, fixtures.fixturePaths);
    check("fixtures-present", { count: fixtures.fixturePaths.length });
    await scenario(dirty, fixtures.fixturePaths, "dirty");
    if (acceptance) {
      const clean = path.join(temp, "clean");
      await prepareContext(sourceDir, clean, { contaminated: false });
      await scenario(clean, fixtures.fixturePaths, "clean");
      const negative = path.join(temp, "negative");
      const negativeFixtures = await prepareContext(sourceDir, negative, {
        contaminated: true,
        omitIgnore: true,
      });
      await assertFixturesPresent(negative, negativeFixtures.fixturePaths);
      const tag = await build(negative, "negative", "dev");
      const present = await inspectBase(
        tag,
        negativeFixtures.fixturePaths,
        "negative",
      );
      assert.deepEqual(
        present,
        negativeFixtures.fixturePaths,
        "Отрицательный контроль не обнаружил все загрязнения",
      );
      check("negative-control", { detected: present });
      // Реальный context отправляется только с теми же правилами, что прошли тест.
      const ignore = await readFile(path.join(sourceDir, ".dockerignore"));
      assert.deepEqual(
        ignore,
        await readFile(path.join(dirty, ".dockerignore")),
      );
      await assert.rejects(
        access(path.join(sourceDir, "Dockerfile.dockerignore")),
        { code: "ENOENT" },
      );
      summary.ignoreSha256 = createHash("sha256").update(ignore).digest("hex");
      workspaceMode = true;
      await scenario(sourceDir, fixtures.fixturePaths, "workspace");
    }
    summary.status = "passed";
  } catch (error) {
    summary.status = "failed";
    // Не сохраняем потенциальный вывод пользовательских build scripts.
    summary.error = workspaceMode
      ? "Ошибка проверки рабочего context; пользовательский вывод не сохранён"
      : error.message;
    console.error(`${id}: ${summary.error}`);
  } finally {
    for (const [kind, names] of [
      ["container", containers],
      ["image", images],
    ]) {
      for (const name of names) {
        try {
          await docker(
            kind === "container" ? ["rm", "-f", name] : ["image", "rm", name],
          );
        } catch (error) {
          if (!/No such (container|image)/i.test(error.message))
            summary.cleanupErrors.push(`${kind} ${name}: ${error.message}`);
        }
      }
    }
    try {
      assert.equal(await realpath(temp), ownedTemp);
      assert.equal(path.dirname(ownedTemp), await realpath(tmpdir()));
      assert.ok(path.basename(ownedTemp).startsWith(`${id}-`));
      await rm(ownedTemp, { recursive: true, force: true });
    } catch (error) {
      summary.cleanupErrors.push(`temp: ${error.message}`);
    }
    if (summary.cleanupErrors.length) summary.status = "failed";
    await writeFile(
      path.join(evidence, "summary.json"),
      `${JSON.stringify(summary, null, 2)}\n`,
    );
    console.log(`${id}: ${summary.status}; evidence: ${evidence}`);
  }
  return summary;
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  try {
    const { values } = parseArgs({
      options: {
        acceptance: { type: "boolean", default: false },
        "evidence-dir": { type: "string" },
      },
      allowPositionals: false,
    });
    const summary = await runVerification({
      acceptance: values.acceptance,
      evidenceDir: values["evidence-dir"],
    });
    process.exitCode = summary.status === "passed" ? 0 : 1;
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
