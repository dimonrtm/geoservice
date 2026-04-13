import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const loginMock = vi.fn();
const fetchMeMock = vi.fn();

vi.mock("@/api/auth", () => ({
  login: loginMock,
  fetchMe: fetchMeMock,
}));

function createLocalStorageMock() {
  const storage = new Map<string, string>();

  return {
    getItem: vi.fn((key: string) => storage.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => {
      storage.set(key, value);
    }),
    removeItem: vi.fn((key: string) => {
      storage.delete(key);
    }),
    clear: vi.fn(() => {
      storage.clear();
    }),
  };
}

describe("auth store", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    setActivePinia(createPinia());

    const localStorageMock = createLocalStorageMock();
    vi.stubGlobal("localStorage", localStorageMock);
  });

  it("stores token and full user object after successful login", async () => {
    loginMock.mockResolvedValue({
      access_token: "token-1",
      token_type: "bearer",
      user: {
        id: "user-1",
        email: "editor@example.com",
        role: "editor",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.loginWithPassword("editor@example.com", "editor-password");

    expect(store.token).toBe("token-1");
    expect(store.user).toEqual({
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    });
    expect(store.isAuthenticated).toBe(true);
  });

  it("restores the user through /me when token exists", async () => {
    localStorage.setItem("access_token", "token-1");
    localStorage.setItem(
      "auth_user",
      JSON.stringify({
        id: "stale-user",
        email: "stale@example.com",
        role: "viewer",
      }),
    );
    fetchMeMock.mockResolvedValue({
      user: {
        id: "user-2",
        email: "viewer@example.com",
        role: "viewer",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(store.isReady).toBe(true);
    expect(store.sessionError).toBeNull();
    expect(store.user).toEqual({
      id: "user-2",
      email: "viewer@example.com",
      role: "viewer",
    });
  });

  it("keeps token and reports temporary error when /me fails without 401", async () => {
    localStorage.setItem("access_token", "token-1");
    fetchMeMock.mockRejectedValue({
      isAxiosError: true,
      response: { status: 503 },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(store.token).toBe("token-1");
    expect(store.sessionError).toBe(
      "Сейчас не удалось восстановить сессию. Попробуйте ещё раз.",
    );
  });
});
