import { describe, expect, it } from "vitest";
import {
  parseGeometrySaveResult,
  parseWorkspaceResponse,
  ProtocolError,
} from "./workspace-edit";
import {
  commandId,
  successFixture,
  target,
  workspaceFixture,
} from "@/test/workspaceEditFixture";

describe("workspace contracts", () => {
  it("accepts complete canonical responses and opaque tokens", () => {
    expect(
      parseGeometrySaveResult(successFixture(), target, commandId)
        .draftVersionToken,
    ).toBe("revision-b");
    expect(
      parseWorkspaceResponse(workspaceFixture(), "wo-1", "ev-1").workOrder
        .editVersion.changeSet,
    ).toBeNull();
    expect(
      parseWorkspaceResponse(workspaceFixture(true), "wo-1", "ev-1").workOrder
        .editVersion.changeSet?.vertexIndex,
    ).toBe(1);
  });
  it("rejects mismatched command or feature", () => {
    expect(() =>
      parseGeometrySaveResult(successFixture("wrong"), target, commandId),
    ).toThrow(ProtocolError);
    const result = successFixture();
    result.updatedFeature.id = "other";
    expect(() => parseGeometrySaveResult(result, target, commandId)).toThrow(
      ProtocolError,
    );
  });
  it("rejects inconsistent summary, missing fields and malformed XY", () => {
    const ws = workspaceFixture();
    ws.workOrder.editVersion.hasPersistedChangeSet = true;
    expect(() => parseWorkspaceResponse(ws, "wo-1", "ev-1")).toThrow(
      ProtocolError,
    );
    const result = successFixture();
    result.updatedFeature.geometry.coordinates[0] = [Infinity, 0];
    expect(() => parseGeometrySaveResult(result, target, commandId)).toThrow(
      ProtocolError,
    );
    expect(() =>
      parseGeometrySaveResult(
        { ...successFixture(), basicValidation: undefined },
        target,
        commandId,
      ),
    ).toThrow(ProtocolError);
  });
});
