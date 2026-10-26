import { describe, expect, it } from "vitest";
import { layerWebSocketUrl, resolveApiBaseUrl } from "./baseUrl";

describe("адреса API", () => {
  it.each([
    [undefined, true, "https://geo.example:8443", "https://geo.example:8443"],
    [undefined, true, "http://geo.example:8088", "http://geo.example:8088"],
    [undefined, false, "http://localhost:5173", "http://localhost:8000"],
    ["", false, "http://localhost:5173", "http://localhost:5173"],
    ["", true, "https://geo.example", "https://geo.example"],
    ["/", true, "https://geo.example", "https://geo.example"],
    ["/gateway", true, "https://geo.example", "https://geo.example/gateway"],
    [
      "http://localhost:18180",
      false,
      "http://localhost:5173",
      "http://localhost:18180",
    ],
  ])(
    "разрешает %s при production=%s",
    (configured, production, origin, expected) => {
      expect(resolveApiBaseUrl(configured, production, origin)).toBe(expected);
    },
  );

  it.each([
    ["https://geo.example:8443", "wss://geo.example:8443"],
    ["http://localhost:18180", "ws://localhost:18180"],
  ])("строит WebSocket из общего HTTP base %s", (base, socketOrigin) => {
    const url = new URL(layerWebSocketUrl(base, "layer-1", "ticket+/?"));
    expect(url.origin).toBe(socketOrigin);
    expect(url.pathname).toBe("/api/v1/ws/layers/layer-1");
    expect(url.searchParams.get("ticket")).toBe("ticket+/?");
  });
});
