import type { EditVersionMap } from "./editVersionMap";
import type { BasicValidation, WorkspaceChangeSet } from "./workspace-edit";

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

export type {
  EditVersionAoi as WorkspaceAoi,
  EditVersionFeature as WorkspaceFeature,
  EditVersionFeatureCollection as WorkspaceFeatureCollection,
  EditVersionAssociation as WorkspaceAssociation,
} from "./editVersionMap";

// Composed view state used by the map and by persisted recovery records.
type MapOrder = EditVersionMap["workOrder"];
export type WorkspaceResponse = {
  workOrder: Omit<MapOrder, "editVersion"> & {
    editVersion: MapOrder["editVersion"] & {
      hasPersistedChangeSet: boolean;
      basicValidation: BasicValidation | null;
      changeSet: WorkspaceChangeSet | null;
    };
  };
};
