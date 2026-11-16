import type { EditVersionMap } from "../edit_version/editVersionMap";
import type {
  BasicValidation,
  WorkspaceChangeSet,
} from "../workspace/workspace-edit";

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

export type {
  EditVersionAoi as WorkspaceAoi,
  EditVersionFeature as WorkspaceFeature,
  EditVersionFeatureCollection as WorkspaceFeatureCollection,
  EditVersionAssociation as WorkspaceAssociation,
} from "../edit_version/editVersionMap";

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
