import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

const loginWithPasswordMock = vi.hoisted(() => vi.fn());

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    loginWithPassword: loginWithPasswordMock,
  }),
}));

async function fillAndSubmitLoginForm(wrapper: VueWrapper) {
  await wrapper.get('input[type="email"]').setValue("editor@example.local");
  await wrapper.get('input[type="password"]').setValue("wrong-password");
  await wrapper.get("form").trigger("submit");
  await flushPromises();
}

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

describe("LoginScreen", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it("shows structured message for invalid credentials", async () => {
    loginWithPasswordMock.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 401,
        data: {
          code: "INVALID_CREDENTIALS",
          message: "Неверная электронная почта или пароль",
          correlationId: "login-correlation-id",
        },
      },
    });

    const { default: LoginScreen } =
      await import("@/components/LoginScreen.vue");
    const wrapper = mount(LoginScreen);

    await fillAndSubmitLoginForm(wrapper);

    expect(loginWithPasswordMock).toHaveBeenCalledWith(
      "editor@example.local",
      "wrong-password",
    );
    const alert = wrapper.get('[role="alert"]');
    expect(alert.text()).toContain("Неверная электронная почта или пароль");
    expect(alert.text()).toContain("Проверьте электронную почту и пароль");
    expect(wrapper.get('[data-test="error-code"]').text()).toContain(
      "INVALID_CREDENTIALS",
    );
    expect(wrapper.get('[data-test="correlation-id"]').text()).toContain(
      "login-correlation-id",
    );
    expect(wrapper.find('[data-test="error-action"]').exists()).toBe(false);
  });

  it("uses generic fallback when invalid login response has no structured message", async () => {
    loginWithPasswordMock.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 401,
        data: {
          detail: "legacy detail should not be rendered",
        },
      },
    });

    const { default: LoginScreen } =
      await import("@/components/LoginScreen.vue");
    const wrapper = mount(LoginScreen);

    await fillAndSubmitLoginForm(wrapper);

    expect(wrapper.get('[role="alert"]').text()).toContain(
      "Сейчас не удалось выполнить вход.",
    );
    expect(wrapper.text()).not.toContain(
      "legacy detail should not be rendered",
    );
    expect(wrapper.find('[data-test="error-action"]').exists()).toBe(false);
  });

  it("keeps stable button layers while login is pending", async () => {
    const loginDeferred = createDeferred<void>();
    loginWithPasswordMock.mockReturnValue(loginDeferred.promise);

    const { default: LoginScreen } =
      await import("@/components/LoginScreen.vue");
    const wrapper = mount(LoginScreen);

    await wrapper.get('input[type="email"]').setValue("editor@example.local");
    await wrapper.get('input[type="password"]').setValue("editor-password");

    const button = wrapper.get('[data-test="login-submit"]');
    const idle = button.get('[data-ui-control-state="idle"]');
    const loading = button.get('[data-ui-control-state="loading"]');

    expect(button.classes()).toContain("submitButton");
    expect(idle.text()).toBe("Войти");
    expect(idle.classes()).not.toContain("isHidden");
    expect(loading.text()).toBe("Выполняем вход…");
    expect(loading.classes()).toContain("isHidden");

    await wrapper.get("form").trigger("submit");
    await nextTick();

    expect(loginWithPasswordMock).toHaveBeenCalledTimes(1);
    expect(button.attributes("disabled")).toBeDefined();
    expect(button.attributes("aria-busy")).toBe("true");
    expect(idle.classes()).toContain("isHidden");
    expect(loading.classes()).not.toContain("isHidden");

    await button.trigger("click");
    expect(loginWithPasswordMock).toHaveBeenCalledTimes(1);

    loginDeferred.resolve();
    await flushPromises();

    expect(button.attributes("disabled")).toBeUndefined();
    expect(button.attributes("aria-busy")).toBeUndefined();
    expect(idle.classes()).not.toContain("isHidden");
    expect(loading.classes()).toContain("isHidden");
  });
});
