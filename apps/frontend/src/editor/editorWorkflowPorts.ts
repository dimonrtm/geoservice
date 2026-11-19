import type { WorkspaceResponse } from "@/contracts/work_order/work-orders";
import type { WorkspaceCommandPhase } from "@/contracts/workspace/workspace-command";
import type { PendingGeometryCommand } from "@/contracts/workspace/workspace-edit";
import type {
  ReadTicket,
  RecoveryApplyResult,
  RecoveryContext,
  RecoveryHost,
  RecoveryRecordV2,
  RecoverySource,
  RecoveryStartResult,
} from "@/contracts/workspace/workspace-recovery";
import type { ResetWorkOrdersOptions } from "@/stores/editor_session/editorSessionStorage";
import type { CommandsPort } from "./contracts/commands";
import type { DraftPort } from "./contracts/draft";
import type { NavigationPort } from "./contracts/navigation";
import type { EditorContext } from "./editorWorkflowContracts";

export type ClearOpenedWorkspaceOptions = {
  force?: boolean;
  preserveStoredWorkspace?: boolean;
};
export type EditorWorkflowPorts = {
  editVersionDraft: DraftPort;
  editVersionCommands: CommandsPort;
  editorNavigation: NavigationPort;
  editorSession: {
    readonly activeWorkspace: WorkspaceResponse | null;
    readonly openedWorkOrderId: string | null;
    readonly openedEditVersionId: string | null;
    readonly workspaceGeneration: number;
    readonly readGenerations: Readonly<Record<string, number>>;
    clearOpenedWorkspace(options?: ClearOpenedWorkspaceOptions): void;
    closeWorkspaceState(options: ClearOpenedWorkspaceOptions): void;
    resetEditor(options?: ResetWorkOrdersOptions): void;
    resetSessionState(options: ResetWorkOrdersOptions): void;
    reserveWorkspaceRead(context: RecoveryContext): ReadTicket;
    applyWorkspaceRead(
      ticket: ReadTicket,
      workspace: WorkspaceResponse,
    ): RecoveryApplyResult;
  };
  auth: {
    readonly user: { id: string; role: string } | null;
    readonly sessionEpoch: number;
    readonly sessionId: string | null;
    readonly isAuthenticated: boolean;
    logout(): Promise<boolean>;
    clearLocalSession(): void;
  };
  workOrders: {
    readonly items: ReadonlyArray<{ id: string | null }>;
    readonly selectedWorkOrderId: string | null;
    selectWorkOrder(id: string): void;
  };
  editor: { readyFor(id: string): boolean; reset(): void };
  recovery: {
    readonly records: Readonly<Record<string, RecoveryRecordV2>>;
    readonly phases: Readonly<Record<string, WorkspaceCommandPhase>>;
    readonly storageError: string | null;
    readonly readbackErrors: Readonly<Record<string, string>>;
    readonly contextErrors: Readonly<Record<string, string>>;
    getRecord(key: string): RecoveryRecordV2 | null;
    bindHost(host: RecoveryHost): () => void;
    initializeActor(actorId: string): Promise<void>;
    submit(
      command: PendingGeometryCommand,
      source: Exclude<RecoverySource, null>,
    ): Promise<RecoveryStartResult>;
    retry(key: string): Promise<void>;
    retryRead(key: string): Promise<void>;
    prepareActorLogout(actorId: string): Promise<boolean>;
    suspendActor(actorId: string, workOrderId?: string): Promise<void>;
  };
  context(): EditorContext | null;
  createCommandId(): string;
  watchConfirmation(
    read: () => boolean,
    changed: (valid: boolean) => void,
    options: { flush: "sync" },
  ): () => void;
};
