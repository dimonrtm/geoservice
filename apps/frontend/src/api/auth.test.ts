import { beforeEach, describe, expect, it, vi } from "vitest";

import { fetchMe, login, logoutSession, refreshSession } from "@/api/auth";

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
      { withCredentials: true },
    );
  });

  it("refreshes the session with credentials and returns the auth response", async () => {
    const responseData = makeLoginResponse({ access_token: "new-token" });
    httpPostMock.mockResolvedValue({ data: responseData });

    const result = await refreshSession();

    expect(httpPostMock).toHaveBeenCalledWith(
      "/api/v1/auth/session/refresh",
      undefined,
      { withCredentials: true },
    );
    expect(result).toEqual(responseData);
  });

  it("logs out the session with credentials", async () => {
    httpPostMock.mockResolvedValue({ data: undefined });

    await logoutSession();

    expect(httpPostMock).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      undefined,
      { withCredentials: true },
    );
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
});

function makeLoginResponse(
  overrides: Partial<{
    access_token: string;
    token_type: string;
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
    user: {
      id: "user-1",
      email: "editor@example.com",
      role: "editor" as const,
    },
    ...overrides,
  };
}
