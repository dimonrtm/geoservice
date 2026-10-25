import { expect, vi } from "vitest";
import type { useWorkOrdersStore } from "@/stores/workOrders";
import { useWorkspaceRecoveryStore } from "@/stores/workspaceRecovery";
import { createRecoveryStorage } from "@/stores/workspaceRecoveryStorage";
export async function settle(store: ReturnType<typeof useWorkOrdersStore>) {
  await vi.waitFor(() => {
    expect(store.phase).not.toBe("sending");
    if (store.phase === "reading-current")
      expect(store.readbackError).toBeTruthy();
  });
}
export async function readPersisted(actor: string) {
  const r = (await createRecoveryStorage().list(actor)).records[0];
  if (!r) return { kind: "empty" };
  const record = {
    schemaVersion: 1,
    command: r.command,
    ...(r.outcome.kind === "succeeded" ? { result: r.outcome.result } : {}),
    ...(r.outcome.kind === "rejected"
      ? { error: r.outcome.error, needsReadback: r.readbackRequired }
      : {}),
    state: r.blocks.length ? "blocked" : r.outcome.kind,
    ...(r.blocks.includes("access") ? { reason: "access" } : {}),
  };
  return { kind: "record", record };
}
export function stopRecovery() {
  useWorkspaceRecoveryStore().stopRuntime();
}

// Wait for native IndexedDB tasks without advancing virtual retry deadlines.
export async function storageTurn() {
  await new Promise<void>((resolve) =>
    import("node:timers").then(({ setImmediate }) => setImmediate(resolve)),
  );
}
export async function until(check: () => boolean) {
  for (let i = 0; i < 1000; i++) {
    if (check()) return;
    await storageTurn();
  }
  expect(check()).toBe(true);
}
