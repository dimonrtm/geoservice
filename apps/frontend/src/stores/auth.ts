import { defineStore } from "pinia";

type Role = "viewer" | "editor";

export const useAuthStore = defineStore(
  "auth",

  {
    state: () => ({
      token: localStorage.getItem("access_token") as string | null,
      role: localStorage.getItem("role") as Role | null,
      email: localStorage.getItem("email") as string | null,
    }),
    actions: {
      setAuth(token: string, email: string, role: Role) {
        this.token = token;
        this.email = email;
        this.role = role;
        localStorage.setItem("access_token", token);
        localStorage.setItem("email", email);
        localStorage.setItem("role", role);
      },
      logout() {
        this.token = null;
        this.email = null;
        this.role = null;
        localStorage.removeItem("access_token");
        localStorage.removeItem("email");
        localStorage.removeItem("role");
      },
    },
  },
);
