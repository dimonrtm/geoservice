import { afterEach, expect, it, vi } from "vitest";
import * as saves from "@/api/edit_version/editVersions";
import * as snapshots from "@/composables/edit_version/useEditVersionEditor";
import { SnapshotReadFailure } from "@/composables/edit_version/readEditVersionSnapshot";
import {
  candidate,
  commandId,
  successFixture,
  target,
} from "@/test/workspaceEditFixture";
import * as migration from "./workspaceRecoveryMigration";
import * as storageModule from "./workspaceRecoveryStorage";
import { createRecoveryIO } from "./createRecoveryIO";

afterEach(() => vi.restoreAllMocks());

it("finishes legacy migration before listing the same actor's records", async () => {
  const storage = storageModule.createRecoveryStorage();
  vi.spyOn(storageModule, "createRecoveryStorage").mockReturnValue(storage);
  const list = vi
    .spyOn(storage, "list")
    .mockResolvedValue({ records: [], invalid: [] });
  let finish!: () => void;
  const migrate = vi
    .spyOn(migration, "migrateLegacyRecovery")
    .mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          finish = resolve;
        }),
    );
  const io = createRecoveryIO();
  const loading = io.loadActor("editor");
  expect(migrate).toHaveBeenCalledWith("editor", storage);
  expect(list).not.toHaveBeenCalled();
  finish();
  await loading;
  expect(list).toHaveBeenCalledWith("editor");

  list.mockClear();
  migrate.mockRejectedValueOnce(new Error("migration failed"));
  await expect(io.loadActor("editor")).rejects.toThrow("migration failed");
  expect(list).not.toHaveBeenCalled();
});

it("classifies a receipt for a different command as a protocol block", async () => {
  vi.spyOn(saves, "saveFeatureGeometry").mockResolvedValue(
    successFixture("other"),
  );
  const command = {
    actorId: "editor",
    target,
    request: { commandId, draftVersionToken: "a", geometry: candidate },
  };
  expect(await createRecoveryIO().send(command, false)).toMatchObject({
    kind: "blocked",
    reason: "protocol",
  });
});

it("distinguishes session loss, unavailable context and a failed baseline read", async () => {
  const failure = new SnapshotReadFailure("baseline");
  const fetch = vi.spyOn(snapshots, "readEditVersionSnapshot");
  const io = createRecoveryIO();
  const read = () =>
    io.read(
      { actorId: "editor", ...target },
      new AbortController().signal,
      {},
      (request) => request(),
    );
  fetch.mockRejectedValueOnce({
    isAxiosError: true,
    response: {
      status: 403,
      data: { code: "ROLE_NOT_ALLOWED", message: "denied" },
    },
  });
  expect(await read()).toEqual({ kind: "session" });
  fetch.mockRejectedValueOnce({
    isAxiosError: true,
    response: { status: 404 },
  });
  expect(await read()).toEqual({ kind: "access" });
  fetch.mockRejectedValueOnce(failure);
  expect(await read()).toEqual({ kind: "failed", message: failure.message });
});
