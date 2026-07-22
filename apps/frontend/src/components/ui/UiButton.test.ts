import { LoaderCircle, Play } from "@lucide/vue";
import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import UiButton from "@/components/ui/UiButton.vue";

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
});
