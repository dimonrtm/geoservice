import { defineStore } from "pinia";
import {
  fetchLayerFeatureById,
  patchLayerFeature,
  deleteLayerFeature,
} from "@/api/layers";
import { HttpError } from "@/api/layers";
import { isVersionMismatchBody } from "@/parsing/complex_errors";
import { isRecord, isString } from "@/parsing/common";

type DraftFeature = {
  properties: Record<string, unknown>;
  geometry: GeoJSON.Polygon;
};
export type EditSession = {
  layerId: string;
  featureId: string;
  version: number;
  draft: DraftFeature;
};
export type EditState =
  | { mode: "idle" }
  | {
      mode: "editing";
      session: EditSession;
      lastError?: EditLastError;
      dirty: boolean;
    };
type ValidationOk = { ok: true; value: GeoJSON.Polygon };
type ValidationError = {
  ok: false;
  code:
    | "INVALID_COORDINATES"
    | "RING_NOT_CLOSED"
    | "RING_TOO_SHORT"
    | "GEOM_NOT_POLYGON";
  message: string;
};
type ValidationResult = ValidationOk | ValidationError;

export type VersionMismatchBody = {
  type: "VERSION_MISMATCH";
  featureId: string;
  requestVersion: number;
  currentVersion: number;
  message: string;
};

export type EditConflictError = {
  kind: "conflict";
  body: VersionMismatchBody;
};

export type EditLastError = ValidationError | EditConflictError;

export const useEditStore = defineStore("edit", {
  state: () => ({
    edit: { mode: "idle" } as EditState,
  }),
  actions: {
    startEditing(featureFromServer: {
      layerId: string;
      featureId: string;
      version: number;
      properties: Record<string, unknown>;
      geometry: GeoJSON.Polygon;
    }): void {
      const draftFeature: DraftFeature = {
        properties: cloneProperties(featureFromServer.properties),
        geometry: cloneGeometry(featureFromServer.geometry),
      };
      const editSession: EditSession = {
        layerId: featureFromServer.layerId,
        featureId: featureFromServer.featureId,
        version: featureFromServer.version,
        draft: draftFeature,
      };
      this.edit = { mode: "editing", session: editSession, dirty: false };
    },
    updateDraft(newDraft: DraftFeature): void {
      if (!this.isEditing()) {
        return;
      }
      const session: EditSession | null = this.sessionOrNull();
      if (!session) {
        return;
      }
      const validateResult = validatePolygon(newDraft.geometry);
      if (!validateResult.ok) {
        const prevDirty =
          this.edit.mode === "editing" ? this.edit.dirty : false;
        this.edit = {
          mode: "editing",
          session: { ...session },
          lastError: validateResult,
          dirty: prevDirty,
        };
      } else {
        this.edit = {
          mode: "editing",
          session: {
            ...session,
            draft: {
              properties: cloneProperties(newDraft.properties),
              geometry: cloneGeometry(newDraft.geometry),
            },
          },
          lastError: undefined,
          dirty: true,
        };
      }
    },
    cancelEditing(): void {
      if (this.isEditing()) {
        this.edit = { mode: "idle" };
      }
    },
    async saveEditing(): Promise<void> {
      if (this.edit.mode !== "editing") {
        return;
      }
      const session: EditSession = this.edit.session;
      if (this.edit.dirty === false) {
        return;
      }
      try {
        const feature = await patchLayerFeature(
          session.layerId,
          session.featureId,
          {
            version: session.version,
            properties: session.draft.properties,
            geometry: session.draft.geometry,
          },
        );
        const draft = {
          properties: cloneProperties(
            feature.properties as Record<string, unknown>,
          ),
          geometry: cloneGeometry(feature.geometry as GeoJSON.Polygon),
        };
        this.edit = {
          ...this.edit,
          session: { ...session, version: feature.version, draft: draft },
          dirty: false,
          lastError: undefined,
        };
      } catch (err: unknown) {
        if (err instanceof HttpError) {
          await this.handleHttpError(err);
        }
      }
    },
    async deleteEditing(): Promise<boolean> {
      if (this.edit.mode !== "editing") {
        return false;
      }
      try {
        await deleteLayerFeature(
          this.edit.session.layerId,
          this.edit.session.featureId,
          { version: this.edit.session.version },
        );
        this.edit = { mode: "idle" };
        return true;
      } catch (err: unknown) {
        if (err instanceof HttpError) {
          await this.handleHttpError(err);
          return this.edit.mode === "idle";
        }
        throw err;
      }
    },
    isEditing(): boolean {
      return this.edit.mode === "editing";
    },
    sessionOrNull(): EditSession | null {
      if (this.edit.mode === "editing") {
        return this.edit.session;
      }
      return null;
    },
    async handleHttpError(err: HttpError): Promise<void> {
      if (this.edit.mode !== "editing") {
        return;
      }
      const status: number = err.status;
      const body: unknown = err.body;
      if (status === 422) {
        if (isRecord(body) && isString(body["error"])) {
          this.edit.lastError = {
            ok: false,
            code: "INVALID_COORDINATES",
            message: body["error"],
          };
        } else {
          this.edit.lastError = {
            ok: false,
            code: "INVALID_COORDINATES",
            message: "ValidationError(422)",
          };
        }
        return;
      }
      if (status === 409) {
        if (isVersionMismatchBody(body)) {
          this.edit.lastError = { kind: "conflict", body: body };
          try {
            const feature = await fetchLayerFeatureById(
              this.edit.session.layerId,
              this.edit.session.featureId,
            );
            this.startEditing({
              layerId: this.edit.session.layerId,
              featureId: feature.id,
              version: feature.version,
              properties: feature.properties as Record<string, unknown>,
              geometry: feature.geometry as GeoJSON.Polygon,
            });
          } catch (err: unknown) {
            if (err instanceof HttpError) {
              if (err.status === 404) {
                this.edit = { mode: "idle" };
                return;
              }
            }
            throw err;
          }
        }
      }
    },
  },
});

