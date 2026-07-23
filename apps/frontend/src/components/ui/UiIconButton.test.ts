import { LogOut, RefreshCw } from "@lucide/vue";
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import UiIconButton from "@/components/ui/UiIconButton.vue";

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("UiIconButton", () => {
  it("connects a native icon-only button to a persistent tooltip node", () => {
    const wrapper = mount(UiIconButton, {
      props: {
        icon: LogOut,
        label: "Выйти",
        tooltip: "Выйти из GeoService",
        tooltipAlign: "end",
      },
      attrs: { "data-test": "logout-icon" },
    });

    const button = wrapper.get('[data-test="logout-icon"]');
    const tooltip = wrapper.get('[role="tooltip"]');
    expect(button.element.tagName).toBe("BUTTON");
    expect(button.attributes("type")).toBe("button");
    expect(button.attributes("aria-label")).toBe("Выйти");
    expect(button.attributes("aria-describedby")).toBe(
      tooltip.attributes("id"),
    );
    expect(tooltip.text()).toBe("Выйти из GeoService");
    expect(tooltip.attributes("data-state")).toBe("closed");
    expect(tooltip.classes()).toContain("uiControlTooltipEnd");
    expect(button.get("svg").attributes("aria-hidden")).toBe("true");
  });

  it("opens after hover delay and stays open until the shared region is left", async () => {
    vi.useFakeTimers();
    const wrapper = mount(UiIconButton, {
      props: {
        icon: RefreshCw,
        label: "Обновить",
        tooltip: "Обновить список назначенных нарядов",
      },
    });

    const root = wrapper.get(".uiIconButtonRoot");
    const button = wrapper.get("button");
    const tooltip = wrapper.get('[role="tooltip"]');

    await root.trigger("mouseenter");
    vi.advanceTimersByTime(499);
    await nextTick();
    expect(tooltip.attributes("data-state")).toBe("closed");

    vi.advanceTimersByTime(1);
    await nextTick();
    expect(tooltip.attributes("data-state")).toBe("open");

    await button.trigger("mouseout", { relatedTarget: tooltip.element });
    await tooltip.trigger("mouseenter");
    expect(tooltip.attributes("data-state")).toBe("open");

    await root.trigger("mouseleave");
    expect(tooltip.attributes("data-state")).toBe("closed");
  });

  it("opens immediately on focus and closes on Escape", async () => {
    vi.useFakeTimers();
    const wrapper = mount(UiIconButton, {
      props: {
        icon: LogOut,
        label: "Выйти",
        tooltip: "Выйти из GeoService",
      },
    });

    const button = wrapper.get("button");
    const tooltip = wrapper.get('[role="tooltip"]');
    await button.trigger("focus");
    expect(tooltip.attributes("data-state")).toBe("open");

    await button.trigger("keydown", { key: "Escape" });
    expect(tooltip.attributes("data-state")).toBe("closed");

    await button.trigger("blur");
    expect(tooltip.attributes("data-state")).toBe("closed");
  });

  it("uses loading semantics and prevents repeated action", async () => {
    const onClick = vi.fn();
    const wrapper = mount(UiIconButton, {
      props: {
        icon: RefreshCw,
        label: "Обновить",
        tooltip: "Обновить список назначенных нарядов",
        loading: true,
        loadingLabel: "Обновление списка нарядов",
      },
      attrs: { onClick },
    });

    const button = wrapper.get("button");
    expect(button.attributes("aria-label")).toBe("Обновление списка нарядов");
    expect(button.attributes("aria-busy")).toBe("true");
    expect(button.attributes("disabled")).toBeDefined();
    expect(button.get("svg").classes()).toContain("uiControlLoader");

    await button.trigger("click");
    expect(onClick).not.toHaveBeenCalled();
  });

  it("keeps the idle accessible state for an empty loading label", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const wrapper = mount(UiIconButton, {
      props: {
        icon: RefreshCw,
        label: "Обновить",
        tooltip: "Обновить список назначенных нарядов",
        loading: true,
        loadingLabel: " ",
      },
    });

    const button = wrapper.get("button");
    expect(warn).toHaveBeenCalledWith(expect.stringContaining("loadingLabel"));
    expect(button.attributes("disabled")).toBeDefined();
    expect(button.attributes("aria-busy")).toBe("true");
    expect(button.attributes("aria-label")).toBe("Обновить");
    expect(button.get("svg").classes()).not.toContain("uiControlLoader");
  });
});
