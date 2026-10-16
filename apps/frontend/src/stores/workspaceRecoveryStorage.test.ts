import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  readRecoveryRecord,
  writeRecoveryRecord,
  removeRecoveryRecord,
} from "./workspaceRecoveryStorage";
import {
  candidate,
  commandId,
  target,
  successFixture,
} from "@/test/workspaceEditFixture";
const command = {
  actorId: "actor",
  target,
  request: { commandId, draftVersionToken: "old", geometry: candidate },
};
describe("recovery storage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });
  it("roundtrips unknown and success without exposing another actor", () => {
    expect(
      writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" }),
    ).toBe(true);
    expect(readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { command, state: "unknown" },
    });
    expect(readRecoveryRecord("other")).toEqual({ kind: "empty" });
    expect(
      writeRecoveryRecord({
        schemaVersion: 1,
        command,
        state: "succeeded",
        result: successFixture(),
      }),
    ).toBe(true);
    expect(readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { state: "succeeded" },
    });
  });
  it("does not overwrite or remove another command", () => {
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    expect(removeRecoveryRecord("actor", "other")).toBe(false);
    expect(
      writeRecoveryRecord({
        schemaVersion: 1,
        command: {
          ...command,
          request: {
            ...command.request,
            commandId: "22222222-2222-4222-8222-222222222222",
          },
        },
        state: "unknown",
      }),
    ).toBe(false);
  });
  it("retains corrupt data and reports unavailable storage", () => {
    sessionStorage.setItem("geoservice:workspace-recovery:v1:actor", "{broken");
    expect(readRecoveryRecord("actor").kind).toBe("invalid");
    expect(sessionStorage.length).toBe(1);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    expect(
      writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" }),
    ).toBe(false);
  });
  it("roundtrips rejection and access block without treating them as success", () => {
    const error = {
      status: 409,
      code: "DRAFT_VERSION_STALE",
      message: "Устарело",
      correlationId: "c",
    };
    expect(
      writeRecoveryRecord({
        schemaVersion: 1,
        command,
        state: "rejected",
        error,
        needsReadback: true,
      }),
    ).toBe(true);
    expect(readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { state: "rejected", error, needsReadback: true },
    });
    expect(
      writeRecoveryRecord({
        schemaVersion: 1,
        command,
        state: "blocked",
        reason: "access",
      }),
    ).toBe(true);
    expect(readRecoveryRecord("actor")).toMatchObject({
      kind: "record",
      record: { state: "blocked" },
    });
  });
  it("rejects unsupported versions and an actor mismatch without deleting evidence", () => {
    const key = "geoservice:workspace-recovery:v1:actor";
    for (const value of [
      { schemaVersion: 2, command, state: "unknown" },
      {
        schemaVersion: 1,
        command: { ...command, actorId: "other" },
        state: "unknown",
      },
    ]) {
      sessionStorage.setItem(key, JSON.stringify(value));
      expect(readRecoveryRecord("actor")).toEqual({ kind: "invalid" });
      expect(sessionStorage.getItem(key)).not.toBeNull();
    }
  });
  it("reports inaccessible reads and failed cleanup", () => {
    writeRecoveryRecord({ schemaVersion: 1, command, state: "unknown" });
    const remove = vi
      .spyOn(Storage.prototype, "removeItem")
      .mockImplementation(() => {
        throw new Error("denied");
      });
    expect(removeRecoveryRecord("actor", commandId)).toBe(false);
    remove.mockRestore();
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("denied");
    });
    expect(readRecoveryRecord("actor")).toEqual({ kind: "unavailable" });
  });
});
