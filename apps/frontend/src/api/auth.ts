import { http } from "@/api/http";

export type AuthRole = "viewer" | "editor";

export type AuthUser = {
  id: string;
  email: string;
  role: AuthRole;
};

export type AuthLoginResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export type AuthMeResponse = {
  user: AuthUser;
};

export async function login(email: string, password: string) {
  const response = await http.post<AuthLoginResponse>("/api/v1/auth/login", {
    email,
    password,
  });
  return response.data;
}

export async function fetchMe() {
  const response = await http.get<AuthMeResponse>("/api/v1/auth/me");
  return response.data;
}
