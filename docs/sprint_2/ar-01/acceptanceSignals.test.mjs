import assert from "node:assert/strict";
import { test } from "node:test";
import * as lifecycle from "./acceptanceResult.mjs";

test(
  "absent signal fails acceptance and releases held routes before cleanup",
  { timeout: 1000 },
  async () => {
    const result = { cases: { first: { passed: true } } };
    let routeFinished = false;
    let closed = false;
    let saved;
    let route;

    await assert.rejects(
      lifecycle.recordAcceptanceResult(
        result,
        () =>
          lifecycle.withAcceptanceSignals(
            async (signals) => {
              const barrier = signals.barrier();
              route = barrier.promise.then(() => {
                routeFinished = true;
              });
              await signals.signal().wait();
            },
            { timeoutMs: 10 },
          ),
        {
          close: async () => {
            await route;
            assert.equal(routeFinished, true);
            closed = true;
          },
          persist: async (value) => {
            saved = structuredClone(value);
          },
        },
      ),
      (error) => {
        assert.equal(
          error.safeMessage,
          "Истёк срок ожидания сигнала browser acceptance",
        );
        assert.equal(error.message, error.safeMessage);
        return true;
      },
    );

    assert.equal(closed, true);
    assert.equal(saved.passed, false);
    assert.equal(saved.completed, false);
    assert.equal(saved.aborted, true);
  },
);

test(
  "resolved signal retains its value and successful action releases barriers",
  { timeout: 1000 },
  async () => {
    let route;
    const value = await lifecycle.withAcceptanceSignals(async (signals) => {
      const barrier = signals.barrier();
      route = barrier.promise.then(() => "released");
      const signal = signals.signal();
      signal.resolve(42);
      return signal.wait();
    });
    assert.equal(value, 42);
    assert.equal(await route, "released");
  },
);

test(
  "action failure releases every barrier and preserves the original failure",
  { timeout: 1000 },
  async () => {
    const failure = new Error("action failed");
    let routes;
    await assert.rejects(
      lifecycle.withAcceptanceSignals(async (signals) => {
        routes = [signals.barrier(), signals.barrier()].map(
          (barrier) => barrier.promise,
        );
        throw failure;
      }),
      (error) => error === failure,
    );
    assert.equal((await Promise.all(routes)).length, 2);
  },
);
