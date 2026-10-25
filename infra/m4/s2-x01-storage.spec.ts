import { test, expect } from "@playwright/test";
test("storage: real IndexedDB CAS, corruption isolation and legacy receipt", async ({
  page,
}) => {
  await page.goto("/");
  const result = await page.evaluate(async () => {
    const path = "/src/stores/workspaceRecoveryIndexedDb.ts";
    const { createRecoveryStorage } = await import(/* @vite-ignore */ path);
    const fixturePath = "/src/test/workspaceEditFixture.ts";
    const { target, commandId, geometry, candidate } = await import(
      /* @vite-ignore */ fixturePath
    );
    const contractPath = "/src/contracts/workspace-recovery.ts";
    const { createRecoveryRecord } = await import(
      /* @vite-ignore */ contractPath
    );
    const storage = createRecoveryStorage();
    const a = createRecoveryRecord(
      {
        actorId: "storage-actor",
        target,
        request: { commandId, draftVersionToken: "v1", geometry: candidate },
      },
      { geometry, vertexIndex: 1 },
    );
    const b = createRecoveryRecord(
      {
        actorId: "storage-actor",
        target: { ...target, workOrderId: "B" },
        request: { commandId, draftVersionToken: "v1", geometry: candidate },
      },
      { geometry, vertexIndex: 1 },
    );
    await storage.insert(a);
    await storage.insert(b);
    let conflict = false;
    try {
      await storage.replace({ ...a, revision: 2 }, 99);
    } catch {
      conflict = true;
    }
    await storage.importLegacy(a, "same-payload");
    await storage.remove(a.key, commandId, 1);
    await storage.importLegacy(a, "same-payload");
    const loaded = await storage.list("storage-actor");
    await new Promise<void>((resolve, reject) => {
      const request = indexedDB.open("geoservice-workspace-recovery", 1);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const db = request.result;
        const tx = db.transaction("recoveries", "readwrite");
        tx.objectStore("recoveries").put({ key: a.key, schemaVersion: 99 });
        tx.oncomplete = () => {
          db.close();
          resolve();
        };
        tx.onabort = () => {
          db.close();
          reject(tx.error);
        };
      };
    });
    const corrupt = await storage.list("storage-actor");
    const other = await storage.list("other-actor");
    return {
      conflict,
      keys: loaded.records.map((r: any) => r.key),
      other: other.records.length,
      otherInvalid: other.invalid.length,
      isolated:
        corrupt.records.length === 1 &&
        corrupt.records[0].key === b.key &&
        corrupt.invalid.length === 1 &&
        corrupt.invalid[0].key === a.key,
      bkey: b.key,
    };
  });
  expect(result).toEqual({
    conflict: true,
    keys: [result.bkey],
    other: 0,
    otherInvalid: 0,
    isolated: true,
    bkey: result.bkey,
  });
});
