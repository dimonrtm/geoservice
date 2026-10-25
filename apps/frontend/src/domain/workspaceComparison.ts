import type { LineStringXY } from "@/contracts/workspace-edit";
export function comparisonRows(
  source: LineStringXY | null,
  candidate: LineStringXY,
  current: LineStringXY | null,
) {
  return Array.from(
    {
      length: Math.max(
        source?.coordinates.length ?? 0,
        candidate.coordinates.length,
        current?.coordinates.length ?? 0,
      ),
    },
    (_, index) => ({
      index,
      source: source?.coordinates[index] ?? null,
      candidate: candidate.coordinates[index] ?? null,
      current: current?.coordinates[index] ?? null,
    }),
  );
}
