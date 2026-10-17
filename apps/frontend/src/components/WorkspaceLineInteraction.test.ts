import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { markRaw } from "vue";
import type { Map as LibreMap } from "maplibre-gl";
import type { FeatureCollection } from "geojson";
import WorkspaceLineInteraction from "./WorkspaceLineInteraction.vue";
import { useWorkOrdersStore } from "@/stores/workOrders";
import { useAuthStore } from "@/stores/auth";
import { workspaceFixture, target } from "@/test/workspaceEditFixture";

const doubles = vi.hoisted(() => ({
  markers: [] as Array<{
    xy: [number, number];
    removed: boolean;
    handlers: Record<string, () => void>;
    setLngLat(xy: [number, number]): unknown;
  }>,
  save: vi.fn(),
}));
vi.mock("@/api/workOrders", () => ({ saveFeatureGeometry: doubles.save }));
vi.mock("maplibre-gl", () => ({
  Marker: class {
    xy: [number, number] = [0, 0];
    removed = false;
    handlers: Record<string, () => void> = {};
    constructor() {
      doubles.markers.push(this);
    }
    setLngLat(xy: [number, number]) {
      this.xy = [...xy];
      return this;
    }
    getLngLat() {
      return { lng: this.xy[0], lat: this.xy[1] };
    }
    addTo() {
      return this;
    }
    on(name: string, handler: () => void) {
      this.handlers[name] = handler;
      return {
        unsubscribe: () => {
          delete this.handlers[name];
        },
      };
    }
    off(name: string) {
      delete this.handlers[name];
      return this;
    }
    remove() {
      this.removed = true;
      return this;
    }
    setDraggable() {
      return this;
    }
  },
}));

function setup() {
  const pinia = createPinia();
  setActivePinia(pinia);
  const auth = useAuthStore();
  auth.token = "test";
  auth.user = { id: "actor", email: "editor@example.local", role: "editor" };
  const store = useWorkOrdersStore();
  const ws = workspaceFixture();
  ws.workOrder.scope.aoi.geometry = {
    type: "Polygon",
    coordinates: [
      [
        [0, 0],
        [10, 0],
        [10, 10],
        [0, 10],
        [0, 0],
      ],
    ],
  };
  const first = ws.workOrder.editVersion.features.features[0]!;
  first.geometry = {
    type: "LineString",
    coordinates: [
      [1, 1],
      [5, 5],
      [9, 1],
    ],
  };
  first.properties = {
    featureType: "line",
    operation: "unchanged",
    assetCode: "L-003",
  };
  ws.workOrder.editVersion.features.features.push(
    {
      ...structuredClone(first),
      id: "line-2",
      properties: { ...first.properties, assetCode: "L-004" },
    },
    {
      type: "Feature",
      id: "point",
      properties: { featureType: "device", operation: "unchanged" },
      geometry: { type: "Point", coordinates: [5, 5] },
    },
  );
  store.workspace = ws;
  store.selectedWorkOrderId = store.openedWorkOrderId = target.workOrderId;
  store.openedEditVersionId = target.editVersionId;
  const handlers = new Map<string, (event: unknown) => void>();
  let hits: string[] = [];
  let rendered: FeatureCollection | undefined;
  const map = markRaw({
    on: (name: string, fn: (event: unknown) => void) => handlers.set(name, fn),
    off: (name: string) => handlers.delete(name),
    queryRenderedFeatures: () => hits.map((id) => ({ id })),
    getLayer: () => ({}),
    getSource: () => ({
      setData: (data: FeatureCollection) => {
        rendered = structuredClone(data);
      },
    }),
    getCanvas: () => document.createElement("canvas"),
  }) as unknown as LibreMap;
  const wrapper = mount(WorkspaceLineInteraction, {
    props: { map, workspace: store.workspace },
    global: { plugins: [pinia] },
    attachTo: document.body,
  });
  const click = async (...ids: string[]) => {
    hits = ids;
    handlers.get("click")?.({
      point: { x: 50, y: 50 },
      originalEvent: { target: document.createElement("canvas") },
    });
    await flushPromises();
  };
  const drag = async (xy: [number, number]) => {
    const marker = doubles.markers[doubles.markers.length - 1]!;
    marker.setLngLat(xy);
    marker.handlers.drag?.();
    await flushPromises();
  };
  return { wrapper, store, click, drag, handlers, rendered: () => rendered };
}
const wrappers: Array<ReturnType<typeof setup>["wrapper"]> = [];
beforeEach(() => {
  doubles.markers.length = 0;
  vi.clearAllMocks();
  sessionStorage.clear();
});
afterEach(() => {
  wrappers.splice(0).forEach((wrapper) => wrapper.unmount());
  document.body.innerHTML = "";
});
function app() {
  const result = setup();
  wrappers.push(result.wrapper);
  return result;
}

