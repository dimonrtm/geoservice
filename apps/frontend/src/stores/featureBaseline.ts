import { defineStore } from "pinia";
import type { FeatureBaseline } from "@/contracts/featureBaseline";
import { createEditorReadState } from "./editorReadState";
export const useFeatureBaselineStore = defineStore("featureBaseline", () =>
  createEditorReadState<FeatureBaseline>(),
);
