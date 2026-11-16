import { defineStore } from "pinia";
import type { EditVersionMap } from "@/contracts/edit_version/editVersionMap";
import { createEditorReadState } from "./editorReadState";
export const useEditVersionMapStore = defineStore("editVersionMap", () =>
  createEditorReadState<EditVersionMap>(),
);
