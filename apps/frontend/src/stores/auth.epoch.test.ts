import { beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
vi.mock("@/api/auth", () => ({
  login: vi.fn(),
  logoutSession: vi.fn(),
  refreshSession: vi.fn(),
}));
import { useAuthStore } from "./auth";
beforeEach(() => {
  setActivePinia(createPinia());
  sessionStorage.clear();
});
it("late unauthorized from an older epoch cannot clear a new session", () => {
  const auth = useAuthStore();
  auth.setAuth("a", { id: "a", email: "a@example.local", role: "editor" });
  const epoch = auth.sessionEpoch;
  auth.setAuth("b", { id: "b", email: "b@example.local", role: "editor" });
  auth.handleUnauthorizedResponse({ response: { status: 401 } }, epoch);
  expect(auth.user?.id).toBe("b");
  expect(auth.sessionEpoch).toBeGreaterThan(epoch);
});
it("loss of editor role invalidates the running session", () => {
  const auth = useAuthStore();
  auth.setAuth("a", { id: "a", email: "a@example.local", role: "editor" });
  const epoch = auth.sessionEpoch;
  auth.setUser({ id: "a", email: "a@example.local", role: "reviewer" });
  expect(auth.sessionEpoch).toBeGreaterThan(epoch);
});
