import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

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
    expect(wrapper.get(".errorMessage").text()).toBe(
      "Неверная электронная почта или пароль",
    );
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

    expect(wrapper.get(".errorMessage").text()).toBe(
      "Сейчас не удалось выполнить вход. Попробуйте ещё раз.",
    );
  });
});
