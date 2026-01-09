import { http } from "@/api/http";
import { useAuthStore } from "@/stores/auth";

export async function devLogin(email: string, role: "viewer" | "editor") {
  const auth = useAuthStore();
  const response = await http.post("/api/v1/auth/dev-login", { email, role });
  auth.setAuth(
    response.data.access_token,
    response.data.email ?? email,
    response.data.role ?? role,
  );
  return response;
}

export async function secureGetRequest() {
  const response = await http.get("/api/v1/secure/ping");
  return response;
}

export async function securePostRequest() {
  const response = await http.post("/api/v1/secure/ping");
  return response;
}
