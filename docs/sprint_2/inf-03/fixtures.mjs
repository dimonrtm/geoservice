import assert from "node:assert/strict";
import { copyFile, lstat, mkdir, readdir, writeFile } from "node:fs/promises";
import path from "node:path";

// Подготовка fixtures намеренно не использует проверяемый .dockerignore.
const localArtifact =
  /^(node_modules|dist|dist-ssr|coverage|\.env(?:\..*)?|\.git|\.idea|\.vscode|\.vite|\.vite-temp|\.cache|\.DS_Store|Thumbs\.db|.*\.tsbuildinfo|.*\.log)$/;
const markers = [
  "node_modules/inf03-marker.txt",
  "nested/node_modules/inf03-marker.txt",
  ".env",
  ".env.local",
  ".env.production",
  ".env.production.local",
  ".env.example",
  "nested/.env.local",
  "dist/inf03-stale.txt",
  "dist-ssr/inf03-stale.txt",
  "coverage/inf03-marker.txt",
  ".vite/inf03-marker.txt",
  ".vscode/inf03-marker.txt",
  "inf03.tsbuildinfo",
  "inf03.log",
];

export async function prepareContext(
  sourceDir,
  targetDir,
  { contaminated, omitIgnore = false },
) {
  const source = path.resolve(sourceDir);
  const target = path.resolve(targetDir);
  const relative = path.relative(source, target);
  assert.ok(
    relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative),
    "Context должен быть вне исходного каталога",
  );
  await mkdir(target);
  async function copyDirectory(from, to) {
    for (const name of await readdir(from)) {
      if (
        localArtifact.test(name) ||
        (omitIgnore &&
          (name === ".dockerignore" || name.endsWith(".dockerignore")))
      )
        continue;
      const src = path.join(from, name);
      const dest = path.join(to, name);
      const stat = await lstat(src);
      assert.ok(
        !stat.isSymbolicLink(),
        `Ссылка не допускается в context: ${path.relative(source, src)}`,
      );
      if (stat.isDirectory()) {
        await mkdir(dest);
        await copyDirectory(src, dest);
      } else {
        assert.ok(stat.isFile(), `Неподдерживаемый тип файла: ${name}`);
        await copyFile(src, dest);
      }
    }
  }
  await copyDirectory(source, target);
  const fixturePaths = contaminated ? [...markers] : [];
  const forbiddenUrl = contaminated ? "https://inf03-build.invalid" : null;
  for (const name of fixturePaths) {
    const dest = path.join(target, name);
    await mkdir(path.dirname(dest), { recursive: true });
    await writeFile(
      dest,
      path.basename(name).startsWith(".env")
        ? `VITE_API_BASE_URL=${forbiddenUrl}\n`
        : "INF03_SYNTHETIC_MARKER\n",
      { flag: "wx" },
    );
  }
  return { fixturePaths, forbiddenUrl };
}

export async function assertFixturesPresent(contextDir, fixturePaths) {
  for (const name of fixturePaths) {
    const stat = await lstat(path.join(contextDir, name)).catch(() => null);
    assert.ok(stat?.isFile(), `Отсутствует искусственный файл: ${name}`);
  }
}
