import { beforeEach, describe, expect, it, vi } from "vitest";

const { authStoreMock, axiosCreateMock, responseUseMock } = vi.hoisted(() => {
  const responseUseMock = vi.fn();
  const axiosInstanceMock = {
    interceptors: {
      request: {
        use: vi.fn(),
      },
      response: {
        use: responseUseMock,
      },
    },
  };

  return {
    authStoreMock: {
      token: null as string | null,
      handleUnauthorizedResponse: vi.fn(),
      logout: vi.fn(),
    },
    axiosCreateMock: vi.fn(() => axiosInstanceMock),
    responseUseMock,
  };
});

vi.mock("axios", () => ({
  default: {
    create: axiosCreateMock,
  },
}));

vi.mock("@/pinia", () => ({
  pinia: {},
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: vi.fn(() => authStoreMock),
}));

describe("http api", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    authStoreMock.token = null;
  });

  it("delegates a 401 to the auth store without backend logout", async () => {
    await import("@/api/http");
    const rejectHandler = responseUseMock.mock.calls[0]?.[1] as (
      error: unknown,
    ) => Promise<never>;
    const error = { response: { status: 401 } };

    await expect(rejectHandler(error)).rejects.toBe(error);

    expect(authStoreMock.handleUnauthorizedResponse).toHaveBeenCalledWith(
      error,
    );
    expect(authStoreMock.logout).not.toHaveBeenCalled();
  });
});
