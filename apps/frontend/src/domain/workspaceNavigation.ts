export type NavigationTarget =
  | { kind: "work-order"; workOrderId: string }
  | { kind: "logout" };
export type NavigationChoice = "save" | "discard" | "leave" | "stay";
export type NavigationContext = {
  id: string;
  actorId: string;
  sessionEpoch: number;
  sourceKey: string | null;
  target: NavigationTarget;
  phase: "dirty" | "sent" | "stale" | "saving";
  commandId: string | null;
};
