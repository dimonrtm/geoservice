import { beforeEach, describe, expect, it, vi } from "vitest";
import { IDBFactory, IDBObjectStore } from "fake-indexeddb";
import { createRecoveryStorage } from "./workspaceRecoveryStorage";
import { createRecoveryRecord } from "@/contracts/workspace-recovery";
import {
  candidate,
  commandId,
  geometry,
  target,
} from "@/test/workspaceEditFixture";

const makeRecord = (suffix = "") =>
  createRecoveryRecord(
    {
      actorId: "actor",
      target: { ...target, workOrderId: target.workOrderId + suffix },
      request: {
        commandId,
        draftVersionToken: "revision-a",
        geometry: candidate,
      },
    },
    { geometry, vertexIndex: 1 },
  );
beforeEach(() => {
  Object.defineProperty(globalThis, "indexedDB", {
    value: new IDBFactory(),
    configurable: true,
  });
  sessionStorage.clear();
});
describe("IndexedDB recovery storage", () => {
  it("request success followed by transaction abort is not a durable write", async () => {
    const storage = createRecoveryStorage();
    const original = IDBObjectStore.prototype.add;
    const spy = vi
      .spyOn(IDBObjectStore.prototype, "add")
      .mockImplementation(function (
        this: IDBObjectStore,
        ...args: Parameters<typeof original>
      ) {
        const request = original.apply(this, args);
        request.addEventListener("success", () => this.transaction.abort());
        return request;
      });
    try {
      await expect(storage.insert(makeRecord())).rejects.toThrow();
    } finally {
      spy.mockRestore();
    }
    expect((await storage.list("actor")).records).toEqual([]);
  });
  it("persists independent contexts and rejects stale replacement", async () => {
    const storage = createRecoveryStorage();
    const a = makeRecord(),
      b = makeRecord("b");
    await storage.insert(a);
    await storage.insert(b);
    await storage.replace(
      {
        ...a,
        revision: 2,
        blocks: ["access"],
        requiresAccessConfirmation: true,
      },
      1,
    );
    await expect(storage.replace({ ...a, revision: 2 }, 1)).rejects.toThrow();
    const loaded = await createRecoveryStorage().list("actor");
    expect(loaded.records).toHaveLength(2);
    expect(loaded.records.find((r) => r.key === a.key)?.blocks).toEqual([
      "access",
    ]);
    expect((await storage.list("other")).records).toEqual([]);
  });
  it("does not overwrite a command or delete a different revision", async () => {
    const storage = createRecoveryStorage();
    const a = makeRecord();
    await storage.insert(a);
    await expect(storage.insert(a)).rejects.toThrow();
    await expect(storage.remove(a.key, "wrong-command", 1)).rejects.toThrow();
    await expect(storage.remove(a.key, commandId, 2)).rejects.toThrow();
    expect((await storage.list("actor")).records).toHaveLength(1);
    await storage.remove(a.key, commandId, 1);
    expect((await storage.list("actor")).records).toEqual([]);
  });
  it("does not resurrect a completed imported command after interrupted legacy cleanup", async () => {
    const storage = createRecoveryStorage();
    const a = makeRecord();
    expect(await storage.importLegacy(a, "payload")).toBe("imported");
    await storage.remove(a.key, commandId, 1);
    expect(await storage.importLegacy(a, "payload")).toBe("already-imported");
    expect((await storage.list("actor")).records).toEqual([]);
    await expect(
      storage.importLegacy(a, "different-payload"),
    ).rejects.toThrow();
  });
});
