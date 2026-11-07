import { defineStore } from "pinia";
import type { EditVersionChangeSet } from "@/contracts/editVersionChangeSet";
import { createEditorReadState } from "./editorReadState";
export const useEditVersionChangeSetStore = defineStore(
  "editVersionChangeSet",
  () => createEditorReadState<EditVersionChangeSet>(),
);
