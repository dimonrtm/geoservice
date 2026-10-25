import { beforeEach } from "vitest";
import { IDBFactory } from "fake-indexeddb";
beforeEach(() => {
  Object.defineProperty(globalThis, "indexedDB", {
    value: new IDBFactory(),
    configurable: true,
  });
});
