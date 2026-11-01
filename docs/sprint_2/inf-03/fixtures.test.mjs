import assert from "node:assert/strict";
import { test } from "node:test";
import {
  mkdtemp,
  mkdir,
  readFile,
  writeFile,
  rm,
  symlink,
  access,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { prepareContext, assertFixturesPresent } from "./fixtures.mjs";

async function workspace(t) {
  const temp = await mkdtemp(path.join(tmpdir(), "inf03-fixtures-test-"));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const source = path.join(temp, "source");
  await mkdir(source);
  const put = async (name, value = "локальный файл") => {
    const dest = path.join(source, name);
    await mkdir(path.dirname(dest), { recursive: true });
    await writeFile(dest, value);
  };
  return { temp, source, target: path.join(temp, "target"), put };
}

test("сохраняет текущие исходники и public, заменяя только локальные артефакты", async (t) => {
  const { source, target, put } = await workspace(t);
  await put("src/current.ts", "незакоммиченный исходник");
  await put("public/resource.txt", "нужный ресурс");
  await put(".dockerignore", "правила");
  await put("Dockerfile.dockerignore", "особые правила");
  await put(".env.local", "PRIVATE_LOCAL_VALUE");
  await put("nested/.env.production", "PRIVATE_LOCAL_VALUE");
  await put("node_modules/host-only.txt");
  await put("dist/host-only.txt");
  const result = await prepareContext(source, target, {
    contaminated: true,
    omitIgnore: false,
  });
  assert.equal(
    await readFile(path.join(target, "src/current.ts"), "utf8"),
    "незакоммиченный исходник",
  );
  assert.equal(
    await readFile(path.join(target, "public/resource.txt"), "utf8"),
    "нужный ресурс",
  );
  assert.equal(
    await readFile(path.join(target, "Dockerfile.dockerignore"), "utf8"),
    "особые правила",
  );
  assert.equal(
    await readFile(path.join(target, ".dockerignore"), "utf8"),
    "правила",
  );
  assert.ok(
    !(await readFile(path.join(target, ".env.local"), "utf8")).includes(
      "PRIVATE_LOCAL_VALUE",
    ),
  );
  await assert.rejects(access(path.join(target, "nested/.env.production")), {
    code: "ENOENT",
  });
  await assert.rejects(
    access(path.join(target, "node_modules/host-only.txt")),
    { code: "ENOENT" },
  );
  await assert.rejects(access(path.join(target, "dist/host-only.txt")), {
    code: "ENOENT",
  });
  assert.ok(
    result.fixturePaths.includes("nested/node_modules/inf03-marker.txt"),
  );
  assert.ok(result.fixturePaths.includes("nested/.env.local"));
  assert.equal(result.forbiddenUrl, "https://inf03-build.invalid");
  await assertFixturesPresent(target, result.fixturePaths);
  await rm(path.join(target, "dist/inf03-stale.txt"));
  await assert.rejects(
    assertFixturesPresent(target, result.fixturePaths),
    /dist\/inf03-stale.txt/,
  );
  assert.equal(
    await readFile(path.join(source, ".env.local"), "utf8"),
    "PRIVATE_LOCAL_VALUE",
  );
});

test("чистая и отрицательная копии не меняют правила исходного дерева", async (t) => {
  const { source, target, put } = await workspace(t);
  await put(".dockerignore", "правила");
  await put("Dockerfile.dockerignore", "особые правила");
  const result = await prepareContext(source, target, {
    contaminated: false,
    omitIgnore: true,
  });
  assert.deepEqual(result, { fixturePaths: [], forbiddenUrl: null });
  await assert.rejects(access(path.join(target, ".dockerignore")), {
    code: "ENOENT",
  });
  await assert.rejects(access(path.join(target, "Dockerfile.dockerignore")), {
    code: "ENOENT",
  });
  assert.equal(
    await readFile(path.join(source, ".dockerignore"), "utf8"),
    "правила",
  );
  await assert.rejects(prepareContext(source, target, { contaminated: true }), {
    code: "EEXIST",
  });
});

test("не следует junction/symlink во внешнюю папку", async (t) => {
  const { temp, source, target } = await workspace(t);
  const outside = path.join(temp, "outside");
  await mkdir(outside);
  await writeFile(path.join(outside, "keep.txt"), "не трогать");
  await symlink(
    outside,
    path.join(source, "linked"),
    process.platform === "win32" ? "junction" : "dir",
  );
  await assert.rejects(
    prepareContext(source, target, { contaminated: false }),
    /ссылк/i,
  );
  assert.equal(
    await readFile(path.join(outside, "keep.txt"), "utf8"),
    "не трогать",
  );
});
