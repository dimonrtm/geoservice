// Executes the real edit store with real Pinia; replaces only HTTP operations.
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const root = path.resolve(__dirname, '../..');
const frontend = path.join(root, 'apps/frontend');
const dependencies = Module.createRequire(path.join(frontend, 'package.json'));
const ts = dependencies('typescript');
const { createPinia, setActivePinia } = dependencies('pinia');
let resolvePatch, resolveDelete;
class HttpError extends Error {}
const api = {
  HttpError,
  patchLayerFeature: () => new Promise(resolve => { resolvePatch = resolve; }),
  deleteLayerFeature: () => new Promise(resolve => { resolveDelete = resolve; }),
  fetchLayerFeatureById: () => { throw new Error('Unexpected GET in this probe'); },
};
const cache = new Map();
function load(file) {
  if (cache.has(file)) return cache.get(file).exports;
  const mod = new Module(file, module); cache.set(file, mod);
  mod.filename = file;
  mod.require = name => {
    if (name === '@/api/layers') return api;
    if (name.startsWith('@/') || name.startsWith('.')) {
      const base = name.startsWith('@/') ? path.join(frontend, 'src', name.slice(2)) : path.resolve(path.dirname(file), name);
      return load(base.endsWith('.ts') ? base : base + '.ts');
    }
    return dependencies(name);
  };
  const output = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  });
  mod._compile(output.outputText, file);
  return mod.exports;
}
const { useEditStore } = load(path.join(frontend, 'src/stores/edit.ts'));
const geometry = { type: 'Polygon', coordinates: [[[10, 10], [20, 10], [20, 20], [10, 10]]] };
function start(store, id) {
  store.startEditing({ layerId: 'layer', featureId: id, version: 1, properties: {}, geometry });
}
async function main() {
  setActivePinia(createPinia());
  const store = useEditStore();
  start(store, 'A'); store.updateDraft({ properties: {}, geometry });
  const pendingSave = store.saveEditing();
  store.cancelEditing(); start(store, 'B');
  resolvePatch({ type: 'Feature', id: 'A', version: 2, properties: {}, geometry });
  await pendingSave;
  const save = { expectedFeature: 'B', observedFeature: store.sessionOrNull()?.featureId, observedVersion: store.sessionOrNull()?.version };
  start(store, 'A');
  const pendingDelete = store.deleteEditing();
  start(store, 'B');
  resolveDelete({ featureId: 'A' });
  await pendingDelete;
  const deletion = { expectedFeature: 'B', observedMode: store.edit.mode, observedFeature: store.sessionOrNull()?.featureId ?? null };
  const result = { scope: 'Store-level reproduction only; legacy screen reachability must be evaluated separately.', save, deletion };
  if (save.observedFeature !== 'A' || deletion.observedMode !== 'idle') throw new Error('Previously documented race did not reproduce; update audit.');
  if (process.argv[2]) fs.writeFileSync(path.resolve(process.argv[2]), JSON.stringify(result, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify(result, null, 2));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
