import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./components/LoginScreen.vue", () => ({
  default: {
    name: "LoginScreen",
    template: '<div data-test="login-screen"></div>',
  },
}));

vi.mock("./components/MapPageView.vue", () => ({
  default: {
    name: "MapPageView",
    template: '<div data-test="map-page-view"></div>',
  },
}));

vi.mock("./components/EditorWorkOrdersView.vue", () => ({
  default: {
    name: "EditorWorkOrdersView",
    template: '<div data-test="editor-work-orders-view"></div>',
  },
}));

vi.mock("./components/ReviewerHome.vue", () => ({
  default: {
    name: "ReviewerHome",
    template: '<div data-test="reviewer-home"></div>',
  },
}));

describe("App", () => {
  beforeEach(() => {
    vi.resetModules();
    setActivePinia(createPinia());
  });

  it("shows editor work orders shell for authenticated editor", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const auth = useAuthStore();
    auth.token = "token-1";
    auth.user = {
      id: "editor-1",
      email: "editor@example.local",
      role: "editor",
    };
    auth.isReady = true;

    const { default: App } = await import("@/App.vue");
    const wrapper = mount(App);

    expect(wrapper.find('[data-test="editor-work-orders-view"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-test="map-page-view"]').exists()).toBe(false);
  });

  it("keeps reviewer home for authenticated reviewer", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const auth = useAuthStore();
    auth.token = "token-1";
    auth.user = {
      id: "reviewer-1",
      email: "reviewer@example.local",
      role: "reviewer",
    };
    auth.isReady = true;

    const { default: App } = await import("@/App.vue");
    const wrapper = mount(App);

    expect(wrapper.find('[data-test="reviewer-home"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="editor-work-orders-view"]').exists()).toBe(
      false,
    );
  });

  it("shows status screen instead of login while auth is not ready", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const auth = useAuthStore();
    auth.token = null;
    auth.user = null;
    auth.isReady = false;
    auth.isRestoring = true;

    const { default: App } = await import("@/App.vue");
    const wrapper = mount(App);

    expect(wrapper.text()).toContain("Восстановление сессии");
    expect(wrapper.find('[data-test="login-screen"]').exists()).toBe(false);
    expect(wrapper.find('[data-test="editor-work-orders-view"]').exists()).toBe(
      false,
    );
    expect(wrapper.find('[data-test="reviewer-home"]').exists()).toBe(false);
  });

  it("retries session restoration through the actionable error", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const auth = useAuthStore();
    auth.isReady = true;
    auth.sessionError = {
      summary: "Не удалось восстановить сессию.",
      guidance: "Проверьте соединение и повторите запрос.",
      action: { id: "retry", label: "Повторить" },
      diagnostics: { code: "INTERNAL_ERROR", correlationId: "session-id" },
    };
    auth.restoreSession = vi.fn();

    const { default: App } = await import("@/App.vue");
    const wrapper = mount(App);
    await wrapper.get('[data-test="error-action"]').trigger("click");

    expect(auth.restoreSession).toHaveBeenCalledTimes(1);
  });

  it("dismisses an expired-session error before showing login", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const auth = useAuthStore();
    auth.isReady = true;
    auth.sessionError = {
      summary: "Сессия завершена.",
      guidance: "Войдите снова.",
      action: { id: "sign-in", label: "Войти снова" },
      diagnostics: { code: "AUTH_REQUIRED", correlationId: "session-id" },
    };

    const { default: App } = await import("@/App.vue");
    const wrapper = mount(App);
    await wrapper.get('[data-test="error-action"]').trigger("click");

    expect(auth.sessionError).toBeNull();
    expect(wrapper.find('[data-test="login-screen"]').exists()).toBe(true);
  });

  it("renders desktop and narrow logout controls through one action", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const auth = useAuthStore();
    auth.token = "token-1";
    auth.user = {
      id: "editor-1",
      email: "editor@example.local",
      role: "editor",
    };
    auth.isReady = true;
    auth.logout = vi.fn();

    const { default: App } = await import("@/App.vue");
    const wrapper = mount(App);
    const desktop = wrapper.get('[data-test="logout-desktop"]');
    const mobile = wrapper.get('[data-test="logout-mobile"]');

    expect(desktop.text()).toContain("Выйти");
    expect(desktop.element.closest(".logoutDesktop")).not.toBeNull();
    expect(mobile.attributes("aria-label")).toBe("Выйти");
    expect(mobile.attributes("aria-describedby")).toBeDefined();
    expect(mobile.element.closest(".logoutMobile")).not.toBeNull();

    await desktop.trigger("click");
    await mobile.trigger("click");
    expect(auth.logout).toHaveBeenCalledTimes(2);
  });

  it("keeps session-error logout as icon plus text", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const auth = useAuthStore();
    auth.isReady = true;
    auth.sessionError = {
      summary: "Не удалось восстановить сессию.",
      guidance: "Проверьте соединение и повторите запрос.",
      action: { id: "retry", label: "Повторить" },
      diagnostics: { code: "INTERNAL_ERROR", correlationId: "session-id" },
    };
    auth.logout = vi.fn();

    const { default: App } = await import("@/App.vue");
    const wrapper = mount(App);
    const logout = wrapper.get('[data-test="session-logout"]');
    expect(logout.text()).toContain("Выйти");

    await logout.trigger("click");
    expect(auth.logout).toHaveBeenCalledTimes(1);
  });
});
