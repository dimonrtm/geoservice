import type {
  Feature,
  FeatureCollection,
  Geometry,
  MultiPolygon,
  Polygon,
} from "geojson";
import type { WorkOrderStatus, EditVersionStatus } from "./work-orders";
import { nonempty, ProtocolError, record } from "./workspace-edit";

export type EditVersionAoi = {
  id: string;
  name: string;
  description: string | null;
  geometry: Polygon | MultiPolygon;
  extent: [number, number, number, number];
};

export type EditVersionFeature = Feature<Geometry, Record<string, unknown>> & {
  id: string;
};

export type EditVersionFeatureCollection = Omit<
  FeatureCollection<Geometry, Record<string, unknown>>,
  "features"
> & {
  features: EditVersionFeature[];
};

export type EditVersionAssociation = {
  id: string;
  fromFeatureId: string;
  toFeatureId: string;
  associationType: string;
  version: number;
};

export type EditVersionMap = {
  workOrder: {
    id: string;
    code: string;
    title: string;
    description: string | null;
    status: WorkOrderStatus;
    scope: {
      aoi: EditVersionAoi;
    };
    editVersion: {
      id: string;
      status: EditVersionStatus;
      baseNetworkRevision: number;
      draftVersionToken: string;
      features: EditVersionFeatureCollection;
      associations: EditVersionAssociation[];
    };
  };
};

export function parseEditVersionMap(
  value: unknown,
  workOrderId: string,
  editVersionId: string,
): EditVersionMap {
  if (!record(value) || !record(value.workOrder)) throw new ProtocolError();
  const order = value.workOrder;
  const version = order.editVersion;
  if (
    order.id !== workOrderId ||
    !record(order.scope) ||
    !record(order.scope.aoi) ||
    !record(version) ||
    version.id !== editVersionId ||
    version.status !== "open" ||
    !nonempty(version.draftVersionToken) ||
    !record(version.features) ||
    version.features.type !== "FeatureCollection" ||
    !Array.isArray(version.features.features) ||
    !Array.isArray(version.associations)
  )
    throw new ProtocolError();
  const ids = new Set<string>();
  for (const feature of version.features.features) {
    if (
      !record(feature) ||
      !nonempty(feature.id) ||
      ids.has(feature.id) ||
      feature.type !== "Feature" ||
      !record(feature.geometry) ||
      !nonempty(feature.geometry.type) ||
      !record(feature.properties)
    )
      throw new ProtocolError();
    ids.add(feature.id);
  }
  return value as EditVersionMap;
}
