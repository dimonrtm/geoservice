import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { authStoreMock, axiosCreateMock, responseUseMock, requestUseMock } =
  vi.hoisted(() => {
    const responseUseMock = vi.fn();
    const requestUseMock = vi.fn();
    const axiosInstanceMock = {
      interceptors: {
        request: {
          use: requestUseMock,
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
        ensureSessionReady: vi.fn(),
        sessionId: null as string | null,
        sessionEpoch: 0,
      },
      axiosCreateMock: vi.fn(() => axiosInstanceMock),
      responseUseMock,
      requestUseMock,
    };
  });

vi.mock("axios", async (original) => ({
  default: {
    CanceledError: (await original<typeof import("axios")>()).CanceledError,
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
  it("explicit_null_disables_bearer_for_cookie_only_status", async () => {
    authStoreMock.token = "new-access";
    await import("@/api/http");
    const { AxiosHeaders } =
      await vi.importActual<typeof import("axios")>("axios");
    const handler = requestUseMock.mock.calls[0]?.[0] as (config: unknown) => {
      headers: InstanceType<typeof AxiosHeaders>;
    };
    const config = await handler({
      headers: new AxiosHeaders({ authorization: "Bearer old-access" }),
      authToken: null,
    });
    expect(config.headers.get("Authorization")).toBeUndefined();
  });
  it("preserves_explicit_old_bearer_instead_of_current_store_token", async () => {
    authStoreMock.token = "new-access";
    await import("@/api/http");
    const handler = requestUseMock.mock.calls[0]?.[0] as (config: unknown) => {
      headers: Record<string, string>;
    };
    const config = await handler({ headers: {}, authToken: "old-access" });
    expect(config.headers.Authorization).toBe("Bearer old-access");
  });
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
    authStoreMock.sessionId = null;
    authStoreMock.ensureSessionReady.mockResolvedValue(true);
  });

  it("protected_request_waits_for_fresh_session_gate", async () => {
    authStoreMock.token = "active";
    authStoreMock.sessionId = "sid-a";
    let release!: (value: boolean) => void;
    authStoreMock.ensureSessionReady.mockReturnValue(
      new Promise((resolve) => {
        release = resolve;
      }),
    );
    await import("@/api/http");
    const handler = requestUseMock.mock.calls[0]?.[0] as (
      config: unknown,
    ) => Promise<unknown>;
    let sent = false;
    const request = Promise.resolve(
      handler({ url: "/api/v1/work-orders", headers: {} }),
    ).then(() => {
      sent = true;
    });
    await Promise.resolve();
    expect(sent).toBe(false);
    release(true);
    await request;
    expect(sent).toBe(true);
  });
  it("failed_gate_blocks_protected_request", async () => {
    authStoreMock.token = "active";
    authStoreMock.sessionId = "sid-a";
    authStoreMock.ensureSessionReady.mockResolvedValue(false);
    await import("@/api/http");
    const handler = requestUseMock.mock.calls[0]?.[0] as (
      config: unknown,
    ) => Promise<unknown>;
    await expect(
      handler({ url: "/api/v1/work-orders", headers: {} }),
    ).rejects.toMatchObject({ code: "ERR_CANCELED" });
  });
  it("actor_change_while_waiting_for_gate_cancels_old_request", async () => {
    authStoreMock.token = "active";
    authStoreMock.sessionId = "sid-a";
    authStoreMock.sessionEpoch = 1;
    let release!: (active: boolean) => void;
    authStoreMock.ensureSessionReady.mockReturnValue(
      new Promise((resolve) => {
        release = resolve;
      }),
    );
    await import("@/api/http");
    const handler = requestUseMock.mock.calls[0]?.[0] as (
      config: unknown,
    ) => Promise<unknown>;
    const result = handler({ url: "/api/v1/work-orders", headers: {} }).catch(
      (error) => error,
    );
    authStoreMock.sessionEpoch = 2;
    release(true);
    expect(await result).toMatchObject({ code: "ERR_CANCELED" });
  });
  it.each(["login", "session/refresh", "logout", "session/status"])(
    "auth_call_%s_does_not_recurse_into_gate",
    async (path) => {
      authStoreMock.token = "active";
      authStoreMock.sessionId = "sid-a";
      authStoreMock.ensureSessionReady.mockRejectedValue(
        new Error("recursive auth"),
      );
      await import("@/api/http");
      const handler = requestUseMock.mock.calls[0]?.[0] as (
        config: unknown,
      ) => Promise<{ headers: Record<string, string> }>;
      const result = await handler({
        url: `/api/v1/auth/${path}`,
        headers: {},
        authToken: "old",
      });
      expect(result.headers.Authorization).toBe("Bearer old");
    },
  );

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
