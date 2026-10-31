import { http } from "@/api/http";
import type {
  BrowserSessionStatus,
  SessionStatusOptions,
} from "@/auth/browserSessionTypes";
import { CanceledError } from "axios";

export type AuthRole = "editor" | "reviewer";

export type AuthUser = {
  id: string;
  email: string;
  role: AuthRole;
};

export type AuthLoginResponse = {
  access_token: string;
  token_type: string;
  session_id: string;
  user: AuthUser;
};

export type AuthMeResponse = {
  user: AuthUser;
};

export async function login(email: string, password: string) {
  const response = await http.post<AuthLoginResponse>(
    "/api/v1/auth/login",
    {
      email,
      password,
    },
    { withCredentials: true, authErrorHandling: "caller", authToken: null },
  );
  return response.data;
}

export async function refreshSession(expectedSessionId?: string) {
  const response = await http.post<AuthLoginResponse>(
    "/api/v1/auth/session/refresh",
    undefined,
    {
      withCredentials: true,
      authErrorHandling: "caller",
      authToken: null,
      ...(expectedSessionId
        ? { headers: { "X-Expected-Session-Id": expectedSessionId } }
        : {}),
    },
  );
  return response.data;
}

export async function logoutSession(sessionId: string) {
  const response = await http.post<{ ok: true; session_id: string }>(
    "/api/v1/auth/logout",
    { session_id: sessionId },
    {
      withCredentials: true,
      authErrorHandling: "caller",
    },
  );
  return response.data;
}

type StatusJob = {
  sessionId: string;
  accessToken?: string;
  promise: Promise<BrowserSessionStatus>;
  resolve: (status: BrowserSessionStatus) => void;
  reject: (error: unknown) => void;
};
let activeStatus: StatusJob | null = null;
let pendingStatus: StatusJob | null = null;

function startStatus(job: StatusJob): void {
  activeStatus = job;
  void Promise.resolve().then(async () => {
    try {
      const response = await http.post<BrowserSessionStatus>(
        "/api/v1/auth/session/status",
        { session_id: job.sessionId },
        {
          withCredentials: true,
          timeout: 1500,
          authErrorHandling: "caller",
          authToken: job.accessToken ?? null,
        },
      );
      job.resolve(response.data);
    } catch (error) {
      job.reject(error);
    } finally {
      activeStatus = null;
      const next = pendingStatus;
      pendingStatus = null;
      if (next) startStatus(next);
    }
  });
}

/** Один status HTTP на вкладку; ожидание другого контекста не продлевает его timeout. */
export function fetchSessionStatus(
  sessionId: string,
  accessToken?: string,
  options: SessionStatusOptions = {},
): Promise<BrowserSessionStatus> {
  for (const job of [
    options.requireFreshRequest ? null : activeStatus,
    pendingStatus,
  ]) {
    if (job?.sessionId === sessionId && job.accessToken === accessToken)
      return job.promise;
  }
  let resolve!: StatusJob["resolve"];
  let reject!: StatusJob["reject"];
  const promise = new Promise<BrowserSessionStatus>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  const job = { sessionId, accessToken, promise, resolve, reject };
  if (!activeStatus) startStatus(job);
  else {
    pendingStatus?.reject(
      new CanceledError("Проверка заменена актуальной сессией"),
    );
    pendingStatus = job;
  }
  return promise;
}

export async function fetchMe() {
  const response = await http.get<AuthMeResponse>("/api/v1/auth/me");
  return response.data;
}
