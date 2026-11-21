import { AxiosError } from "axios";
import { http, installHttpSession } from "@/api/http";
import { fetchMe } from "@/api/auth";
import { getBrowserSessionCoordinator } from "@/auth/browserSessionCoordinator";
import { installBrowserAuthEnvironment } from "@/test/browserAuthEnvironment";
import { useAuthStore } from "@/stores/auth";
import { useEditVersionDraftStore } from "@/stores/edit_version/editVersionDraft";
import { editorTestContext } from "@/test/editorTestContext";
import {
  candidate,
  commandId,
  geometry,
  successFixture,
  target,
  workspaceFixture,
} from "@/test/workspaceEditFixture";
import * as snapshots from "@/composables/edit_version/useEditVersionEditor";
import { workOrderListEntryFixture } from "@/test/workOrderListFixture";
import { createRecoveryRecord } from "@/contracts/workspace/workspace-recovery";
import { createRecoveryStorage } from "@/stores/workspace/workspace_recovery/workspaceRecoveryStorage";
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

it("reads session access live across role changes and store reset", () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const runtime = installEditorRuntime(pinia);
  const auth = useAuthStore(pinia);
  const access = runtime.sessionAccess;
  const editor = { id: "a", email: "a@example.local", role: "editor" as const };
  try {
    auth.setAuth("token", editor, { sessionId: "sid" });
    expect(access.actorId).toBe("a");
    expect(access.canEdit).toBe(true);
    expect(access).not.toHaveProperty("token");
    const epoch = access.sessionEpoch;
    const orders = editorTestContext().workOrders;
    const resetOrders = vi.spyOn(orders, "reset");
    const trackedAuth = new Proxy(auth, {});
    trackedAuth.setUser({ ...editor, role: "reviewer" });
    expect(access.canEdit).toBe(false);
    expect(access.sessionEpoch).toBeGreaterThan(epoch);
    expect(resetOrders).not.toHaveBeenCalled();
    auth.$reset();
    auth.setAuth("next", { ...editor, id: "b" }, { sessionId: "sid-b" });
    expect(access.actorId).toBe("b");
    expect(resetOrders).toHaveBeenCalledOnce();
  } finally {
    runtime.dispose();
  }
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

it("finishes a previously interrupted GET once through the replacement runtime", async () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const store = useWorkspaceRecoveryStore(pinia);
  const bind = vi.spyOn(store, "bindHost");
  let runtime = installEditorRuntime(pinia);
  const firstHost = vi.spyOn(bind.mock.calls[0]![0], "complete");
  let releaseOldRead!: (data: ReturnType<typeof workspaceFixture>) => void;
  const read = vi
    .spyOn(snapshots, "readEditVersionSnapshot")
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          releaseOldRead = resolve;
        }),
    )
    .mockResolvedValueOnce(workspaceFixture(true));
  try {
    const auth = useAuthStore(pinia);
    auth.token = "token";
    auth.user = { id: "actor", role: "editor", email: "actor@example.local" };
    editorTestContext().workOrders.items = [
      workOrderListEntryFixture({
        id: target.workOrderId,
        code: "WO",
        title: "Работа",
        description: null,
        status: "in_progress",
      }),
    ];
    const record = createRecoveryRecord(
      {
        actorId: "actor",
        target,
        request: {
          commandId,
          draftVersionToken: "revision-a",
          geometry: candidate,
        },
      },
      { geometry, vertexIndex: 1 },
    );
    record.outcome = { kind: "succeeded", result: successFixture() };
    record.readbackRequired = true;
    await createRecoveryStorage().insert(record);
    await store.initializeActor("actor");
    expect(read).toHaveBeenCalledOnce();

    runtime.dispose();
    runtime = installEditorRuntime(pinia);
    const secondHost = vi.spyOn(bind.mock.calls[1]![0], "complete");
    releaseOldRead(workspaceFixture(true));
    await store.retryRead(record.key);
    expect(read).toHaveBeenCalledTimes(2);
    expect(firstHost).not.toHaveBeenCalled();
    expect(secondHost).toHaveBeenCalledOnce();
    expect(store.getRecord(record.key)).toBeNull();
  } finally {
    runtime.dispose();
    bind.mockRestore();
    read.mockRestore();
  }
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

