import { defineStore } from "pinia";
import type { EditVersionMap } from "@/contracts/editVersionMap";
import { createEditorReadState } from "./editorReadState";
export const useEditVersionMapStore = defineStore("editVersionMap", () =>
  createEditorReadState<EditVersionMap>(),
);
