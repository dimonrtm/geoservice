import type { AuthRole } from "@/api/auth";

export interface SessionIdentity {
  readonly actorId: string | null;
  readonly role: AuthRole | null;
  readonly sessionId: string | null;
}

export interface SessionTransition {
  previous: SessionIdentity;
  current: SessionIdentity;
  cause: "update" | "initial-restore" | "clear" | "initial-ended";
}

export interface SessionAccessEffects {
  beforeAccessLoss(previousActorId?: string): void;
  afterEpochChange(): void;
  afterSessionTransition(transition: SessionTransition): void;
  prepareExplicitLogin(actorId: string): Promise<void>;
}
