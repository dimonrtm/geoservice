import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { HttpError } from "@/api/layers";
import { useEditStore } from "@/stores/edit";

vi.mock("@/api/layers", () => ({
  HttpError: class HttpError extends Error {
    status: number;
    body: unknown;

    constructor(status: number, body: unknown) {
      super();
      this.status = status;
      this.body = body;
    }
  },
  fetchLayerFeatureById: vi.fn(),
  patchLayerFeature: vi.fn(),
  deleteLayerFeature: vi.fn(),
}));

describe("edit store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("starts editing with cloned polygon geometry", () => {
    const store = useEditStore();

    store.startEditing({
      layerId: "layer-1",
      featureId: "feature-1",
      version: 3,
      properties: { name: "Polygon A" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [10, 10],
            [20, 10],
            [20, 20],
            [10, 10],
          ],
        ],
      },
    });

    if (store.edit.mode !== "editing") {
      throw new Error("Store did not enter editing mode");
    }

    expect(store.edit.session.featureId).toBe("feature-1");
    expect(store.edit.dirty).toBe(false);
    expect(store.edit.session.draft.geometry).not.toBeUndefined();
  });

  it("stores validation error for invalid polygon draft", () => {
    const store = useEditStore();

    store.startEditing({
      layerId: "layer-1",
      featureId: "feature-1",
      version: 1,
      properties: {},
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [10, 10],
            [20, 10],
            [20, 20],
            [10, 10],
          ],
        ],
      },
    });

    store.updateDraft({
      properties: {},
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [10, 10],
            [20, 10],
            [20, 20],
            [10, 20],
          ],
        ],
      },
    });

    if (store.edit.mode !== "editing") {
      throw new Error("Store did not remain in editing mode");
    }

    expect(store.edit.lastError).toEqual({
      ok: false,
      code: "RING_NOT_CLOSED",
      message: "Все кольца полигона должны быть замкнутыми",
    });
  });

  it("maps 422 http error into validation state", async () => {
    const store = useEditStore();

    store.startEditing({
      layerId: "layer-1",
      featureId: "feature-1",
      version: 1,
      properties: {},
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [10, 10],
            [20, 10],
            [20, 20],
            [10, 10],
          ],
        ],
      },
    });

    await store.handleHttpError(
      new HttpError(422, { error: "Некорректная геометрия" }),
    );

    if (store.edit.mode !== "editing") {
      throw new Error("Store did not remain in editing mode");
    }

    expect(store.edit.lastError).toEqual({
      ok: false,
      code: "INVALID_COORDINATES",
      message: "Некорректная геометрия",
    });
  });
});
