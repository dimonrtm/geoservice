import { expect, it } from "vitest";
// @ts-expect-error The command-line checker is an independently executable JS module.
import { analyzeEditorBoundaries } from "../../scripts/check-editor-boundaries.mjs";

const header =
  'import { useEditVersionDraftStore as useDraft } from "@/stores/edit_version/editVersionDraft"; const d = useDraft();';
it.each([
  "d.localDraft = null;",
  "d.$patch({localDraft:null});",
  "d.$reset();",
  "const a = d.localDraft; a.candidateGeometry.coordinates[1][0]++;",
  "const {localDraft: a} = d; delete a.featureId;",
  "const a = d.localDraft.candidateGeometry.coordinates; a.push([1,2]);",
  "const {localDraft} = storeToRefs(d); localDraft.value = null;",
  "Object.assign(d, {localDraft: null});",
  'import {storeToRefs as refs} from "pinia"; const {localDraft} = refs(d); localDraft.value = null;',
  'import {mutate} from "./unsafe"; mutate(d.localDraft);',
  "const draft = d.localDraft; export {draft};",
])("rejects external editor mutation: %s", (body) => {
  expect(
    analyzeEditorBoundaries([
      { path: "src/example.ts", source: header + body },
    ]),
  ).not.toHaveLength(0);
});
it("rejects a write through destructured workflow dependencies", () => {
  expect(
    analyzeEditorBoundaries([
      {
        path: "src/editor/workflows/example.ts",
        source:
          "const {editVersionDraft: draft} = ports; draft.localDraft = null;",
      },
    ]),
  ).not.toHaveLength(0);
});
it("accepts reading and owner operations", () => {
  expect(
    analyzeEditorBoundaries([
      {
        path: "src/example.ts",
        source:
          header +
          "const a = d.localDraft; console.log(a?.featureId); d.cancelLocalEdit();",
      },
    ]),
  ).toEqual([]);
});
it.each(['@click="d.localDraft = null"', 'v-model="d.localDraft.featureId"'])(
  "rejects a Vue template mutation: %s",
  (handler) => {
    expect(
      analyzeEditorBoundaries([
        {
          path: "src/Example.vue",
          source: `<script setup lang="ts">${header}</script><template><input ${handler}/></template>`,
        },
      ]),
    ).not.toHaveLength(0);
  },
);
it("rejects a runtime owner cycle but permits a type-only contract", () => {
  const path = "src/stores/editor_navigation/editorNavigation.ts";
  expect(analyzeEditorBoundaries([{ path, source: header }])).not.toHaveLength(
    0,
  );
  expect(
    analyzeEditorBoundaries([
      {
        path,
        source: 'import type { DraftPort } from "@/editor/contracts/draft";',
      },
    ]),
  ).toEqual([]);
});
it("rejects framework dependencies in the pure coordinator", () => {
  expect(
    analyzeEditorBoundaries([
      {
        path: "src/editor/createEditorWorkflow.ts",
        source: 'import { watch } from "vue";',
      },
    ]),
  ).not.toHaveLength(0);
});
