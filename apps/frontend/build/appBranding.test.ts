// @vitest-environment node
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { JSDOM } from "jsdom";
import { createServer } from "vite";
import { describe, expect, it } from "vitest";
import { createAppBrandingPlugin, resolveAppName } from "./appBranding";

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));

describe("application branding", () => {
  it.each([
    [undefined, "GeoService"],
    ["", "GeoService"],
    ["   ", "GeoService"],
    ["  Сети Уфы  ", "Сети Уфы"],
  ])("normalizes %j to %j", (configuredAppName, expectedAppName) => {
    expect(resolveAppName(configuredAppName)).toBe(expectedAppName);
  });

  it.each([
    "GeoService",
    "Сети Уфы",
    'Сети & "Уфа" </title><div id="injected">',
    "%MODE% &amp; $& $` $'",
  ])("preserves %j as title text before JavaScript runs", async (appName) => {
    const server = await createServer({
      configFile: false,
      root: frontendRoot,
      plugins: [createAppBrandingPlugin(appName)],
      server: { middlewareMode: true, watch: null },
    });
    try {
      const sourceHtml = await readFile(
        new URL("../index.html", import.meta.url),
        "utf8",
      );
      const transformedHtml = await server.transformIndexHtml("/", sourceHtml);
      const dom = new JSDOM(transformedHtml);
      try {
        expect(dom.window.document.documentElement.lang).toBe("ru");
        expect(dom.window.document.querySelectorAll("title")).toHaveLength(1);
        expect(dom.window.document.querySelector("title")?.textContent).toBe(
          appName,
        );
        expect(dom.window.document.getElementById("injected")).toBeNull();
      } finally {
        dom.window.close();
      }
    } finally {
      await server.close();
    }
  });
});
