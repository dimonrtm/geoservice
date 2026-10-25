import { beforeEach, expect, it } from "vitest";
import { IDBFactory } from "fake-indexeddb";
import { createRecoveryStorage } from "./workspaceRecoveryStorage";
import { migrateLegacyRecovery } from "./workspaceRecoveryMigration";
import {
  candidate,
  commandId,
  successFixture,
  target,
} from "@/test/workspaceEditFixture";
beforeEach(() => {
  Object.defineProperty(globalThis, "indexedDB", {
    value: new IDBFactory(),
    configurable: true,
  });
  sessionStorage.clear();
});
it("imports blocked success without inventing a source or losing known outcome", async () => {
  sessionStorage.setItem(
    "geoservice:workspace-recovery:v1:actor",
    JSON.stringify({
      schemaVersion: 1,
      command: {
        actorId: "actor",
        target,
        request: { commandId, draftVersionToken: "old", geometry: candidate },
      },
      state: "blocked",
      reason: "access",
      result: successFixture(),
    }),
  );
  const storage = createRecoveryStorage();
  await migrateLegacyRecovery("actor", storage);
  const { records } = await storage.list("actor");
  expect(records[0]).toMatchObject({
    source: null,
    outcome: { kind: "succeeded" },
    blocks: ["access"],
    requiresAccessConfirmation: true,
  });
  expect(records[0]?.command.request.draftVersionToken).toBe("old");
  expect(
    sessionStorage.getItem("geoservice:workspace-recovery:v1:actor"),
  ).toBeNull();
  await migrateLegacyRecovery("actor", storage);
  expect((await storage.list("actor")).records).toHaveLength(1);
});
it("retains invalid legacy records instead of deleting them", async () => {
  sessionStorage.setItem("geoservice:workspace-recovery:v1:actor", "broken");
  await expect(
    migrateLegacyRecovery("actor", createRecoveryStorage()),
  ).rejects.toThrow();
  expect(sessionStorage.getItem("geoservice:workspace-recovery:v1:actor")).toBe(
    "broken",
  );
});
