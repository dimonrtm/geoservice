import { afterEach, describe, expect, it } from "vitest";
import { mount, type VueWrapper } from "@vue/test-utils";

import WorkspaceDetailsPanel from "@/components/WorkspaceDetailsPanel.vue";
import type {
  WorkOrderSummary,
  WorkspaceResponse,
} from "@/contracts/work-orders";

const mountedWrappers: VueWrapper[] = [];

type PanelTestProps = {
  workOrder: WorkOrderSummary;
  workspace: WorkspaceResponse | null;
  isOpening: boolean;
  isOpenActionDisabled: boolean;
  errorMessage: string | null;
};

function workOrder(
  overrides: Partial<WorkOrderSummary> = {},
): WorkOrderSummary {
  return {
    id: "wo-1",
    code: "WO-001",
    title: "Проверка участка фидера",
    description: "Проверить оборудование внутри области работ",
    status: "assigned",
    ...overrides,
  };
}

function workspace(): WorkspaceResponse {
  return {
    workOrder: {
      id: "wo-1",
      code: "WO-001",
      title: "Проверка участка фидера",
      description: "Не показывать после открытия",
      status: "in_progress",
      scope: {
        aoi: {
          id: "aoi-1",
          name: "Рабочая область WO-001",
          description: null,
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [65.5, 44.8],
                [65.54, 44.8],
                [65.54, 44.84],
                [65.5, 44.84],
                [65.5, 44.8],
              ],
            ],
          },
          extent: [65.5, 44.8, 65.54, 44.84],
        },
      },
      editVersion: {
        id: "ev-secret-1",
        status: "open",
        baseNetworkRevision: 7,
        features: {
          type: "FeatureCollection",
          features: [
            {
              id: "feature-1",
              type: "Feature",
              geometry: { type: "Point", coordinates: [65.52, 44.82] },
              properties: {},
            },
            {
              id: "feature-2",
              type: "Feature",
              geometry: { type: "Point", coordinates: [65.53, 44.83] },
              properties: {},
            },
          ],
        },
        associations: [
          {
            id: "assoc-1",
            fromFeatureId: "feature-1",
            toFeatureId: "feature-2",
            associationType: "connected_to",
            version: 1,
          },
        ],
      },
    },
  };
}

function mountPanel(props: Partial<PanelTestProps> = {}) {
  const wrapper = mount(WorkspaceDetailsPanel, {
    props: {
      workOrder: workOrder(),
      workspace: null,
      isOpening: false,
      isOpenActionDisabled: false,
      errorMessage: null,
      ...props,
    },
    attachTo: document.body,
  });
  mountedWrappers.push(wrapper);
  return wrapper;
}

afterEach(() => {
  for (const wrapper of mountedWrappers.splice(0)) {
    wrapper.unmount();
  }
});

describe("WorkspaceDetailsPanel", () => {
  it("renders assigned preview and emits open", async () => {
    const wrapper = mountPanel();

    expect(wrapper.get('[data-test="workspace-code"]').text()).toBe("WO-001");
    expect(wrapper.get('[data-test="workspace-details-title"]').text()).toBe(
      "Проверка участка фидера",
    );
    expect(wrapper.get('[data-test="workspace-status"]').text()).toBe(
      "Назначен",
    );
    expect(wrapper.get('[data-test="workspace-description"]').text()).toContain(
      "Проверить оборудование",
    );
    expect(wrapper.get('[data-test="workspace-open-action"]').text()).toBe(
      "Начать",
    );

    await wrapper.get('[data-test="workspace-open-action"]').trigger("click");
    expect(wrapper.emitted("open")).toHaveLength(1);
  });

  it("localizes in-progress preview and exposes loading semantics", () => {
    const wrapper = mountPanel({
      workOrder: workOrder({ status: "in_progress" }),
      isOpening: true,
      isOpenActionDisabled: true,
    });

    expect(wrapper.get('[data-test="workspace-status"]').text()).toBe(
      "В работе",
    );
    expect(wrapper.get('[data-test="workspace-open-action"]').text()).toBe(
      "Открываем…",
    );
    expect(
      wrapper.get('[data-test="workspace-open-action"]').attributes("disabled"),
    ).toBeDefined();
    expect(
      wrapper
        .get('[data-test="workspace-details-panel"]')
        .attributes("aria-busy"),
    ).toBe("true");
  });

  it("shows continue for an in-progress work order in the normal state", () => {
    const wrapper = mountPanel({
      workOrder: workOrder({ status: "in_progress" }),
      isOpening: false,
    });

    expect(wrapper.get('[data-test="workspace-open-action"]').text()).toBe(
      "Продолжить",
    );
  });

  it("keeps the normal label while another work order is opening", () => {
    const wrapper = mountPanel({
      isOpening: false,
      isOpenActionDisabled: true,
    });

    expect(wrapper.get('[data-test="workspace-open-action"]').text()).toBe(
      "Начать",
    );
    expect(
      wrapper.get('[data-test="workspace-open-action"]').attributes("disabled"),
    ).toBeDefined();
    expect(
      wrapper
        .get('[data-test="workspace-details-panel"]')
        .attributes("aria-busy"),
    ).toBe("false");
  });

  it("renders an actionable alert in preview", () => {
    const wrapper = mountPanel({
      errorMessage: "Не удалось открыть workspace",
    });

    const error = wrapper.get('[data-test="workspace-open-error"]');
    const action = wrapper.get('[data-test="workspace-open-action"]');
    expect(error.text()).toBe("Не удалось открыть workspace");
    expect(error.attributes("role")).toBe("alert");
    expect(action.attributes("aria-describedby")).toBe("workspace-open-error");
  });

  it("renders localized workspace details without technical values", () => {
    const wrapper = mountPanel({
      workOrder: workOrder({ status: "in_progress" }),
      workspace: workspace(),
    });

    expect(wrapper.get('[data-test="workspace-aoi"]').text()).toBe(
      "Рабочая область WO-001",
    );
    expect(wrapper.get('[data-test="workspace-version-status"]').text()).toBe(
      "Открыта",
    );
    expect(wrapper.get('[data-test="workspace-base-revision"]').text()).toBe(
      "7",
    );
    expect(wrapper.get('[data-test="workspace-feature-count"]').text()).toBe(
      "2",
    );
    expect(
      wrapper.get('[data-test="workspace-association-count"]').text(),
    ).toBe("1");
    expect(wrapper.find('[data-test="workspace-description"]').exists()).toBe(
      false,
    );
    expect(wrapper.find('[data-test="workspace-open-action"]').exists()).toBe(
      false,
    );
    expect(wrapper.text()).not.toContain("ev-secret-1");
    expect(wrapper.text()).not.toContain("in_progress");
    expect(wrapper.text()).not.toContain("open");
  });

  it("exposes focusHeading for the orchestration boundary", () => {
    const wrapper = mountPanel({ workspace: workspace() });
    const exposed = wrapper.vm as unknown as { focusHeading(): void };

    exposed.focusHeading();

    expect(document.activeElement).toBe(
      wrapper.get('[data-test="workspace-details-title"]').element,
    );
  });
});
