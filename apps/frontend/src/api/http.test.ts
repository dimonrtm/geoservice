import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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
  it.each([401, 403, 503])(
    "caller обрабатывает отказ %s самостоятельно",
    async (status) => {
      await import("@/api/http");
      const rejectHandler = responseUseMock.mock.calls[0]?.[1] as (
        error: unknown,
      ) => Promise<never>;
      const error = {
        config: { authErrorHandling: "caller", sessionEpoch: 7 },
        response: { status, data: { code: "USER_INACTIVE" } },
      };
      await expect(rejectHandler(error)).rejects.toBe(error);
      expect(authStoreMock.handleUnauthorizedResponse).not.toHaveBeenCalled();
    },
  );
  it.each(["ROLE_NOT_ALLOWED", "USER_INACTIVE"])(
    "обычный 403 %s делегируется с epoch",
    async (code) => {
      await import("@/api/http");
      const rejectHandler = responseUseMock.mock.calls[0]?.[1] as (
        error: unknown,
      ) => Promise<never>;
      const error = {
        config: { sessionEpoch: 7 },
        response: { status: 403, data: { code } },
      };
      await expect(rejectHandler(error)).rejects.toBe(error);
      expect(authStoreMock.handleUnauthorizedResponse).toHaveBeenCalledWith(
        error,
        7,
      );
    },
  );
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    authStoreMock.token = null;
  });

  it("использует origin страницы в production без API override", async () => {
    vi.stubEnv("PROD", true);
    vi.stubEnv("VITE_API_BASE_URL", undefined);
    await import("@/api/http");
    expect(axiosCreateMock).toHaveBeenCalledWith({
      baseURL: window.location.origin,
      timeout: 30000,
    });
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
      undefined,
    );
    expect(authStoreMock.logout).not.toHaveBeenCalled();
  });
});
