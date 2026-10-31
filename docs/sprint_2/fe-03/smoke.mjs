// Настоящие Vue/MapLibre/WebGL, синтетический workspace и задержанный style JSON.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { mkdir, writeFile } from "node:fs/promises";
const require = createRequire(new URL("../../../infra/m4/package.json", import.meta.url));
const { chromium } = require("@playwright/test");
const { createServer } = await import("../../../apps/frontend/node_modules/vite/dist/node/index.js");
const root = fileURLToPath(new URL("../../../apps/frontend/", import.meta.url));
const evidence = new URL("./evidence/", import.meta.url);
await mkdir(evidence, { recursive: true });
const fixture = {
  workOrder: {
    id: "wo-1", code: "WO-001", title: "FE-03", status: "in_progress",
    scope: { aoi: { id: "aoi", name: "AOI", extent: [65.5,44.8,65.54,44.84],
      geometry: { type: "Polygon", coordinates: [[[65.5,44.8],[65.54,44.8],[65.54,44.84],[65.5,44.84],[65.5,44.8]]] } } },
    editVersion: { id: "ev-1", status: "open", draftVersionToken: "1", hasPersistedChangeSet: false,
      features: { type: "FeatureCollection", features: [{ type: "Feature", id: "line-1", properties: {},
        geometry: { type: "LineString", coordinates: [[65.51,44.81],[65.52,44.82],[65.53,44.81]] } }] }, associations: [] },
  },
};
const harness = `
import {createApp, h, ref, nextTick} from 'vue';
import {createPinia} from 'pinia';
import {Map} from 'maplibre-gl';
import MapView from '/src/components/MapView.vue';
const removed = new WeakSet();
window.evidence = {writes: [], afterRemove: [], ready: [], fit: []};
for (const name of ['resize','on','off','addSource','addLayer','fitBounds']) {
  const original = Map.prototype[name];
  Map.prototype[name] = function(...args) {
    if (removed.has(this)) window.evidence.afterRemove.push(name);
    if (name === 'addSource' || name === 'addLayer') window.evidence.writes.push(name);
    window.currentMap = this;
    return original.apply(this,args);
  };
}
const remove = Map.prototype.remove;
Map.prototype.remove = function(...args) { const result = remove.apply(this,args); removed.add(this); return result; };
const snapshot = ref(${JSON.stringify(fixture)});
const key = ref('initial');
const shouldFit = ref(true);
const app = createApp({render: () => h(MapView, {mode:'workspace', workspace:snapshot.value,
  workspaceKey:key.value, shouldFitWorkspace:shouldFit.value,
  onReadyChange: value => window.evidence.ready.push(value),
  onWorkspaceFitted: value => { window.evidence.fit.push(value); shouldFit.value=false; }
})});
app.use(createPinia()); app.mount('#app');
window.updateWorkspace = async () => {
  for (const token of ['2','3']) {
    const next = structuredClone(${JSON.stringify(fixture)});
    next.workOrder.editVersion.draftVersionToken=token;
    next.workOrder.editVersion.features.features[0].geometry.coordinates[1]=[65.525,44.825];
    snapshot.value=next; key.value='latest'; await nextTick();
  }
};
window.dispose = () => app.unmount();
`;
const server = await createServer({ root, server: { host: "127.0.0.1", port: 0 }, plugins: [{
  name: "fe03-smoke-fixture", enforce: "pre",
  resolveId(id) { if (id === "/fe03-harness.js") return "\0fe03-harness"; },
  load(id) {
    if (id === "\0fe03-harness") return harness;
    if (id.replaceAll("\\", "/").endsWith("/composables/map/mapStyle.ts"))
      return "export const baseMapStyle = '/delayed-style.json';";
  },
  configureServer(vite) { vite.middlewares.use(async (req,res,next) => {
    if (req.url !== "/fe03.html") return next();
    res.setHeader("Content-Type", "text/html");
    res.end(await vite.transformIndexHtml("/fe03.html", '<html><head></head><body><div id="app" style="height:700px"></div><script type="module" src="/fe03-harness.js"></script></body></html>'));
  }); },
}] });
let browser;
try {
  await server.listen();
  const url = `http://127.0.0.1:${server.httpServer.address().port}/fe03.html`;
  browser = await chromium.launch({ channel: "msedge", args: ["--enable-unsafe-swiftshader"] });
  const results = [];
  for (const scenario of ["latest-workspace", "unmount-before-load"]) {
    const page = await browser.newPage({ viewport: { width: 1000, height: 750 } });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    let release;
    const gate = new Promise(resolve => { release = resolve; });
    let requested;
    const requestedStyle = new Promise(resolve => { requested = resolve; });
    await page.route("**/delayed-style.json", async route => {
      requested(); await gate;
      await route.fulfill({ json: { version: 8, sources: {}, layers: [{id:"background",type:"background",paint:{"background-color":"#dde8ee"}}] } });
    });
    await page.goto(url);
    await requestedStyle;
    await page.waitForFunction(() => !!window.updateWorkspace);
    await page.evaluate(() => window.updateWorkspace());
    const before = await page.evaluate(() => window.evidence);
    assert.deepEqual(before.writes, []);
    assert.deepEqual(before.fit, []);
    assert.deepEqual(before.ready, [false]);
    if (scenario === "unmount-before-load") await page.evaluate(() => window.dispose());
    release();
    if (scenario === "latest-workspace") {
      await page.waitForFunction(() => window.evidence.ready.includes(true));
      const geometry = await page.evaluate(async () => (await window.currentMap.getSource('workspace:features').getData()).features[0].geometry);
      assert.deepEqual(geometry.coordinates[1], [65.525,44.825]);
      assert.deepEqual(await page.evaluate(() => window.evidence.fit), ["latest"]);
      await page.screenshot({ path: fileURLToPath(new URL("latest-workspace.png", evidence)) });
      await page.evaluate(() => window.dispose());
    }
    await page.waitForTimeout(250);
    const after = await page.evaluate(() => window.evidence);
    assert.deepEqual(after.afterRemove, []);
    assert.deepEqual(errors, []);
    if (scenario === "unmount-before-load") { assert.deepEqual(after.writes, []); assert.ok(!after.ready.includes(true)); }
    results.push({ scenario, before, after, errors });
    await page.close();
  }
  await writeFile(new URL("results.json", evidence), JSON.stringify(results,null,2)+"\n");
  console.log(JSON.stringify(results,null,2));
} finally { await browser?.close(); await server.close(); }
