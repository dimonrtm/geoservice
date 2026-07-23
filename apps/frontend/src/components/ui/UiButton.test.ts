import { LoaderCircle, Play } from "@lucide/vue";
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import UiButton from "@/components/ui/UiButton.vue";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("UiButton", () => {
  it("renders icon and text through a native button", () => {
    const wrapper = mount(UiButton, {
      props: { icon: Play, variant: "primary" },
      attrs: { type: "submit", "data-test": "primary-action" },
      slots: { default: "Начать" },
    });

    const button = wrapper.get('[data-test="primary-action"]');
    expect(button.element.tagName).toBe("BUTTON");
    expect(button.attributes("type")).toBe("submit");
    expect(button.classes()).toContain("uiControlPrimary");
    expect(button.get('[data-ui-control-state="idle"]').text()).toBe("Начать");
    expect(button.find('[data-ui-control-state="loading"]').exists()).toBe(
      false,
    );
    expect(
      button
        .findAll("svg")
        .every((icon) => icon.attributes("aria-hidden") === "true"),
    ).toBe(true);
  });

  it("keeps idle and loading layers stable while blocking repeated clicks", async () => {
    const onClick = vi.fn();
    const wrapper = mount(UiButton, {
      props: {
        icon: Play,
        loading: true,
        loadingLabel: "Открываем…",
      },
      attrs: { onClick },
      slots: { default: "Продолжить" },
    });

    const button = wrapper.get("button");
    expect(button.attributes("type")).toBe("button");
    expect(button.attributes("disabled")).toBeDefined();
    expect(button.attributes("aria-busy")).toBe("true");
    expect(button.get('[data-ui-control-state="idle"]').classes()).toContain(
      "isHidden",
    );
    expect(
      button.get('[data-ui-control-state="loading"]').classes(),
    ).not.toContain("isHidden");
    expect(button.get('[data-ui-control-state="loading"]').text()).toBe(
      "Открываем…",
    );
    expect(wrapper.findComponent(LoaderCircle).exists()).toBe(true);

    await button.trigger("click");
    expect(onClick).not.toHaveBeenCalled();
  });

  it("mounts the declared loading layer before loading starts", () => {
    const wrapper = mount(UiButton, {
      props: {
        icon: Play,
        loading: false,
        loadingLabel: "Открываем…",
      },
      slots: { default: "Продолжить" },
    });

    const button = wrapper.get("button");
    const idle = button.get('[data-ui-control-state="idle"]');
    const loading = button.get('[data-ui-control-state="loading"]');

    expect(idle.classes()).not.toContain("isHidden");
    expect(idle.attributes("aria-hidden")).toBeUndefined();
    expect(loading.classes()).toContain("isHidden");
    expect(loading.attributes("aria-hidden")).toBe("true");
    expect(loading.text()).toBe("Открываем…");
  });

  it("keeps idle content visible and warns for an empty loading label", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const wrapper = mount(UiButton, {
      props: {
        icon: Play,
        loading: true,
        loadingLabel: "   ",
      },
      slots: { default: "Продолжить" },
    });

    const button = wrapper.get("button");
    expect(warn).toHaveBeenCalledWith(expect.stringContaining("loadingLabel"));
    expect(button.attributes("disabled")).toBeDefined();
    expect(button.attributes("aria-busy")).toBe("true");
    expect(
      button.get('[data-ui-control-state="idle"]').classes(),
    ).not.toContain("isHidden");
    expect(button.find('[data-ui-control-state="loading"]').exists()).toBe(
      false,
    );
    expect(wrapper.findComponent(LoaderCircle).exists()).toBe(false);
  });

  it("exposes constrained text hooks for both stable labels", () => {
    const wrapper = mount(UiButton, {
      props: {
        icon: Play,
        loading: false,
        loadingLabel: "Предметная длинная loading-подпись",
      },
      slots: { default: "Короткое действие" },
    });

    const button = wrapper.get("button");
    const labels = button.findAll(".uiControlLabel");

    expect(button.classes()).toContain("uiControlText");
    expect(labels).toHaveLength(2);
    expect(labels[0]?.text()).toBe("Короткое действие");
    expect(labels[1]?.text()).toBe("Предметная длинная loading-подпись");
  });
});
