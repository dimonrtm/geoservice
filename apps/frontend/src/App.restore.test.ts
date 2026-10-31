import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, expect, it, vi } from "vitest";
import { installBrowserAuthEnvironment } from "@/test/browserAuthEnvironment";
import App from "./App.vue";
import { useAuthStore } from "./stores/auth";

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
vi.mock("@/stores/workOrders", () => ({
  useWorkOrdersStore: () => ({
    reset: vi.fn(),
    suspendWorkspaceRecoveryForAccessLoss: vi.fn(),
  }),
}));
vi.mock("@/stores/workspaceRecovery", () => ({
  useWorkspaceRecoveryStore: () => ({ hideActor: vi.fn() }),
}));
vi.mock("./components/WorkspaceNavigationDialog.vue", () => ({
  default: { template: "<div />" },
}));
vi.mock("./components/LoginScreen.vue", () => ({
  default: { template: '<div data-test="login-screen" />' },
}));
vi.mock("./components/EditorWorkOrdersView.vue", () => ({
  default: { template: '<div data-test="editor" />' },
}));
vi.mock("./components/ReviewerHome.vue", () => ({
  default: { template: '<div data-test="reviewer" />' },
}));

beforeEach(() => {
  setActivePinia(createPinia());
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
