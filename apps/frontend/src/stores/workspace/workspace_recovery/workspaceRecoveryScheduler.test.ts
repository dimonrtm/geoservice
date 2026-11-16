import { expect, it, vi } from "vitest";
import { createRecoveryScheduler } from "./workspaceRecoveryScheduler";
it("limits HTTP requests, releases slots and does not overlap a context", async () => {
  const scheduler = createRecoveryScheduler(2),
    controller = new AbortController();
  const started: string[] = [];
  const releases: Array<() => void> = [];
  const job = (name: string) =>
    scheduler.run(name, controller.signal, async () => {
      started.push(name);
      await new Promise<void>((r) => releases.push(r));
    });
  const a = job("A"),
    again = job("A"),
    b = job("B"),
    c = job("C");
  await Promise.resolve();
  expect(started).toEqual(["A", "B"]);
  releases[0]!();
  await a;
  await vi.waitFor(() => expect(started).toEqual(["A", "B", "A"]));
  releases[1]!();
  await b;
  await vi.waitFor(() => expect(started).toEqual(["A", "B", "A", "C"]));
  releases[2]!();
  releases[3]!();
  await Promise.all([again, c]);
});
it("does not send queued requests after abort", async () => {
  const scheduler = createRecoveryScheduler(1),
    controller = new AbortController();
  let release!: () => void;
  const first = scheduler.run(
    "A",
    controller.signal,
    () =>
      new Promise<void>((r) => {
        release = r;
      }),
  );
  let sent = false;
  const second = scheduler.run("B", controller.signal, async () => {
    sent = true;
  });
  const rejection = expect(second).rejects.toThrow();
  await Promise.resolve();
  controller.abort();
  release();
  await first;
  await rejection;
  expect(sent).toBe(false);
});