function cloneProperties(
  properties: Record<string, unknown>,
): Record<string, unknown> {
  const duplicate: Record<string, unknown> = {};
  for (const key of Object.keys(properties)) {
    duplicate[key] = properties[key];
  }
  return duplicate;
}

function cloneGeometry(geometry: GeoJSON.Polygon): GeoJSON.Polygon {
  const cloneCoordinates: GeoJSON.Position[][] = [];
  for (const ring of geometry.coordinates) {
    const ringClone: GeoJSON.Position[] = [];
    for (const point of ring) {
      const clonePoint: GeoJSON.Position = point.slice();
      ringClone.push(clonePoint);
    }
    cloneCoordinates.push(ringClone);
  }
  const cloned: GeoJSON.Polygon = {
    type: "Polygon",
    coordinates: cloneCoordinates,
  };

  if (geometry.bbox) {
    cloned.bbox = geometry.bbox.slice() as GeoJSON.BBox;
  }
  return cloned;
}

function validatePolygon(geom: GeoJSON.Polygon): ValidationResult {
  if (geom.type !== "Polygon") {
    return {
      ok: false,
      code: "GEOM_NOT_POLYGON",
      message: "Геометрия не является полигоном",
    };
  }
  if (geom.coordinates.length === 0) {
    return {
      ok: false,
      code: "INVALID_COORDINATES",
      message: "В полигоне должно быть хотя бы одно кольцо",
    };
  }

  for (const ring of geom.coordinates) {
    if (ring.length < 4) {
      return {
        ok: false,
        code: "RING_TOO_SHORT",
        message: "Кольцо полигона должно содержать минимум 4 точки",
      };
    }
    const firstPoint = ring[0];
    const lastPoint = ring[ring.length - 1];
    if (
      firstPoint &&
      lastPoint &&
      (firstPoint[0] !== lastPoint[0] || firstPoint[1] !== lastPoint[1])
    ) {
      return {
        ok: false,
        code: "RING_NOT_CLOSED",
        message: "Все кольца полигона должны быть замкнутыми",
      };
    }
    for (const point of ring) {
      if (!isValidPoint(point)) {
        return {
          ok: false,
          code: "INVALID_COORDINATES",
          message: "Полигон содуржит невалидные координаты",
        };
      }
    }
  }
  return { ok: true, value: geom };
}

function isValidPoint(point: GeoJSON.Position): boolean {
  return (
    point &&
    point.every((coord) => Number.isFinite(coord)) &&
    (point[0] as number) >= -180 &&
    (point[0] as number) <= 180 &&
    (point[1] as number) >= -90 &&
    (point[1] as number) <= 90
  );
}
