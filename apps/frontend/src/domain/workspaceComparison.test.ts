import { expect, it } from "vitest";
import { comparisonRows } from "./workspaceComparison";
import { geometry, candidate } from "@/test/workspaceEditFixture";
it("keeps source and candidate separate from newer current and represents legacy missing source", () => {
  const before = JSON.stringify(candidate);
  const rows = comparisonRows(null, candidate, geometry);
  expect(rows[1]).toEqual({
    index: 1,
    source: null,
    candidate: [65.1, 44.2],
    current: [65.1, 44.1],
  });
  expect(JSON.stringify(candidate)).toBe(before);
});
