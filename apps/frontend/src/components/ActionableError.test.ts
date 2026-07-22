import {
  FolderOpen,
  LogIn,
  RefreshCw,
  RotateCcw,
  type LucideIcon,
} from "@lucide/vue";
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ActionableError from "@/components/ActionableError.vue";
import UiButton from "@/components/ui/UiButton.vue";
import type { ErrorActionId, ErrorPresentation } from "@/contracts/api-error";

const presentation: ErrorPresentation = {
  summary: "Рабочая версия не найдена.",
  guidance: "Откройте рабочую версию заново.",
  action: { id: "reopen", label: "Открыть заново" },
  diagnostics: {
    code: "EDIT_VERSION_NOT_FOUND",
    correlationId: "workspace-correlation-id",
  },
};

describe("ActionableError", () => {
  beforeEach(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  it("renders an alert with closed diagnostics", () => {
    const wrapper = mount(ActionableError, { props: { presentation } });

    expect(wrapper.get('[role="alert"]').text()).toContain(
      "Рабочая версия не найдена",
    );
    expect(wrapper.text()).toContain("Откройте рабочую версию заново");
    expect(wrapper.get("details").attributes("open")).toBeUndefined();
    expect(wrapper.get('[data-test="error-code"]').text()).toContain(
      "EDIT_VERSION_NOT_FOUND",
    );
    expect(wrapper.get('[data-test="correlation-id"]').text()).toContain(
      "workspace-correlation-id",
    );
  });

  it("emits the selected workflow action", async () => {
    const wrapper = mount(ActionableError, { props: { presentation } });

    await wrapper.get('[data-test="error-action"]').trigger("click");

    expect(wrapper.emitted("action")).toEqual([["reopen"]]);
  });

  it("copies the full correlation id and announces success", async () => {
    const wrapper = mount(ActionableError, { props: { presentation } });

    await wrapper.get('[data-test="copy-correlation-id"]').trigger("click");

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      "workspace-correlation-id",
    );
    expect(wrapper.get('[data-test="copy-status"]').text()).toBe(
      "Код обращения скопирован",
    );
    expect(
      wrapper.get('[data-test="copy-status"]').attributes("aria-live"),
    ).toBe("polite");
  });

  it("keeps the id visible when clipboard is unavailable", async () => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: undefined,
    });
    const wrapper = mount(ActionableError, { props: { presentation } });

    await wrapper.get('[data-test="copy-correlation-id"]').trigger("click");

    expect(wrapper.get('[data-test="correlation-id"]').text()).toContain(
      "workspace-correlation-id",
    );
    expect(wrapper.get('[data-test="copy-status"]').text()).toBe(
      "Не удалось скопировать код обращения",
    );
  });

  it("hides diagnostics and action when absent", () => {
    const wrapper = mount(ActionableError, {
      props: {
        presentation: {
          summary: "Ошибка сети",
          guidance: null,
          action: null,
          diagnostics: { code: null, correlationId: null },
        },
      },
    });

    expect(wrapper.find("details").exists()).toBe(false);
    expect(wrapper.find('[data-test="error-action"]').exists()).toBe(false);
  });

  it.each([
    ["retry", RotateCcw],
    ["refresh", RefreshCw],
    ["reopen", FolderOpen],
    ["sign-in", LogIn],
  ] satisfies [ErrorActionId, LucideIcon][])(
    "maps %s to the agreed Lucide icon",
    (actionId, expectedIcon) => {
      const actionPresentation: ErrorPresentation = {
        summary: "Ошибка операции",
        guidance: null,
        action: { id: actionId, label: "Выполнить действие" },
        diagnostics: { code: null, correlationId: null },
      };
      const wrapper = mount(ActionableError, {
        props: { presentation: actionPresentation },
      });

      expect(wrapper.getComponent(UiButton).props("icon")).toBe(expectedIcon);
    },
  );

  it("blocks duplicate clipboard writes while copy is pending", async () => {
    let resolveWriteText: (() => void) | undefined;
    const writeText = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveWriteText = resolve;
        }),
    );
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    const wrapper = mount(ActionableError, { props: { presentation } });
    const copyButton = wrapper.get('[data-test="copy-correlation-id"]');

    await copyButton.trigger("click");
    expect(copyButton.attributes("disabled")).toBeDefined();
    expect(copyButton.attributes("aria-busy")).toBe("true");
    expect(copyButton.attributes("aria-label")).toBe("Копируем код обращения");
    expect(
      copyButton.get('[data-ui-control-state="loading"]').classes(),
    ).not.toContain("isHidden");
    expect(copyButton.get('[data-ui-control-state="loading"]').text()).toBe(
      "Копируем…",
    );

    await copyButton.trigger("click");
    expect(writeText).toHaveBeenCalledTimes(1);

    resolveWriteText?.();
    await flushPromises();
    expect(copyButton.attributes("disabled")).toBeUndefined();
    expect(wrapper.get('[data-test="copy-status"]').text()).toBe(
      "Код обращения скопирован",
    );
  });
});
