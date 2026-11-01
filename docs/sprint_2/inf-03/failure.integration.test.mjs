import assert from "node:assert/strict";
import { test } from "node:test";
import { mkdtemp, readFile, writeFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { prepareContext } from "./fixtures.mjs";
import { runCommand, runVerification } from "./run.mjs";

test(
  "ошибка Docker build сохраняет failed и очищает только свои ресурсы",
  { timeout: 600000 },
  async () => {
    const repo = fileURLToPath(new URL("../../../", import.meta.url));
    const temp = await mkdtemp(path.join(tmpdir(), "inf03-failure-test-"));
    try {
      const source = path.join(temp, "source");
      await prepareContext(path.join(repo, "apps/frontend"), source, {
        contaminated: false,
      });
      const dockerfile = path.join(source, "Dockerfile");
      const original = await readFile(dockerfile, "utf8");
      assert.ok(original.includes("RUN npm run build"));
      await writeFile(
        dockerfile,
        original.replace("RUN npm run build", "RUN exit 37"),
      );
      const sibling = path.join(temp, "keep.txt");
      await writeFile(sibling, "сохранить");
      const evidenceDir = path.join(
        repo,
        "docs/sprint_2/evidence/inf-03/failure-path",
      );
      const summary = await runVerification({ sourceDir: source, evidenceDir });
      assert.equal(summary.status, "failed");
      assert.match(summary.error, /37/);
      assert.deepEqual(summary.cleanupErrors, []);
      assert.ok(
        summary.checks.some((check) => check.name === "dirty:base-isolation"),
      );
      assert.equal(await readFile(sibling, "utf8"), "сохранить");
      assert.ok((await readFile(dockerfile, "utf8")).includes("RUN exit 37"));
      assert.ok(
        !(await readdir(tmpdir())).some((name) => name.startsWith(summary.id)),
      );
      assert.equal(
        await runCommand("docker", [
          "ps",
          "-aq",
          "--filter",
          `name=${summary.id}`,
        ]),
        "",
      );
      assert.equal(
        await runCommand("docker", ["images", "-q", `${summary.id}:*`]),
        "",
      );
    } finally {
      // temp — исключительно mkdtemp этого теста; source и соседний маркер внутри него.
      assert.ok(path.basename(temp).startsWith("inf03-failure-test-"));
      assert.equal(path.dirname(temp), path.resolve(tmpdir()));
      await rm(temp, { recursive: true, force: true });
    }
  },
);
