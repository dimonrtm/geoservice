import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import {
  failedAcceptanceResult,
  recordAcceptanceResult,
} from "./acceptanceResult.mjs";

async function evidenceFile(t) {
  const directory = await mkdtemp(path.join(tmpdir(), "ar01-result-test-"));
  t.after(async () => {
    assert.equal(path.dirname(directory), path.resolve(tmpdir()));
    assert.ok(path.basename(directory).startsWith("ar01-result-test-"));
    await rm(directory, { recursive: true });
  });
  const filename = path.join(directory, "browser.json");
  return {
    persist: (result) => writeFile(filename, JSON.stringify(result) + "\n"),
    read: async () => JSON.parse(await readFile(filename, "utf8")),
  };
}

for (const failureAt of [
  "next context setup",
  "context cleanup",
  "browser cleanup",
]) {
  test(`successful first case cannot hide ${failureAt} exception`, async (t) => {
    const evidence = await evidenceFile(t);
    const result = { cases: {} };
    const failure = new Error(failureAt);
    let browserClosed = false;

    await assert.rejects(
      recordAcceptanceResult(
        result,
        async () => {
          result.cases.first = { passed: true };
          if (failureAt === "next context setup") {
            const contextFor = async () => {
              throw failure;
            };
            await contextFor();
          }
          if (failureAt === "context cleanup") {
            result.cases.second = { passed: true };
            const context = {
              close: async () => {
                throw failure;
              },
            };
            await context.close();
          }
        },
        {
          close: async () => {
            browserClosed = true;
            if (failureAt === "browser cleanup") throw failure;
          },
          persist: evidence.persist,
        },
      ),
      (error) => error === failure,
    );

    assert.equal(browserClosed, true);
    const saved = await evidence.read();
    assert.equal(saved.cases.first.passed, true);
    assert.equal(saved.passed, false);
    assert.equal(saved.completed, false);
    assert.equal(saved.aborted, true);
  });
}

test("persistence exception clears success even when a prior snapshot exists", async (t) => {
  const evidence = await evidenceFile(t);
  const result = { cases: {} };
  const failure = new Error("persist failed after writing");
  let writes = 0;
  let browserClosed = false;

  await assert.rejects(
    recordAcceptanceResult(
      result,
      async () => {
        result.cases.first = { passed: true };
      },
      {
        close: async () => {
          browserClosed = true;
        },
        persist: async (value) => {
          await evidence.persist(value);
          if (++writes === 1) throw failure;
        },
      },
    ),
    (error) => error === failure,
  );

  assert.equal(browserClosed, true);
  assert.equal(result.passed, false);
  assert.equal((await evidence.read()).passed, false);
});

test("runner catch cannot recover success from a stale passed browser JSON", () => {
  const saved = {
    passed: true,
    completed: true,
    cases: { first: { passed: true } },
  };
  const recovered = failedAcceptanceResult(saved);
  assert.equal(recovered.passed, false);
  assert.equal(recovered.completed, false);
  assert.equal(recovered.aborted, true);
  assert.equal(recovered.cases.first.passed, true);
  const manifest = { browsers: { chrome: recovered } };
  assert.equal(
    Object.values(manifest.browsers).every((entry) => entry.passed),
    false,
  );
});

test("normal completion records passed cases and closes browser", async (t) => {
  const evidence = await evidenceFile(t);
  const result = { cases: {} };
  let closed = false;
  await recordAcceptanceResult(
    result,
    async () => {
      result.cases.first = { passed: true };
    },
    {
      close: async () => {
        closed = true;
      },
      persist: evidence.persist,
    },
  );
  assert.equal(closed, true);
  const saved = await evidence.read();
  assert.equal(saved.passed, true);
  assert.equal(saved.completed, true);
  assert.equal(saved.aborted, false);
});

test("normal completion without matching cases is not a pass", async (t) => {
  const evidence = await evidenceFile(t);
  const result = { cases: {} };
  await recordAcceptanceResult(result, async () => {}, {
    close: async () => {},
    persist: evidence.persist,
  });
  assert.equal((await evidence.read()).passed, false);
});
