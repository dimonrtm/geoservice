// Read-only source analysis; writes only the explicitly requested JSON report.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const ts = require(path.join(root, 'apps/frontend/node_modules/typescript'));
const src = path.join(root, 'apps/frontend/src');
function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(e =>
    e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]);
}
const relative = p => path.relative(root, p).replaceAll('\\', '/');
const files = walk(src).filter(p => /\.(ts|vue)$/.test(p) && !/\.(test|typecheck)\.ts$/.test(p) && !p.includes(path.sep + 'test' + path.sep));
const fileSet = new Set(files);
const edges = [];
const unresolved = [];
for (const file of files) {
  let source = fs.readFileSync(file, 'utf8');
  if (file.endsWith('.vue')) source = [...source.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
  const ast = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  function visit(node) {
    if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier)) {
      const spec = node.moduleSpecifier.text;
      if (spec.startsWith('@/') || spec.startsWith('.')) {
        const base = spec.startsWith('@/') ? path.join(src, spec.slice(2)) : path.resolve(path.dirname(file), spec);
        const target = [base, base + '.ts', base + '.vue', path.join(base, 'index.ts')].find(p => fileSet.has(p));
        const clause = node.importClause;
        const bindings = clause?.namedBindings;
        const typeOnly = !!node.isTypeOnly || !!clause?.isTypeOnly ||
          (!!bindings && ts.isNamedImports(bindings) && !clause.name && bindings.elements.length > 0 && bindings.elements.every(e => e.isTypeOnly)) ||
          (!!node.exportClause && ts.isNamedExports(node.exportClause) && node.exportClause.elements.length > 0 && node.exportClause.elements.every(e => e.isTypeOnly));
        if (target) edges.push({ from: relative(file), to: relative(target), typeOnly });
        else unresolved.push({ from: relative(file), spec });
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(ast);
}
const graph = new Map(files.map(p => [relative(p), []]));
for (const e of edges) if (!e.typeOnly) graph.get(e.from).push(e.to);
let sequence = 0;
const indexes = new Map(), low = new Map(), stack = [], active = new Set(), components = [];
function connect(v) {
  indexes.set(v, sequence); low.set(v, sequence++); stack.push(v); active.add(v);
  for (const w of graph.get(v)) {
    if (!indexes.has(w)) { connect(w); low.set(v, Math.min(low.get(v), low.get(w))); }
    else if (active.has(w)) low.set(v, Math.min(low.get(v), indexes.get(w)));
  }
  if (low.get(v) === indexes.get(v)) {
    const component = []; let w;
    do { w = stack.pop(); active.delete(w); component.push(w); } while (w !== v);
    if (component.length > 1) components.push(component.sort());
  }
}
for (const v of graph.keys()) if (!indexes.has(v)) connect(v);
const result = {
  method: 'TypeScript AST static import/export graph; explicit type-only edges excluded from SCC. Vue script blocks only. Dynamic imports and runtime call graph are not analyzed. Source value imports can still be erased by compiler configuration.',
  productionFiles: files.length, edges: edges.length, valueEdges: edges.filter(e => !e.typeOnly).length,
  stronglyConnectedComponents: components.sort((a, b) => b.length - a.length), unresolved, imports: edges,
};
if (process.argv[2]) fs.writeFileSync(path.resolve(process.argv[2]), JSON.stringify(result, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ ...result, imports: undefined }, null, 2));
