import { useAuthStore } from "@/stores/auth";
import { useEditVersionDraftStore } from "@/stores/edit_version/editVersionDraft";
import { editorTestContext } from "@/test/editorTestContext";
import { target, workspaceFixture } from "@/test/workspaceEditFixture";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, expect, it, vi } from "vitest";
import { useWorkspaceRecoveryStore } from "@/stores/workspace/workspace_recovery/workspaceRecovery";
import { installEditorRuntime } from "./editorRuntime";
import { requireEditorWorkflow } from "./editorRuntimeBinding";

beforeEach(() => sessionStorage.clear());
it("disposes its recovery host and Revert watcher exactly once", () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const recovery = useWorkspaceRecoveryStore(pinia);
  const bind = recovery.bindHost.bind(recovery);
  const detached = vi.fn();
  vi.spyOn(recovery, "bindHost").mockImplementation((host) => {
    const release = bind(host);
    return () => {
      release();
      detached();
    };
  });
  const runtime = installEditorRuntime(pinia);
  const auth = useAuthStore(pinia);
  auth.token = "token";
  auth.user = { id: "actor", role: "editor", email: "a@local" };
  const s = editorTestContext();
  s.seed(workspaceFixture(true));
  s.editorSession.openedWorkOrderId = s.workOrders.selectedWorkOrderId =
    target.workOrderId;
  s.editorSession.openedEditVersionId = target.editVersionId;
  expect(runtime.workflow.beginRevert()).toBe("confirm");
  runtime.dispose();
  runtime.dispose();
  expect(detached).toHaveBeenCalledOnce();
  // A live watcher would invoke an unbound commands getter here.
  expect(() => {
    auth.user = null;
  }).not.toThrow();
});
it("binds before authentication and keeps two application instances independent", () => {
  const firstPinia = createPinia();
  setActivePinia(firstPinia);
  const first = installEditorRuntime(firstPinia);
  expect(installEditorRuntime(firstPinia)).toBe(first);
  useAuthStore().setAuth(
    "token",
    { id: "actor", email: "a@local", role: "editor" },
    { sessionId: "sid" },
  );
  const s = editorTestContext();
  s.seed(workspaceFixture());
  s.editorSession.openedWorkOrderId = s.workOrders.selectedWorkOrderId =
    target.workOrderId;
  s.editorSession.openedEditVersionId = target.editVersionId;
  expect(first.workflow.beginLocalEdit(target.featureId, 1)).toBe(true);
  const secondPinia = createPinia();
  setActivePinia(secondPinia);
  const second = installEditorRuntime(secondPinia);
  expect(useEditVersionDraftStore().localDraft).toBeNull();
  expect(first.workflow.beginLocalEdit(target.featureId, 1)).toBe(true);
  expect(first.workflow.moveLocalVertex([65.1, 44.3])).toBe(true);
  expect(
    s.editVersionDraft.localDraft?.candidateGeometry.coordinates[1],
  ).toEqual([65.1, 44.3]);
  const navigationId = first.workflow.requestNavigation({
    kind: "work-order",
    workOrderId: "B",
  });
  expect(navigationId).not.toBeNull();
  first.workflow.clearOpenedWorkspace({ force: true });
  expect(s.editorNavigation.navigation).toBeNull();
  second.dispose();
  first.dispose();
});

it("reset retains binding and disposal allows a new runtime", async () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const runtime = installEditorRuntime(pinia);
  runtime.workflow.resetEditor();
  expect(await runtime.workflow.saveLocalDraft()).toEqual({
    kind: "not-started",
  });
  expect(runtime.workflow.cancelLocalEdit()).toBe(true);
  runtime.dispose();
  runtime.dispose();
  const replacement = installEditorRuntime(pinia);
  expect(replacement).not.toBe(runtime);
  replacement.dispose();
});

it("resolves the same owner through a Pinia devtools action proxy", () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const runtime = installEditorRuntime(pinia);
  const owner = useEditVersionDraftStore();
  const trackedOwner = new Proxy(owner, {
    get: (target, key, receiver) => Reflect.get(target, key, receiver),
  });
  expect(requireEditorWorkflow(trackedOwner)).toBe(runtime.workflow);
  runtime.dispose();
  expect(() => requireEditorWorkflow(trackedOwner)).toThrow("installed");
});
