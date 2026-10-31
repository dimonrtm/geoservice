import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  fetchMe,
  fetchSessionStatus,
  login,
  logoutSession,
  refreshSession,
} from "@/api/auth";

const { httpGetMock, httpPostMock } = vi.hoisted(() => ({
  httpGetMock: vi.fn(),
  httpPostMock: vi.fn(),
}));

vi.mock("@/api/http", () => ({
  http: {
    get: httpGetMock,
    post: httpPostMock,
  },
}));

describe("auth api", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends credentials when logging in so the browser accepts the session cookie", async () => {
    httpPostMock.mockResolvedValue({ data: makeLoginResponse() });

    await login("editor@example.com", "editor-password");

    expect(httpPostMock).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      {
        email: "editor@example.com",
        password: "editor-password",
      },
      { withCredentials: true, authErrorHandling: "caller", authToken: null },
    );
  });

  it("refreshes the session with credentials and returns the auth response", async () => {
    const responseData = makeLoginResponse({ access_token: "new-token" });
    httpPostMock.mockResolvedValue({ data: responseData });

    const result = await refreshSession();

    expect(httpPostMock).toHaveBeenCalledWith(
      "/api/v1/auth/session/refresh",
      undefined,
      { withCredentials: true, authErrorHandling: "caller", authToken: null },
    );
    expect(result).toEqual(responseData);
  });

  it("logs out only the explicit session and returns confirmation", async () => {
    httpPostMock.mockResolvedValue({ data: { ok: true, session_id: "sid-a" } });

    const result = await logoutSession("sid-a");

    expect(httpPostMock).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      { session_id: "sid-a" },
      { withCredentials: true, authErrorHandling: "caller" },
    );
    expect(result).toEqual({ ok: true, session_id: "sid-a" });
  });

  it("fences refresh against a replacement cookie session", async () => {
    httpPostMock.mockResolvedValue({ data: makeLoginResponse() });
    await refreshSession("sid-a");
    expect(httpPostMock).toHaveBeenCalledWith(
      "/api/v1/auth/session/refresh",
      undefined,
      {
        withCredentials: true,
        authErrorHandling: "caller",
        authToken: null,
        headers: { "X-Expected-Session-Id": "sid-a" },
      },
    );
  });

  it("checks_status_with_short_timeout_and_explicit_old_bearer", async () => {
    httpPostMock.mockResolvedValue({
      data: { session_id: "sid-a", state: "ended" },
    });
    const result = await fetchSessionStatus("sid-a", "old-access");
    expect(httpPostMock).toHaveBeenCalledWith(
      "/api/v1/auth/session/status",
      { session_id: "sid-a" },
      {
        withCredentials: true,
        timeout: 1500,
        authErrorHandling: "caller",
        authToken: "old-access",
      },
    );
    expect(result).toEqual({ session_id: "sid-a", state: "ended" });
  });

  it("fetches the current user without credential options", async () => {
    const responseData = {
      user: {
        id: "user-1",
        email: "editor@example.com",
        role: "editor",
      },
    };
    httpGetMock.mockResolvedValue({ data: responseData });

    const result = await fetchMe();

    expect(httpGetMock).toHaveBeenCalledWith("/api/v1/auth/me");
    expect(result).toEqual(responseData);
  });

  it("coalesces_same_status_context_and_serializes_different_context", async () => {
    let finish!: (value: unknown) => void;
    httpPostMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    httpPostMock.mockResolvedValue({
      data: { session_id: "sid-b", state: "active" },
    });
    const first = fetchSessionStatus("sid-a", "old");
    const duplicate = fetchSessionStatus("sid-a", "old");
    const next = fetchSessionStatus("sid-b", "new");
    await Promise.resolve();
    expect(httpPostMock).toHaveBeenCalledTimes(1);
    finish({ data: { session_id: "sid-a", state: "ended" } });
    expect(await first).toEqual({ session_id: "sid-a", state: "ended" });
    expect(await duplicate).toEqual({ session_id: "sid-a", state: "ended" });
    expect(await next).toEqual({ session_id: "sid-b", state: "active" });
    expect(httpPostMock).toHaveBeenCalledTimes(2);
  });

  it("status_queue_keeps_only_latest_pending_context", async () => {
    let finish!: (value: unknown) => void;
    httpPostMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    httpPostMock.mockResolvedValue({
      data: { session_id: "sid-c", state: "active" },
    });
    const active = fetchSessionStatus("sid-a", "a");
    const superseded = fetchSessionStatus("sid-b", "b").catch((error) => error);
    const latest = fetchSessionStatus("sid-c", "c");
    await Promise.resolve();
    expect(httpPostMock).toHaveBeenCalledTimes(1);
    finish({ data: { session_id: "sid-a", state: "active" } });
    await active;
    expect(await superseded).toMatchObject({ code: "ERR_CANCELED" });
    expect(await latest).toEqual({ session_id: "sid-c", state: "active" });
    expect(httpPostMock.mock.calls.map((call) => call[1].session_id)).toEqual([
      "sid-a",
      "sid-c",
    ]);
  });

  it("fresh_status_skips_active_request_but_coalesces_pending_request", async () => {
    let finish!: (value: unknown) => void;
    httpPostMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    httpPostMock.mockResolvedValue({
      data: { session_id: "sid-a", state: "ended" },
    });
    const old = fetchSessionStatus("sid-a", "access-a");
    const fresh = fetchSessionStatus("sid-a", "access-a", {
      requireFreshRequest: true,
    });
    const duplicate = fetchSessionStatus("sid-a", "access-a", {
      requireFreshRequest: true,
    });
    await Promise.resolve();
    expect(httpPostMock).toHaveBeenCalledTimes(1);
    finish({ data: { session_id: "sid-a", state: "active" } });
    expect(await old).toEqual({ session_id: "sid-a", state: "active" });
    expect(await fresh).toEqual({ session_id: "sid-a", state: "ended" });
    expect(await duplicate).toEqual({ session_id: "sid-a", state: "ended" });
    expect(httpPostMock).toHaveBeenCalledTimes(2);
  });
});

function makeLoginResponse(
  overrides: Partial<{
    access_token: string;
    token_type: string;
    session_id: string;
    user: {
      id: string;
      email: string;
      role: "editor" | "reviewer";
    };
  }> = {},
) {
  return {
    access_token: "access-token",
    token_type: "bearer",
    session_id: "sid-a",
    user: {
      id: "user-1",
      email: "editor@example.com",
      role: "editor" as const,
    },
    ...overrides,
  };
}
