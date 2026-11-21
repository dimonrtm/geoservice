import { defineStore } from "pinia";
import { reactive, toRefs } from "vue";
import {
  createRecoveryExecutor,
  createRecoveryState,
} from "./createRecoveryExecutor";
import type { RecoveryIO } from "./workspaceRecoveryIO";

export function defineWorkspaceRecoveryStore(createIO: () => RecoveryIO) {
  return defineStore("workspaceRecovery", () => {
    const state = reactive(createRecoveryState());
    const executor = createRecoveryExecutor(state, createIO());
    return { ...toRefs(state), ...executor };
  });
}
