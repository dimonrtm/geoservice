import { createRecoveryIO } from "./createRecoveryIO";
import { defineWorkspaceRecoveryStore } from "./defineWorkspaceRecoveryStore";

export const useWorkspaceRecoveryStore =
  defineWorkspaceRecoveryStore(createRecoveryIO);
