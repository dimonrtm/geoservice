export type BrowserSessionMarker = {
  version: 1;
  revision: number;
  sessionId: string;
  state: "active" | "ended";
};

export type BrowserSessionCredentials = {
  sessionId: string;
  accessToken: string;
};

export type BrowserSessionStatus = {
  session_id: string;
  state: "active" | "ended";
};

export type SessionStatusOptions = {
  /** Не присоединяться к уже запущенному запросу; pending ещё начнётся после вызова. */
  requireFreshRequest?: boolean;
};

export type SessionClock = {
  setTimeout: (
    callback: () => void,
    delay: number,
  ) => ReturnType<typeof setTimeout>;
  clearTimeout: (timer: ReturnType<typeof setTimeout>) => void;
};

export const sessionClock: SessionClock = {
  setTimeout: (callback, delay) => setTimeout(callback, delay),
  clearTimeout: (timer) => clearTimeout(timer),
};