it.each(["current", "replaced", "disposed"] as const)(
  "handles a delayed protected 401 with a %s session and an open workspace",
  async (scenario) => {
    installBrowserAuthEnvironment();
    const pinia = createPinia();
    setActivePinia(pinia);
    const runtime = installEditorRuntime(pinia);
    const auth = useAuthStore(pinia);
    const releaseHttp = installHttpSession(auth);
    const adapter = http.defaults.adapter;
    const { editorSession, workOrders } = editorTestContext();
    const workspace = workspaceFixture();
    const user = { id: "actor", email: "a@example.local", role: "editor" };
    let loginNumber = 0;
    let started!: () => void;
    let respond!: () => void;
    const received = new Promise<void>((resolve) => {
      started = resolve;
    });
    const delayed = new Promise<void>((resolve) => {
      respond = resolve;
    });
    http.defaults.adapter = async (config) => {
      const ok = (data: unknown) => ({
        config,
        status: 200,
        statusText: "OK",
        headers: {},
        data,
      });
      if (config.url?.endsWith("/login")) {
        loginNumber++;
        return ok({
          user,
          token_type: "bearer",
          session_id: "sid-" + loginNumber,
          access_token: "token-" + loginNumber,
        });
      }
      if (config.url?.endsWith("/session/status"))
        return ok({
          session_id: JSON.parse(config.data).session_id,
          state: "active",
        });
      if (config.url?.endsWith("/me")) {
        started();
        await delayed;
        throw new AxiosError("expired", "ERR_BAD_REQUEST", config, undefined, {
          config,
          status: 401,
          statusText: "Unauthorized",
          headers: {},
          data: { code: "AUTH_REQUIRED", message: "expired" },
        });
      }
      if (config.url?.endsWith("/change-set"))
        return ok(workspace.workOrder.editVersion);
      if (config.url?.endsWith("/" + target.editVersionId))
        return ok(workspace);
      throw new Error("Unexpected API request " + config.url);
    };
    try {
      await auth.loginWithPassword(user.email, "test");
      const pending = fetchMe().catch((error) => error);
      await received;
      const oldRead = editorSession.reserveWorkspaceRead({
        actorId: user.id,
        ...target,
      });
      if (scenario === "replaced")
        await auth.loginWithPassword(user.email, "test");
      workOrders.selectWorkOrder(target.workOrderId);
      await editorSession.loadVersion(target.workOrderId, target.editVersionId);
      expect(editorSession.isWorkOrderOpened(target.workOrderId)).toBe(true);
      if (scenario === "disposed") {
        releaseHttp();
        runtime.dispose();
      }
      respond();
      expect(await pending).toMatchObject({ response: { status: 401 } });
      expect(getBrowserSessionCoordinator().readSessionMarker()).toMatchObject({
        state: "active",
        sessionId: "sid-" + loginNumber,
      });
      if (scenario === "replaced") {
        expect(
          editorSession.applyWorkspaceRead(oldRead, workspaceFixture(true)),
        ).toBe("blocked");
        expect(
          editorSession.activeWorkspace?.workOrder.editVersion
            .draftVersionToken,
        ).toBe("revision-a");
      }
      expect(auth.sessionId).toBe(
        scenario === "current" ? null : "sid-" + loginNumber,
      );
      expect(auth.token).toBe(
        scenario === "current" ? null : "token-" + loginNumber,
      );
      expect(editorSession.openedWorkOrderId).toBe(
        scenario === "current" ? null : target.workOrderId,
      );
    } finally {
      auth.stopBrowserSessionSync();
      releaseHttp();
      runtime.dispose();
      http.defaults.adapter = adapter;
    }
  },
);
