import assert from "node:assert/strict";
import { test } from "node:test";
import { runCommand } from "./run.mjs";

test("запускает процесс без shell и возвращает stdout", async () => {
  assert.equal(
    await runCommand(process.execPath, [
      "-e",
      "process.stdout.write(process.argv[1])",
      "literal $value & text",
    ]),
    "literal $value & text",
  );
});

test("ошибка spawn и nonzero не превращаются в успех", async () => {
  await assert.rejects(runCommand("inf03-nonexistent-command", []), /ENOENT/);
  await assert.rejects(
    runCommand(process.execPath, ["-e", "process.exit(7)"]),
    /код 7/,
  );
});

test("таймаут завершает собственный процесс", async () => {
  const start = Date.now();
  await assert.rejects(
    runCommand(process.execPath, ["-e", "setInterval(() => {}, 1000)"], 100),
    /таймаут/,
  );
  assert.ok(Date.now() - start < 10000);
});

test("таймаут завершает также потомка с унаследованным stdout", async () => {
  const script = `require('node:child_process').spawn(process.execPath, ['-e', 'setTimeout(() => {}, 4000)'], {stdio:'inherit'}); setInterval(() => {}, 1000);`;
  const start = Date.now();
  await assert.rejects(
    runCommand(process.execPath, ["-e", script], 500),
    /таймаут/,
  );
  assert.ok(
    Date.now() - start < 2500,
    "Потомок удерживает stdout после таймаута родителя",
  );
});
