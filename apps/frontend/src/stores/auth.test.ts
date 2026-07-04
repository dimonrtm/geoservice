import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const {
  loginMock,
  fetchMeMock,
  refreshSessionMock,
  logoutSessionMock,
  resetWorkOrdersMock,
} = vi.hoisted(() => ({
  loginMock: vi.fn(),
  fetchMeMock: vi.fn(),
  refreshSessionMock: vi.fn(),
  logoutSessionMock: vi.fn(),
  resetWorkOrdersMock: vi.fn(),
}));

vi.mock("@/api/auth", () => ({
  login: loginMock,
  fetchMe: fetchMeMock,
  refreshSession: refreshSessionMock,
  logoutSession: logoutSessionMock,
}));

vi.mock("@/stores/workOrders", () => ({
  useWorkOrdersStore: () => ({
    reset: resetWorkOrdersMock,
  }),
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

const SESSION_RETRY_MESSAGE =
  "Сейчас не удалось восстановить сессию. Попробуйте ещё раз.";

function expectAuthLocalStorageNotUsed() {
  expect(localStorage.getItem).not.toHaveBeenCalled();
  expect(localStorage.setItem).not.toHaveBeenCalled();
  expect(localStorage.removeItem).not.toHaveBeenCalled();
  expect(localStorage.clear).not.toHaveBeenCalled();
}

function clearLocalStorageMockCalls() {
  vi.mocked(localStorage.getItem).mockClear();
  vi.mocked(localStorage.setItem).mockClear();
  vi.mocked(localStorage.removeItem).mockClear();
  vi.mocked(localStorage.clear).mockClear();
}

describe("auth store", () => {
  beforeEach(() => {
    vi.resetModules();
    loginMock.mockReset();
    fetchMeMock.mockReset();
    refreshSessionMock.mockReset();
    logoutSessionMock.mockReset();
    resetWorkOrdersMock.mockReset();
    setActivePinia(createPinia());

    const localStorageMock = createLocalStorageMock();
    vi.stubGlobal("localStorage", localStorageMock);
  });

  it("stores access token only in memory after successful login", async () => {
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
    expectAuthLocalStorageNotUsed();
  });

  it("clearLocalSession clears memory without calling backend logout", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    };
    store.sessionError = SESSION_RETRY_MESSAGE;
    store.isReady = false;
    store.isRestoring = true;

    store.clearLocalSession();
    store.clearLocalSession();

    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(store.sessionError).toBeNull();
    expect(store.isReady).toBe(true);
    expect(store.isRestoring).toBe(false);
    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
    expect(logoutSessionMock).not.toHaveBeenCalled();
    expectAuthLocalStorageNotUsed();
  });

  it("clears memory synchronously and blocks readiness until backend logout resolves", async () => {
    let resolveLogout: (() => void) | undefined;
    logoutSessionMock.mockReturnValue(
      new Promise<void>((resolve) => {
        resolveLogout = resolve;
      }),
    );

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    };
    store.sessionError = SESSION_RETRY_MESSAGE;
    store.isReady = true;
    store.isRestoring = true;

    const logoutPromise = store.logout();

    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(store.sessionError).toBeNull();
    expect(store.isReady).toBe(false);
    expect(store.isRestoring).toBe(false);
    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
    expect(logoutSessionMock).toHaveBeenCalledTimes(1);
    expectAuthLocalStorageNotUsed();

    resolveLogout?.();
    await logoutPromise;

    expect(store.isReady).toBe(true);
    expect(store.isRestoring).toBe(false);
  });

  it("resets work orders on logout only when user id changes to null", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    };

    await store.logout();
    await store.logout();

    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
  });

  it("does not reset work orders when setAuth keeps the same user id", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "old@example.com",
      role: "editor",
    };

    store.setAuth("token-2", {
      id: "user-1",
      email: "new-email@example.com",
      role: "editor",
    });

    expect(resetWorkOrdersMock).not.toHaveBeenCalled();
  });

  it("resets work orders when setAuth changes user id", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    };

    store.setAuth("token-2", {
      id: "user-2",
      email: "other-editor@example.com",
      role: "editor",
    });

    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
  });

  it("restores session through refresh endpoint without reading localStorage token", async () => {
    localStorage.setItem("access_token", "token-1");
    localStorage.setItem(
      "auth_user",
      JSON.stringify({
        id: "stale-user",
        email: "stale@example.com",
        role: "editor",
      }),
    );
    clearLocalStorageMockCalls();
    refreshSessionMock.mockResolvedValue({
      access_token: "token-2",
      token_type: "bearer",
      user: {
        id: "user-2",
        email: "marina.reviewer@example.local",
        role: "reviewer",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(localStorage.getItem).not.toHaveBeenCalledWith("access_token");
    expect(refreshSessionMock).toHaveBeenCalledTimes(1);
    expect(store.token).toBe("token-2");
    expect(store.user).toEqual({
      id: "user-2",
      email: "marina.reviewer@example.local",
      role: "reviewer",
    });
    expect(store.sessionError).toBeNull();
    expect(store.isReady).toBe(true);
    expect(localStorage.setItem).not.toHaveBeenCalled();
    expect(localStorage.removeItem).not.toHaveBeenCalled();
    expect(localStorage.clear).not.toHaveBeenCalled();
  });

  it("does not reset work orders when restoreSession refreshes the same user id", async () => {
    refreshSessionMock.mockResolvedValue({
      access_token: "token-2",
      token_type: "bearer",
      user: {
        id: "user-1",
        email: "fresh@example.com",
        role: "editor",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "cached@example.com",
      role: "editor",
    };

    await store.restoreSession();

    expect(store.user?.id).toBe("user-1");
    expect(resetWorkOrdersMock).not.toHaveBeenCalled();
  });

  it("resets work orders when restoreSession refreshes a different user id", async () => {
    refreshSessionMock.mockResolvedValue({
      access_token: "token-2",
      token_type: "bearer",
      user: {
        id: "user-2",
        email: "fresh@example.com",
        role: "editor",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "cached@example.com",
      role: "editor",
    };

    await store.restoreSession();

    expect(store.user?.id).toBe("user-2");
    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
  });

  it("treats refresh 401 as logged out without session error", async () => {
    refreshSessionMock.mockRejectedValue({
      isAxiosError: true,
      response: { status: 401 },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(store.sessionError).toBeNull();
    expect(store.isReady).toBe(true);
  });

  it("keeps retry UX when refresh fails without 401", async () => {
    refreshSessionMock.mockRejectedValue({
      isAxiosError: true,
      response: { status: 503 },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(store.sessionError).toBe(SESSION_RETRY_MESSAGE);
    expect(store.isReady).toBe(true);
  });

  it("resets work orders when restoreSession logs out the current user", async () => {
    refreshSessionMock.mockRejectedValue({
      isAxiosError: true,
      response: { status: 401 },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "cached@example.com",
      role: "editor",
    };

    await store.restoreSession();

    expect(store.user).toBeNull();
    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
  });

  it("calls backend logout and clears memory state", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    };

    await store.logout();

    expect(logoutSessionMock).toHaveBeenCalledTimes(1);
    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(store.sessionError).toBeNull();
    expect(store.isReady).toBe(true);
    expect(store.isRestoring).toBe(false);
    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
    expectAuthLocalStorageNotUsed();
  });

  it("re-enables readiness when backend logout fails", async () => {
    let rejectLogout: ((error: Error) => void) | undefined;
    logoutSessionMock.mockReturnValue(
      new Promise<void>((_, reject) => {
        rejectLogout = reject;
      }),
    );

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();
    store.token = "token-1";
    store.user = {
      id: "user-1",
      email: "editor@example.com",
      role: "editor",
    };
    store.isReady = true;

    const logoutPromise = store.logout();

    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(store.isReady).toBe(false);

    rejectLogout?.(new Error("logout failed"));
    await logoutPromise;

    expect(logoutSessionMock).toHaveBeenCalledTimes(1);
    expect(store.token).toBeNull();
    expect(store.user).toBeNull();
    expect(store.sessionError).toBeNull();
    expect(store.isReady).toBe(true);
    expect(store.isRestoring).toBe(false);
    expect(resetWorkOrdersMock).toHaveBeenCalledTimes(1);
    expectAuthLocalStorageNotUsed();
  });

  it("does not call fetchMe when restoring a session", async () => {
    localStorage.setItem("access_token", "token-1");
    localStorage.setItem(
      "auth_user",
      JSON.stringify({
        id: "stale-user",
        email: "stale@example.com",
        role: "editor",
      }),
    );
    clearLocalStorageMockCalls();
    refreshSessionMock.mockResolvedValue({
      access_token: "token-2",
      token_type: "bearer",
      user: {
        id: "user-2",
        email: "marina.reviewer@example.local",
        role: "reviewer",
      },
    });

    const { useAuthStore } = await import("@/stores/auth");
    const store = useAuthStore();

    await store.restoreSession();

    expect(fetchMeMock).not.toHaveBeenCalled();
  });
});
