import type { Plugin } from "vite";

export function resolveAppName(configuredAppName: string | undefined): string {
  return configuredAppName?.trim() || "GeoService";
}

export function createAppBrandingPlugin(appName: string): Plugin {
  const escapedAppName = appName
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

  return {
    name: "app-branding",
    transformIndexHtml: {
      order: "post",
      handler: (html) =>
        html.replace(
          /<title>[^]*?<\/title>/i,
          () => `<title>${escapedAppName}</title>`,
        ),
    },
  };
}
