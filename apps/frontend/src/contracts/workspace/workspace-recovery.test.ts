import { describe, expect, it } from "vitest";
import {
  candidate,
  commandId,
  geometry,
  successFixture,
  target,
} from "@/test/workspaceEditFixture";
import {
  createRecoveryRecord,
  parseRecoveryRecord,
  recoveryKey,
} from "./workspace-recovery";

function command() {
  return {
    actorId: "actor",
    target: { ...target },
    request: {
      commandId,
      draftVersionToken: "revision-a",
      geometry: structuredClone(candidate),
    },
  };
}
describe("recovery records", () => {
  it("copies the sent intent and its source before the caller can change them", () => {
    const input = command();
    const source = { geometry: structuredClone(geometry), vertexIndex: 1 };
    const saved = createRecoveryRecord(input, source);
    input.request.geometry.coordinates[1] = [0, 0];
    source.geometry.coordinates[1] = [0, 0];
    expect(saved.command.request.geometry.coordinates[1]).toEqual([65.1, 44.2]);
    expect(saved.source?.geometry.coordinates[1]).toEqual([65.1, 44.1]);
    expect(saved.key).toBe('["actor","wo-1","ev-1"]');
  });
  it("rejects actor, context key and geometry identity mismatches", () => {
    const record = createRecoveryRecord(command(), {
      geometry,
      vertexIndex: 1,
    });
    expect(() => parseRecoveryRecord(record, "other")).toThrow();
    expect(() =>
      parseRecoveryRecord(
        {
          ...record,
          key: recoveryKey({
            actorId: "actor",
            workOrderId: "other",
            editVersionId: "ev-1",
          }),
        },
        "actor",
      ),
    ).toThrow();
    expect(() =>
      parseRecoveryRecord(
        { ...record, source: { geometry, vertexIndex: 0 } },
        "actor",
      ),
    ).toThrow();
  });
  it("retains a terminal outcome independently of access suspension", () => {
    const record = createRecoveryRecord(command(), {
      geometry,
      vertexIndex: 1,
    });
    const parsed = parseRecoveryRecord(
      {
        ...record,
        outcome: { kind: "succeeded", result: successFixture() },
        blocks: ["access"],
        requiresAccessConfirmation: true,
      },
      "actor",
    );
    expect(parsed.outcome).toMatchObject({
      kind: "succeeded",
      result: { commandId },
    });
    expect(parsed.requiresAccessConfirmation).toBe(true);
    expect(parsed.command.request.draftVersionToken).toBe("revision-a");
  });
});

it("rejects inconsistent outcome/readback flags before a stale record could skip current GET", () => {
  const r = createRecoveryRecord(command(), { geometry, vertexIndex: 1 });
  expect(() =>
    parseRecoveryRecord(
      {
        ...r,
        outcome: {
          kind: "rejected",
          error: {
            code: "DRAFT_VERSION_STALE",
            status: 409,
            message: "stale",
            correlationId: null,
          },
          needsReadback: true,
        },
        readbackRequired: false,
      },
      "actor",
    ),
  ).toThrow();
});
