import { describe, expect, it } from "vitest";

import { getRoleLabel, isEditorRole } from "@/domain/authRole";

describe("auth role", () => {
  it("returns Russian labels for both workflow roles", () => {
    expect(getRoleLabel("editor")).toBe("Редактор");
    expect(getRoleLabel("reviewer")).toBe("Рецензент");
  });

  it("allows editor workspace only for Editor", () => {
    expect(isEditorRole("editor")).toBe(true);
    expect(isEditorRole("reviewer")).toBe(false);
  });
});
