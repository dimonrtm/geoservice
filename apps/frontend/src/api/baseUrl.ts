export function resolveApiBaseUrl(
  configuredUrl: string | undefined,
  production: boolean,
  origin: string,
): string {
  const base = configuredUrl ?? (production ? "" : "http://localhost:8000");
  return new URL(base || "/", origin).toString().replace(/\/$/, "");
}

export function getApiBaseUrl(): string {
  return resolveApiBaseUrl(
    import.meta.env.VITE_API_BASE_URL,
    import.meta.env.PROD,
    window.location.origin,
  );
}

export function layerWebSocketUrl(
  baseUrl: string,
  layerId: string,
  ticket: string,
): string {
  const url = new URL(`/api/v1/ws/layers/${layerId}`, baseUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.searchParams.set("ticket", ticket);
  return url.toString();
}
