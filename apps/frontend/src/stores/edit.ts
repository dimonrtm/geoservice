import { defineStore } from "pinia";

import {
  deleteLayerFeature,
  fetchLayerFeatureById,
  HttpError,
  patchLayerFeature,
} from "@/api/layers";
import {
  isVersionMismatchBody,
  type VersionMismatchBody,
} from "@/contracts/api";
import {
  type ApiFeature,
  clonePolygonGeometry,
  isPolygonGeometry,
  isRecord,
  isString,
  validatePolygonGeometry,
  type FeatureProperties,
  type PolygonGeometry,
  type PolygonValidationError,
} from "@/contracts/geojson";

type DraftFeature = {
  properties: FeatureProperties;
  geometry: PolygonGeometry;
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

export type EditConflictError = {
  kind: "conflict";
  body: VersionMismatchBody;
};

export type EditLastError = PolygonValidationError | EditConflictError;

export const useEditStore = defineStore("edit", {
  state: () => ({
    edit: { mode: "idle" } as EditState,
  }),
  actions: {
    startEditing(featureFromServer: {
      layerId: string;
      featureId: string;
      version: number;
      properties: FeatureProperties;
      geometry: PolygonGeometry;
    }): void {
      const draftFeature: DraftFeature = {
        properties: cloneProperties(featureFromServer.properties),
        geometry: clonePolygonGeometry(featureFromServer.geometry),
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

      const session = this.sessionOrNull();
      if (!session) {
        return;
      }

      const validateResult = validatePolygonGeometry(newDraft.geometry);
      if (!validateResult.ok) {
        const prevDirty =
          this.edit.mode === "editing" ? this.edit.dirty : false;
        this.edit = {
          mode: "editing",
          session: { ...session },
          lastError: validateResult,
          dirty: prevDirty,
        };
        return;
      }

      this.edit = {
        mode: "editing",
        session: {
          ...session,
          draft: {
            properties: cloneProperties(newDraft.properties),
            geometry: clonePolygonGeometry(newDraft.geometry),
          },
        },
        lastError: undefined,
        dirty: true,
      };
    },
    cancelEditing(): void {
      if (this.isEditing()) {
        this.edit = { mode: "idle" };
      }
    },
    async saveEditing(): Promise<ApiFeature<PolygonGeometry> | null> {
      if (this.edit.mode !== "editing" || this.edit.dirty === false) {
        return null;
      }

      const session = this.edit.session;
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

        if (!isPolygonGeometry(feature.geometry)) {
          this.edit.lastError = {
            ok: false,
            code: "GEOM_NOT_POLYGON",
            message: "Сервер вернул геометрию неожиданного типа",
          };
          return null;
        }

        const polygonFeature: ApiFeature<PolygonGeometry> = {
          ...feature,
          geometry: feature.geometry,
        };

        this.edit = {
          ...this.edit,
          session: {
            ...session,
            version: polygonFeature.version,
            draft: {
              properties: cloneProperties(polygonFeature.properties),
              geometry: clonePolygonGeometry(polygonFeature.geometry),
            },
          },
          dirty: false,
          lastError: undefined,
        };
        return polygonFeature;
      } catch (err: unknown) {
        if (err instanceof HttpError) {
          await this.handleHttpError(err);
          return null;
        }
        throw err;
      }
    },
    async deleteEditing(): Promise<string | null> {
      if (this.edit.mode !== "editing") {
        return null;
      }

      try {
        const deletedFeatureId = this.edit.session.featureId;
        await deleteLayerFeature(
          this.edit.session.layerId,
          this.edit.session.featureId,
          { version: this.edit.session.version },
        );
        this.edit = { mode: "idle" };
        return deletedFeatureId;
      } catch (err: unknown) {
        if (err instanceof HttpError) {
          await this.handleHttpError(err);
          return null;
        }
        throw err;
      }
    },
    isEditing(): boolean {
      return this.edit.mode === "editing";
    },
    sessionOrNull(): EditSession | null {
      return this.edit.mode === "editing" ? this.edit.session : null;
    },
    async handleHttpError(err: HttpError): Promise<void> {
      if (this.edit.mode !== "editing") {
        return;
      }

      const status = err.status;
      const body = err.body;

      if (status === 422) {
        if (isRecord(body) && isString(body.error)) {
          this.edit.lastError = {
            ok: false,
            code: "INVALID_COORDINATES",
            message: body.error,
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

      if (status === 409 && isVersionMismatchBody(body)) {
        this.edit.lastError = { kind: "conflict", body };
        try {
          const feature = await fetchLayerFeatureById(
            this.edit.session.layerId,
            this.edit.session.featureId,
          );
          if (!isPolygonGeometry(feature.geometry)) {
            return;
          }
          this.startEditing({
            layerId: this.edit.session.layerId,
            featureId: feature.id,
            version: feature.version,
            properties: feature.properties,
            geometry: feature.geometry,
          });
        } catch (refreshErr: unknown) {
          if (refreshErr instanceof HttpError && refreshErr.status === 404) {
            this.edit = { mode: "idle" };
            return;
          }
          throw refreshErr;
        }
      }
    },
  },
});

function cloneProperties(properties: FeatureProperties): FeatureProperties {
  const duplicate: FeatureProperties = {};
  for (const key of Object.keys(properties)) {
    duplicate[key] = properties[key];
  }
  return duplicate;
}
