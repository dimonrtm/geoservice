import { useWorkspaceRecoveryStore } from "@/stores/workspaceRecovery";
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { markRaw } from "vue";
import type { Map as LibreMap } from "maplibre-gl";
import type { FeatureCollection } from "geojson";
import WorkspaceLineInteraction from "./WorkspaceLineInteraction.vue";
import WorkspaceEditCommands from "./WorkspaceEditCommands.vue";
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
    getSource: (id: string) => ({
      setData: (data: FeatureCollection) => {
        if (id === "workspace:features") rendered = structuredClone(data);
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
const wrappers: Array<{ unmount(): void }> = [];
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute("open");
  };
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
  it("revert confirmation removes marker and prevents map edits without cancelling consent", async () => {
    const { store, click, drag } = app();
    await click(target.featureId);
    await drag([5, 6]);
    store.workspace!.workOrder.editVersion.hasPersistedChangeSet = true;
    store.workspace!.workOrder.editVersion.changeSet = {
      featureId: target.featureId,
      vertexIndex: 1,
      operation: "updated",
      baselineGeometry: {
        type: "LineString",
        coordinates: [
          [1, 1],
          [5, 4],
          [9, 1],
        ],
      },
    };
    expect(store.beginRevert()).toBe("resolve-dirty");
    await flushPromises();
    expect(doubles.markers[doubles.markers.length - 1]?.removed).toBe(true);
    const draft = JSON.stringify(store.localDraft);
    await click("line-2");
    await drag([5, 7]);
    expect(JSON.stringify(store.localDraft)).toBe(draft);
    expect(store.revertConfirmation?.phase).toBe("resolve-dirty");
  });
  it("panel Cancel keeps marker at persisted current and Save clears it", async () => {
    const { store, click, drag } = app();
    const panel = mount(WorkspaceEditCommands, { attachTo: document.body });
    wrappers.push(panel);
    await click(target.featureId);
    await drag([5, 6]);
    await panel.get('[data-test="cancel-edit"]').trigger("click");
    expect(store.localDraft?.featureId).toBe(target.featureId);
    expect(doubles.markers[doubles.markers.length - 1]?.xy).toEqual([5, 5]);
    expect(doubles.markers[doubles.markers.length - 1]?.removed).toBe(false);
    expect(doubles.save).not.toHaveBeenCalled();
    store.localDraft = null;
    store.localPhase = "idle";
    await flushPromises();
    expect(doubles.markers[doubles.markers.length - 1]?.removed).toBe(true);
    panel.unmount();
  });
  it("opens a native modal and restores fallback focus after Escape", async () => {
    const { click, drag, wrapper, store } = app();
    const heading = document.createElement("h2");
    heading.id = "workspace-edit-heading";
    heading.tabIndex = -1;
    document.body.append(heading);
    const original = document.createElement("button");
    document.body.append(original);
    original.focus();
    await click(target.featureId);
    await drag([5, 6]);
    await click();
    expect(wrapper.get("dialog").attributes("open")).toBeDefined();
    original.remove();
    const keep = wrapper.get('[data-test="keep-draft"]');
    await keep.trigger("keydown", { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(
      wrapper.get('[data-test="discard-draft"]').element,
    );
    await wrapper.get("dialog").trigger("cancel");
    await flushPromises();
    expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([5, 6]);
    expect(document.activeElement).toBe(heading);
  });
  it("closes the modal before restoring focus after affirmative discard", async () => {
    const { click, drag, wrapper } = app();
    await click(target.featureId);
    await drag([5, 6]);
    await click();
    const dialog = wrapper.get("dialog").element as HTMLDialogElement;
    await wrapper.get('[data-test="discard-draft"]').trigger("click");
    // An open detached modal cannot reliably restore browser focus to its background.
    expect(dialog.open).toBe(false);
  });
  it.each(["stale", "unknown", "reading-current"] as const)(
    "prevents map cancellation and movement in %s",
    async (phase) => {
      const { click, drag, wrapper, store } = app();
      await click(target.featureId);
      await drag([5, 6]);
      store.localPhase = phase;
      await flushPromises();
      await click();
      expect(wrapper.find('[data-test="discard-draft"]').exists()).toBe(false);
      expect(store.localDraft?.candidateGeometry.coordinates[1]).toEqual([
        5, 6,
      ]);
      expect(doubles.markers[doubles.markers.length - 1]?.removed).toBe(true);
    },
  );
  it("blocks marker editing on storage failure before PUT", async () => {
    const { click, drag, store } = app();
    await click(target.featureId);
    await drag([5, 6]);
    useWorkspaceRecoveryStore().storageError = "quota";
    await flushPromises();
    expect(doubles.markers[doubles.markers.length - 1]?.removed).toBe(true);
    expect(store.moveLocalVertex([5, 7])).toBe(false);
  });
  it("restores clicking after a drag interrupted by a temporary recovery phase", async () => {
    const { click, store } = app();
    await click(target.featureId);
    doubles.markers[0]!.handlers.dragstart!();
    store.localPhase = "reading-current";
    await flushPromises();
    store.localPhase = "editing";
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
