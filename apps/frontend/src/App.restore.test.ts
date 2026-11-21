vi.mock("@/editor/editorRuntime", () => ({
  getEditorRuntime: () => ({ workflow: { requestNavigation: vi.fn() } }),
}));
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, expect, it, vi } from "vitest";
import { installBrowserAuthEnvironment } from "@/test/browserAuthEnvironment";
import App from "./App.vue";
import { bindSessionAccessEffects, useAuthStore } from "./stores/auth";

const { refresh, statusCheck, logout } = vi.hoisted(() => ({
  refresh: vi.fn(),
  statusCheck: vi.fn(),
  logout: vi.fn(),
}));
vi.mock("@/api/auth", () => ({
  refreshSession: refresh,
  login: vi.fn(),
  logoutSession: logout,
  fetchSessionStatus: statusCheck,
}));
vi.mock("./components/workspace/WorkspaceNavigationDialog.vue", () => ({
  default: { template: "<div />" },
}));
vi.mock("./components/LoginScreen.vue", () => ({
  default: { template: '<div data-test="login-screen" />' },
}));
vi.mock("./components/work_order/EditorWorkOrdersView.vue", () => ({
  default: { template: '<div data-test="editor" />' },
}));
vi.mock("./components/ReviewerHome.vue", () => ({
  default: { template: '<div data-test="reviewer" />' },
}));

function bindEffects() {
  return bindSessionAccessEffects(useAuthStore(), {
    beforeAccessLoss: vi.fn(),
    afterEpochChange: vi.fn(),
    afterSessionTransition: vi.fn(),
    prepareExplicitLogin: vi.fn(),
  });
}
let releaseEffects: () => void;
beforeEach(() => {
  setActivePinia(createPinia());
  releaseEffects = bindEffects();
  refresh.mockReset();
  installBrowserAuthEnvironment();
  statusCheck.mockReset().mockImplementation(async (session_id: string) => ({
    session_id,
    state: "active",
  }));
  logout.mockReset();
});
it.each([200, 401, 503, 0])(
  "retry удерживает ожидание до исхода %s",
  async (status) => {
    const error = (code: number) => ({
      isAxiosError: true,
      code: code === 0 ? "ECONNABORTED" : undefined,
      response: code ? { status: code } : undefined,
    });
    refresh.mockRejectedValueOnce(error(503));
    let resolve!: (value: unknown) => void;
    let reject!: (value: unknown) => void;
    refresh.mockImplementationOnce(
      () =>
        new Promise((yes, no) => {
          resolve = yes;
          reject = no;
        }),
    );
    const wrapper = mount(App);
    await flushPromises();
    expect(wrapper.find('[data-test="error-action"]').exists()).toBe(true);
    await wrapper.get('[data-test="error-action"]').trigger("click");
    expect(useAuthStore().isRestoring).toBe(true);
    expect(wrapper.text()).toContain("Восстановление сессии");
    expect(wrapper.find('[data-test="login-screen"]').exists()).toBe(false);
    expect(wrapper.find('[data-test="error-action"]').exists()).toBe(false);
    expect(wrapper.find('[data-test="session-logout"]').exists()).toBe(false);
    if (status === 200)
      resolve({
        access_token: "synthetic",
        token_type: "bearer",
        session_id: "sid-a",
        user: { id: "a", email: "a@example.local", role: "editor" },
      });
    else reject(error(status));
    await flushPromises();
    expect(useAuthStore().isRestoring).toBe(false);
    expect(wrapper.find('[data-test="editor"]').exists()).toBe(status === 200);
    expect(wrapper.find('[data-test="login-screen"]').exists()).toBe(
      status === 401,
    );
    expect(wrapper.find('[data-test="error-action"]').exists()).toBe(
      status === 503 || status === 0,
    );
    wrapper.unmount();
  },
);

it("confirmed_ended_immediately_replaces_workspace_with_login", async () => {
  const auth = useAuthStore();
  auth.setAuth(
    "a",
    { id: "a", email: "a@example.local", role: "editor" },
    { sessionId: "sid-a" },
  );
  auth.isReady = true;
  statusCheck.mockResolvedValue({ session_id: "sid-a", state: "ended" });
  const wrapper = mount(App);
  expect(wrapper.find('[data-test="editor"]').exists()).toBe(true);
  await flushPromises();
  expect(wrapper.find('[data-test="login-screen"]').exists()).toBe(true);
  expect(wrapper.find('[data-test="editor"]').exists()).toBe(false);
  wrapper.unmount();
});

it("failed_logout_keeps_workspace_and_renders_logout_error", async () => {
  const auth = useAuthStore();
  auth.setAuth(
    "a",
    { id: "a", email: "a@example.local", role: "editor" },
    { sessionId: "sid-a" },
  );
  auth.isReady = true;
  logout.mockRejectedValue({ isAxiosError: true, response: { status: 503 } });
  const wrapper = mount(App);
  await auth.logout();
  await flushPromises();
  expect(wrapper.find('[data-test="editor"]').exists()).toBe(true);
  expect(wrapper.text()).toContain("Не удалось выйти, попробуйте ещё раз");
  wrapper.unmount();
});

it("initial_retry_error_can_be_dismissed_to_allow_explicit_login", async () => {
  refresh.mockRejectedValue({ isAxiosError: true, response: { status: 503 } });
  const wrapper = mount(App);
  await flushPromises();
  await wrapper.get('[data-test="session-logout"]').trigger("click");
  await flushPromises();
  expect(wrapper.find('[data-test="login-screen"]').exists()).toBe(true);
  wrapper.unmount();
});

it("restarts an interrupted initial restore when App is remounted with the same Pinia", async () => {
  const payload = (id: string) => ({
    access_token: id,
    session_id: id,
    user: { id, role: "reviewer", email: id + "@example.local" },
  });
  let finishOld!: (result: ReturnType<typeof payload>) => void;
  refresh
    .mockReturnValueOnce(
      new Promise((resolve) => {
        finishOld = resolve;
      }),
    )
    .mockResolvedValueOnce(payload("current"));
  const first = mount(App);
  await flushPromises();
  expect(refresh).toHaveBeenCalledTimes(1);
  first.unmount();
  releaseEffects();
  releaseEffects = bindEffects();
  const second = mount(App);
  try {
    finishOld(payload("old"));
    await flushPromises();
    expect(refresh).toHaveBeenCalledTimes(2);
    expect(useAuthStore().token).toBe("current");
    expect(second.find('[data-test="reviewer"]').exists()).toBe(true);
  } finally {
    second.unmount();
    releaseEffects();
  }
});
