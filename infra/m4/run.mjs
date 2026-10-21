import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

const cwd = fileURLToPath(new URL(".", import.meta.url));
const project = `geoservice-m4-${randomUUID().slice(0, 8)}`;
const env = { ...process.env, M4_PROJECT: project };
async function run(command, args) {
  await new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      env,
      stdio: "inherit",
      windowsHide: true,
    });
    child.on("error", reject);
    child.on("exit", (code) =>
      code === 0 ? resolve() : reject(new Error(`${command}: exit ${code}`)),
    );
  });
}
const compose = (...args) =>
  run("docker", ["compose", "-p", project, "-f", "compose.yml", ...args]);
try {
  await compose("build");
  await compose("up", "-d", "--wait", "db");
  // Инициализация выполняется только до измеряемых сценариев.
  await compose(
    "run",
    "--rm",
    "--no-deps",
    "api",
    "bash",
    "-lc",
    "set -euo pipefail; alembic upgrade head; python -m seeds.runners.seed_demo_users; python -m seeds.runners.seed_utility_dataset; python -m seeds.runners.seed_work_orders; python -m seeds.runners.upgrade_demo_fixture",
  );
  await compose("up", "-d", "--wait", "api", "frontend");
  await run(process.execPath, ["node_modules/@playwright/test/cli.js", "test"]);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
} finally {
  // Только уникальный disposable-проект этого запуска, после обоих сценариев.
  try {
    await compose("down", "--volumes", "--remove-orphans", "--rmi", "local");
  } catch (error) {
    console.error(
      `Не удалось очистить тестовый проект ${project}: ${error.message}`,
    );
    process.exitCode = 1;
  }
}
