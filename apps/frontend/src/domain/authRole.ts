import type { AuthRole } from "@/api/auth";

const ROLE_LABELS: Record<AuthRole, string> = {
  editor: "Редактор",
  reviewer: "Рецензент",
};

export function getRoleLabel(role: AuthRole): string {
  return ROLE_LABELS[role];
}

export function isEditorRole(role: AuthRole): boolean {
  return role === "editor";
}
