import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { useMapInstance } from "./useMapInstance";

const state = vi.hoisted(() => ({ ticks: [] as (() => void)[] }));
vi.mock("vue", async (original) => ({
  ...(await original<typeof import("vue")>()),
  nextTick: () => new Promise<void>((resolve) => state.ticks.push(resolve)),
}));

const maps = vi.hoisted(() => ({ instances: [] as FakeMap[] }));
class FakeMap {
  removed = false;
  afterRemove: string[] = [];
  handlers = new Set<() => unknown>();
  addControl = vi.fn();
  resize = vi.fn(() => {
    if (this.removed) this.afterRemove.push("resize");
  });
  remove = vi.fn(() => {
    this.removed = true;
  });
  on = vi.fn((_event: string, handler: () => unknown) => {
    if (this.removed) this.afterRemove.push("on");
    this.handlers.add(handler);
    return this;
  });
  once = vi.fn((_event: string, handler: () => unknown) => {
    if (this.removed) this.afterRemove.push("once");
    this.handlers.add(handler);
    return this;
  });
  off = vi.fn((_event: string, handler: () => unknown) => {
    if (this.removed) this.afterRemove.push("off");
    this.handlers.delete(handler);
    return this;
  });
  fireLoad() {
    for (const handler of [...this.handlers]) void handler();
  }
}
vi.mock("maplibre-gl", () => ({
  Map: class {
    constructor() {
      const map = new FakeMap();
      maps.instances.push(map);
      return map;
    }
  },
  NavigationControl: class {},
}));

async function microtasks() {
  for (let i = 0; i < 12; i++) await Promise.resolve();
}
async function tick() {
  const callbacks = state.ticks.splice(0);
  callbacks.forEach((done) => done());
  await microtasks();
}
function start() {
  const api = useMapInstance(ref(document.createElement("div")));
  const creation = api.createMap();
  const map = maps.instances.slice(-1)[0]!;
  return { api, creation, map };
}

describe("useMapInstance lifecycle", () => {
  it.each(["initial", "load"])(
    "rejects_resize_failure_on_%s_tick",
    async (stage) => {
      const { api, creation, map } = start();
      const error = new Error("resize failed");
      const result = creation.catch((reason: unknown) => reason);
      if (stage === "load") {
        await tick();
        map.fireLoad();
      }
      map.resize.mockImplementationOnce(() => {
        throw error;
      });
      await tick();
      expect(await result).toBe(error);
      expect(map.handlers.size).toBe(0);
      api.destroyMap();
      expect(map.afterRemove).toEqual([]);
    },
  );

  beforeEach(() => {
    state.ticks = [];
    maps.instances = [];
  });

  it("cancels_before_initial_tick", async () => {
    const { api, creation, map } = start();
    let result: unknown = "pending";
    void creation.then((value) => {
      result = value;
    });
    api.destroyMap();
    await tick();
    expect(map.afterRemove).toEqual([]);
    expect(result).toBeNull();
  });

  it("cancels_waiting_for_load", async () => {
    const { api, creation, map } = start();
    await tick();
    const callback = [...map.handlers][0]!;
    let result: unknown = "pending";
    void creation.then((value) => {
      result = value;
    });
    api.destroyMap();
    await microtasks();
    expect(result).toBeNull();
    expect(map.handlers.size).toBe(0);
    expect(map.off).toHaveBeenCalledWith("load", callback);
    void callback();
    await tick();
    expect(map.afterRemove).toEqual([]);
  });

  it("cancels_inside_load_tick", async () => {
    const { api, creation, map } = start();
    await tick();
    map.fireLoad();
    api.destroyMap();
    await tick();
    expect(map.afterRemove).toEqual([]);
    expect(await creation).toBeNull();
  });

  it("captures_load_before_initial_tick", async () => {
    const { api, creation, map } = start();
    let result: unknown = "pending";
    void creation.then((value) => {
      result = value;
    });
    map.fireLoad();
    await tick();
    await tick();
    expect(result).toBe(map);
    api.destroyMap();
  });

  it("ignores_old_start_after_recreate", async () => {
    const { api, creation, map: oldMap } = start();
    await tick();
    const oldCallback = [...oldMap.handlers][0]!;
    api.destroyMap();
    const nextCreation = api.createMap();
    const newMap = maps.instances.slice(-1)[0]!;
    void oldCallback();
    await tick();
    newMap.fireLoad();
    await tick();
    expect(oldMap.afterRemove).toEqual([]);
    expect(await creation).toBeNull();
    expect(await nextCreation).toBe(newMap);
    expect(api.map.value).toBe(newMap);
    api.destroyMap();
  });

  it("returns_live_map_after_load_and_destroy_is_idempotent", async () => {
    const { api, creation, map } = start();
    await tick();
    expect(map.resize).toHaveBeenCalled();
    map.fireLoad();
    await tick();
    expect(await creation).toBe(map);
    expect(map.resize).toHaveBeenCalledTimes(2);
    api.destroyMap();
    api.destroyMap();
    expect(map.remove).toHaveBeenCalledTimes(1);
    expect(api.map.value).toBeNull();
    expect(map.afterRemove).toEqual([]);
  });
});
