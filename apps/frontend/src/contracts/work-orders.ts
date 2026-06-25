import type {
  Feature,
  FeatureCollection,
  Geometry,
  MultiPolygon,
  Polygon,
} from "geojson";

export type WorkOrderStatus = "assigned" | "in_progress";

export type WorkOrderSummary = {
  id: string;
  code: string;
  title: string;
  description: string | null;
  status: WorkOrderStatus;
};

export type AssignedWorkOrdersResponse = {
  workOrders: WorkOrderSummary[];
};

export type EditVersionStatus = "open";

export type EditVersionSummary = {
  id: string;
  workOrderId: string;
  ownerId: string;
  status: EditVersionStatus;
  baseNetworkRevision: number;
  createdAt: string;
  lastOpenedAt: string;
};

export type OpenEditVersionResponse = {
  created: boolean;
  editVersion: EditVersionSummary;
};

export type WorkspaceAoi = {
  id: string;
  name: string;
  description: string | null;
  geometry: Polygon | MultiPolygon;
  extent: [number, number, number, number];
};

export type WorkspaceFeature = Feature<Geometry, Record<string, unknown>> & {
  id: string;
};

export type WorkspaceFeatureCollection = Omit<
  FeatureCollection<Geometry, Record<string, unknown>>,
  "features"
> & {
  features: WorkspaceFeature[];
};

export type WorkspaceAssociation = {
  id: string;
  fromFeatureId: string;
  toFeatureId: string;
  associationType: string;
  version: number;
};

export type WorkspaceResponse = {
  workOrder: {
    id: string;
    code: string;
    title: string;
    description: string | null;
    status: WorkOrderStatus;
    scope: {
      aoi: WorkspaceAoi;
    };
    editVersion: {
      id: string;
      status: EditVersionStatus;
      baseNetworkRevision: number;
      features: WorkspaceFeatureCollection;
      associations: WorkspaceAssociation[];
    };
  };
};
