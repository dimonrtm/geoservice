import {
  AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { installBrowserAuthEnvironment } from "@/test/browserAuthEnvironment";
import { setActivePinia } from "pinia";
import { pinia } from "@/pinia";
import { http } from "./http";
import { useAuthStore } from "@/stores/auth";

const effects = vi.hoisted(() => ({
  reset: vi.fn(),
  suspendWorkspaceRecoveryForAccessLoss: vi.fn(),
  hideActor: vi.fn(),
  suspendActor: vi.fn(),
}));
vi.mock("@/stores/workOrders", () => ({ useWorkOrdersStore: () => effects }));
vi.mock("@/stores/workspaceRecovery", () => ({
  useWorkspaceRecoveryStore: () => effects,
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
function payload(id: string, token = id) {
  return {
    access_token: token,
    token_type: "bearer",
    session_id: `sid-${id}`,
    user: { id, email: `${id}@example.local`, role: "editor" as const },
  };
}
function response(
  config: InternalAxiosRequestConfig,
  id: string,
): AxiosResponse {
  return {
    config,
    data: payload(id),
    status: 200,
    statusText: "OK",
    headers: {},
  };
}
function failure(config: InternalAxiosRequestConfig, status: number) {
  return new AxiosError(
    "Ошибка запроса",
    status === 0 ? "ECONNABORTED" : "ERR_BAD_RESPONSE",
    config,
    undefined,
    status
      ? {
          config,
          status,
          statusText: "Error",
          headers: {},
          data: {
            code: status === 403 ? "USER_INACTIVE" : "AUTH_REQUIRED",
            message: "Сессия недействительна.",
          },
        }
      : undefined,
  );
}
beforeEach(() => {
  installBrowserAuthEnvironment();
  setActivePinia(pinia);
  useAuthStore().$reset();
  vi.resetAllMocks();
  effects.suspendActor.mockResolvedValue(undefined);
});
afterEach(() => useAuthStore().stopBrowserSessionSync());

it.each(
  [200, 401, 403, 503, 0].flatMap((status) =>
    [false, true].map((same) => ({ status, same })),
  ),
)(
  "старый refresh $status не меняет новый login (тот же actor: $same)",
  async ({ status, same }) => {
    const auth = useAuthStore();
    if (same)
      auth.setAuth("previous", payload("new").user, { sessionId: "sid-new" });
    const pending = deferred<AxiosResponse>();
    const started = deferred<InternalAxiosRequestConfig>();
    const loginResponse = deferred<AxiosResponse>();
    const loginStarted = deferred<InternalAxiosRequestConfig>();
    http.defaults.adapter = async (config) => {
      if (config.url?.endsWith("/session/refresh")) {
        started.resolve(config);
        return pending.promise;
      }
      loginStarted.resolve(config);
      return loginResponse.promise;
    };
    const restore = auth.restoreSession();
    const config = await started.promise;
    const login = auth.loginWithPassword("new@example.local", "synthetic");
    const snapshot = JSON.stringify(auth.$state);
    const calls = Object.values(effects).map((mock) => mock.mock.calls.length);
    if (status === 200)
      pending.resolve({
        ...response(config, same ? "new" : "old"),
        data: payload(same ? "new" : "old", "obsolete-restore-token"),
      });
    else pending.reject(failure(config, status));
    await restore;
    expect(JSON.stringify(auth.$state)).toBe(snapshot);
    expect(
      Object.values(effects).map((mock) => mock.mock.calls.length),
    ).toEqual(calls);
    loginResponse.resolve(response(await loginStarted.promise, "new"));
    await login;
  },
);

it.each(["request", "recovery", "failed"])(
  "новый login владеет состоянием: %s",
  async (phase) => {
    const auth = useAuthStore();
    auth.isReady = true;
    const old = deferred<AxiosResponse>();
    const started = deferred<InternalAxiosRequestConfig>();
    const next = deferred<AxiosResponse>();
    const loginStarted = deferred<InternalAxiosRequestConfig>();
    const recovery = deferred<void>();
    const recoveryStarted = deferred<void>();
    effects.suspendActor.mockImplementation(() => {
      recoveryStarted.resolve();
      return recovery.promise;
    });
    http.defaults.adapter = (config) => {
      if (config.url?.endsWith("/session/refresh")) {
        started.resolve(config);
        return old.promise;
      }
      loginStarted.resolve(config);
      return next.promise;
    };
    const restore = auth.restoreSession();
    const oldConfig = await started.promise;
    const login = auth.loginWithPassword("new", "synthetic");
    const handled = login.catch((error) => error);
    const beforeOldResponse = JSON.stringify(auth.$state);
    old.resolve(response(oldConfig, "old"));
    await restore;
    expect(JSON.stringify(auth.$state)).toBe(beforeOldResponse);
    const config = await loginStarted.promise;
    if (phase === "recovery") {
      next.resolve(response(config, "new"));
      await recoveryStarted.promise;
    }
    if (phase === "failed") {
      next.reject(failure(config, 503));
      await handled;
    }
    expect(auth.isRestoring).toBe(false);
    if (phase === "request") next.resolve(response(config, "new"));
    recovery.resolve();
    await handled;
    expect(auth.isReady).toBe(true);
  },
);

it.each(
  [200, 401, 403, 503, 0].flatMap((status) =>
    [false, true].map((runtime) => ({ status, runtime })),
  ),
)(
  "актуальный refresh $status завершается (runtime: $runtime)",
  async ({ status, runtime }) => {
    const auth = useAuthStore();
    if (runtime)
      auth.setAuth("current", payload("current").user, {
        sessionId: "sid-current",
      });
    http.defaults.adapter = async (config) => {
      if (status !== 200) throw failure(config, status);
      return response(config, "current");
    };
    await auth.restoreSession();
    expect(auth.isReady).toBe(true);
    expect(auth.isRestoring).toBe(false);
    expect(auth.isAuthenticated).toBe(status === 200);
    if (status === 401)
      expect(auth.sessionError?.action?.id ?? null).toBe(
        runtime ? "sign-in" : null,
      );
    if (status === 503 || status === 0)
      expect(auth.sessionError?.action?.id).toBe("retry");
    if (status === 403)
      expect(auth.sessionError?.guidance).toBe("Обратитесь к администратору.");
  },
);

it.each([false, true])(
  "обычный 401 сохраняет epoch-защиту (старый: %s)",
  async (stale) => {
    const auth = useAuthStore();
    auth.setAuth("first", payload("first").user, { sessionId: "sid-first" });
    const pending = deferred<AxiosResponse>();
    const started = deferred<InternalAxiosRequestConfig>();
    http.defaults.adapter = (config) => {
      if (config.url?.endsWith("/session/status"))
        return Promise.resolve({
          ...response(config, "first"),
          data: {
            session_id: JSON.parse(config.data).session_id,
            state: "active",
          },
        });
      started.resolve(config);
      return pending.promise;
    };
    const request = http.get("/work").catch((error) => error);
    const config = await started.promise;
    if (stale)
      auth.setAuth("new", payload("new").user, { sessionId: "sid-new" });
    pending.reject(failure(config, 401));
    await request;
    expect(auth.user?.id ?? null).toBe(stale ? "new" : null);
  },
);
