// Приёмка реального MapView в legacy-режиме на отдельном API с PostGIS.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
const frontend = createRequire(
  new URL("../../../apps/frontend/package.json", import.meta.url),
);
const { chromium } = createRequire(
  new URL("../../../infra/m4/package.json", import.meta.url),
)("@playwright/test");
const { createServer } = await import(
  pathToFileURL(
    frontend
      .resolve("vite/package.json")
      .replace(/package\.json$/, "dist/node/index.js"),
  )
);
const root = fileURLToPath(new URL("../../../apps/frontend", import.meta.url));
const target = "http://127.0.0.1:18762";
const credentials = {
  email: process.env.AR02_EDITOR_EMAIL,
  password: process.env.AR02_EDITOR_PASSWORD,
};
const server = await createServer({
  root,
  configFile: root + "/vite.config.ts",
  define: { "import.meta.env.VITE_API_BASE_URL": JSON.stringify("") },
  server: {
    host: "127.0.0.1",
    port: 0,
    proxy: { "/api": { target, ws: true } },
  },
  plugins: [
    {
      name: "ar02-browser-entry",
      resolveId(id) {
        if (id === "/ar02-entry.js") return id;
      },
      load(id) {
        if (id === "/ar02-entry.js")
          return `
      import {createApp} from "vue";
      import MapView from "/src/components/MapView.vue";
      import {pinia} from "/src/pinia.ts";
      import {login} from "/src/api/auth.ts";
      import {useAuthStore} from "/src/stores/auth.ts";
      const session = await login(window.fixture.email, window.fixture.password);
      useAuthStore(pinia).setAuth(session.access_token, session.user, {sessionId:session.session_id});
      const app = createApp(MapView);
      app.use(pinia);
      app.mount("#map");
      window.visibleFeatures = async layer => {
        const source = app._instance.setupState.map?.getSource("src:" + layer);
        return source ? (await source.getData()).features : [];
      };
    `;
      },
      configureServer(dev) {
        dev.middlewares.use("/ar02-page", (_req, res) => {
          res.setHeader("Content-Type", "text/html");
          res.end(
            '<style>html,body,#map{height:100%;margin:0}</style><div id="map"></div><script type="module" src="/ar02-entry.js"></script>',
          );
        });
      },
    },
  ],
});
let browser;
try {
  await server.listen();
  const origin = "http://127.0.0.1:" + server.httpServer.address().port;
  browser = await chromium.launch({
    channel: "msedge",
    args: ["--enable-unsafe-swiftshader"],
  });
  const page = await browser.newPage({ viewport: { width: 680, height: 440 } });
  page.on("pageerror", (error) => console.error(error.message));
  await page.addInitScript((creds) => {
    window.fixture = creds;
    window.closeCodes = [];
    const Native = window.WebSocket;
    window.WebSocket = class extends Native {
      constructor(...args) {
        super(...args);
        this.addEventListener("close", (event) =>
          window.closeCodes.push(event.code),
        );
      }
    };
  }, credentials);
  await page.route("https://tile.openstreetmap.org/**", (route) =>
    route.abort(),
  );
  const login = await fetch(target + "/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
  assert.equal(login.status, 200);
  const headers = {
    Authorization: "Bearer " + (await login.json()).access_token,
    "Content-Type": "application/json",
  };
  const layers = await (
    await fetch(target + "/api/v1/layers", { headers })
  ).json();
  const layer = layers.layers.find((layer) => layer.name === "ar02-browser").id;
  await page.goto(origin + "/ar02-page");
  await page.locator("select").selectOption(layer);
  const connected = () =>
    page.waitForFunction(
      () =>
        document.querySelector(".realtimeBadge")?.textContent.trim() ===
        "Подключено",
      null,
      { timeout: 65000 },
    );
  await connected();
  const geometry = {
    type: "Polygon",
    coordinates: [
      [
        [70.18, 52.93],
        [70.2, 52.93],
        [70.2, 52.94],
        [70.18, 52.93],
      ],
    ],
  };
  const url = target + "/api/v1/layers/" + layer + "/features";
  async function write(method, suffix, body, status) {
    const response = await fetch(url + suffix, {
      method,
      headers,
      body: JSON.stringify(body),
    });
    assert.equal(response.status, status);
    return response.json();
  }
  let rejects = 0;
  let unavailable = true;
  await page.route("**/ticket", (route) => {
    if (!unavailable) return route.continue();
    rejects++;
    return route.fulfill({ status: 503, body: "temporarily unavailable" });
  });
  const oversized = await write(
    "POST",
    "",
    { geometry, properties: { text: "x".repeat(3072) } },
    201,
  );
  await page.waitForFunction(() => window.closeCodes.includes(1013));
  const transient = await write("POST", "", { geometry, properties: {} }, 201);
  await write(
    "PATCH",
    "/" + transient.id,
    { geometry: null, version: 1, properties: { name: "changed" } },
    200,
  );
  await write("DELETE", "/" + transient.id, { version: 2 }, 200);
  const deadline = Date.now() + 80000;
  while (rejects < 5 && Date.now() < deadline)
    await new Promise((resolve) => setTimeout(resolve, 200));
  assert.ok(rejects >= 5);
  unavailable = false;
  await connected();
  await page.waitForFunction(
    async ({ layer, id, removed }) => {
      const features = await window.visibleFeatures(layer);
      return (
        features.some((item) => item.id === id) &&
        !features.some((item) => item.id === removed)
      );
    },
    { layer, id: oversized.id, removed: transient.id },
  );
  await write(
    "PATCH",
    "/" + oversized.id,
    { geometry: null, version: 1, properties: { name: "current" } },
    200,
  );
  await page.waitForFunction(
    async ({ layer, id }) =>
      (await window.visibleFeatures(layer)).some(
        (item) => item.id === id && item.version === 2,
      ),
    { layer, id: oversized.id },
  );
  console.log(
    JSON.stringify({
      temporaryTicketFailures: rejects,
      closeCode: 1013,
      readback: true,
      liveVersion: 2,
    }),
  );
} finally {
  await browser?.close();
  await server.close();
}
