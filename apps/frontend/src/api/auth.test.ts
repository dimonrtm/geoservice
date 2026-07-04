import { beforeEach, describe, expect, it, vi } from "vitest";

import { fetchMe, login, logoutSession, refreshSession } from "@/api/auth";
import { http } from "@/api/http";

vi.mock("@/api/http", () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const httpMock = vi.mocked(http);

describe("auth api", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends credentials when logging in so the browser accepts the session cookie", async () => {
    httpMock.post.mockResolvedValue({ data: makeLoginResponse() });

    await login("editor@example.com", "editor-password");

    expect(httpMock.post).toHaveBeenCalledWith(
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
    httpMock.post.mockResolvedValue({ data: responseData });

    const result = await refreshSession();

    expect(httpMock.post).toHaveBeenCalledWith(
      "/api/v1/auth/session/refresh",
      undefined,
      { withCredentials: true },
    );
    expect(result).toEqual(responseData);
  });

  it("logs out the session with credentials", async () => {
    httpMock.post.mockResolvedValue({ data: undefined });

    await logoutSession();

    expect(httpMock.post).toHaveBeenCalledWith(
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
    httpMock.get.mockResolvedValue({ data: responseData });

    const result = await fetchMe();

    expect(httpMock.get).toHaveBeenCalledWith("/api/v1/auth/me");
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
