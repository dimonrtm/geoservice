export type WorkspaceCommandPhase =
  | "idle"
  | "editing"
  | "sending"
  | "retry-wait"
  | "unknown"
  | "reading-current"
  | "rejected"
  | "stale"
  | "blocked";