describe("workspace line interaction", () => {
  it("restores clicking after a drag interrupted by a temporary recovery phase", async () => {
    const { click, store } = app();
    await click(target.featureId);
    doubles.markers[0]!.handlers.dragstart!();
    store.phase = "reading-current";
    await flushPromises();
    store.phase = "editing";
    await flushPromises();
    await click();
    expect(store.localDraft).toBeNull();
  });
  it("moves keyboard focus from the candidate list into the discard dialog", async () => {
    const { click, drag, wrapper } = app();
    await click(target.featureId);
    await drag([5, 6]);
    await click(target.featureId, "line-2");
    const option = wrapper.findAll('[data-test="line-option"]')[1]!;
    (option.element as HTMLButtonElement).focus();
    await option.trigger("click");
    await flushPromises();
    expect(document.activeElement).toBe(
      wrapper.get('[data-test="keep-draft"]').element,
    );
    await wrapper
      .get('[data-test="keep-draft"]')
      .trigger("keydown", { key: "Escape" });
    expect(wrapper.find('[data-test="discard-draft"]').exists()).toBe(false);
  });
  it("selects a line, renders only local changes and holds the last valid position until reentry", async () => {
    const { store, click, drag, rendered, wrapper } = app();
    const before = JSON.stringify(store.workspace);
    await click(target.featureId);
    expect(store.localDraft?.vertexIndex).toBe(1);
    expect(doubles.markers).toHaveLength(1);
    await drag([5, 6]);
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([5, 6]);
    expect(rendered()?.features[0]?.geometry).toMatchObject({
      coordinates: [
        [1, 1],
        [5, 6],
        [9, 1],
      ],
    });
    await drag([5, 11]);
    expect(doubles.markers[0]!.xy).toEqual([5, 6]);
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([5, 6]);
    expect(wrapper.get('[role="status"]').text()).toContain("область");
    await drag([5, 7]);
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([5, 7]);
    expect(JSON.stringify(store.workspace)).toBe(before);
    expect(doubles.save).not.toHaveBeenCalled();
  });
  it("deduplicates hits and asks which overlapping line to select", async () => {
    const { click, store, wrapper } = app();
    await click(target.featureId, target.featureId, "line-2");
    expect(store.localDraft).toBeNull();
    expect(wrapper.findAll('[data-test="line-option"]')).toHaveLength(2);
    await wrapper.findAll('[data-test="line-option"]')[1]!.trigger("click");
    expect(store.localDraft?.featureId).toBe("line-2");
  });
  it("clears clean selection, confirms dirty deselection and does not lose rejected cancellation", async () => {
    const { click, drag, store, wrapper } = app();
    await click(target.featureId);
    await click();
    expect(store.localDraft).toBeNull();
    await click(target.featureId);
    await drag([5, 6]);
    await click();
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true);
    await wrapper.get('[data-test="keep-draft"]').trigger("click");
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([5, 6]);
    await click();
    await wrapper.get('[data-test="discard-draft"]').trigger("click");
    expect(store.localDraft).toBeNull();
    expect(doubles.markers[doubles.markers.length - 1]!.removed).toBe(true);
  });
  it("confirms switching targets but preserves selection for ineligible hits", async () => {
    const { click, drag, store, wrapper } = app();
    await click(target.featureId);
    await drag([5, 6]);
    await click("point");
    expect(store.localDraft?.featureId).toBe(target.featureId);
    expect(wrapper.get('[role="status"]').text()).not.toBe("");
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
    await click("line-2");
    await wrapper.get('[data-test="discard-draft"]').trigger("click");
    expect(store.localDraft?.featureId).toBe("line-2");
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([5, 5]);
  });
  it("preserves candidate on reselection and removes handles/listeners on access loss and unmount", async () => {
    const { click, drag, store, wrapper, handlers } = app();
    await click(target.featureId);
    await drag([5, 6]);
    await click(target.featureId);
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([5, 6]);
    const callback = doubles.markers[0]!.handlers.drag!;
    store.reset();
    await flushPromises();
    callback();
    expect(store.localDraft).toBeNull();
    expect(doubles.markers[0]!.removed).toBe(true);
    wrapper.unmount();
    expect(handlers.has("click")).toBe(false);
  });
});
