import fs from "node:fs";
import process from "node:process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@typescript-eslint/parser";
import * as tsParser from "@typescript-eslint/parser";
import vueParser from "vue-eslint-parser";

const owners = {
  useEditVersionDraftStore: "editVersionDraft",
  useEditVersionCommandsStore: "editVersionCommands",
  useEditorNavigationStore: "editorNavigation",
  useEditorSessionStore: "editorSession",
};
const ownerNames = new Set(Object.values(owners));
// Reviewed readers/copy constructors. Unknown imported helpers must not receive
// owner references; add a contract here only after checking it does not mutate.
const readContracts = new Set([
  "@/domain/workspace/workspaceDraft:isLocalDraftDirty",
  "@/domain/workspace/workspaceDraft:createLocalDraft",
  "@/domain/workspace/workspaceComparison:comparisonRows",
  "@/domain/workspace/workspaceLineInteraction:lineSelectionBlockReason",
  "../editorWorkflowContracts:sameDraft",
  "../editorWorkflowContracts:sameEditorContext",
]);
const mutators = new Set([
  "push",
  "pop",
  "shift",
  "unshift",
  "splice",
  "sort",
  "reverse",
  "fill",
  "copyWithin",
  "set",
  "delete",
  "clear",
]);
function walk(node, visit) {
  if (!node || typeof node !== "object") return;
  if (typeof node.type === "string") visit(node);
  for (const [key, value] of Object.entries(node)) {
    if (["parent", "tokens", "comments", "loc", "range"].includes(key))
      continue;
    if (Array.isArray(value)) value.forEach((child) => walk(child, visit));
    else if (value && typeof value === "object") walk(value, visit);
  }
}
function memberName(node) {
  return node.computed ? node.property?.value : node.property?.name;
}
export function analyzeEditorBoundaries(files) {
  const violations = [];
  for (const file of files) {
    const normalized = file.path.replaceAll("\\", "/");
    if (/\.test\.ts$|\/test\//.test(normalized)) continue;
    const own = [...ownerNames].find((name) =>
      normalized.endsWith(`/${name}.ts`),
    );
    const pure = /\/editor\/(?:createEditorWorkflow\.ts|workflows\/)/.test(
      normalized,
    );
    const report = (node, rule) =>
      violations.push({
        path: file.path,
        line: node.loc?.start.line ?? 1,
        rule,
      });
    let ast;
    try {
      ast = normalized.endsWith(".vue")
        ? vueParser.parse(file.source, {
            sourceType: "module",
            ecmaVersion: "latest",
            parser: tsParser,
            loc: true,
            range: true,
          })
        : parse(file.source, { sourceType: "module", loc: true, range: true });
    } catch (error) {
      report({}, `parse-error: ${error.message}`);
      continue;
    }
    const refHooks = new Set(["storeToRefs"]);
    const importedHelpers = new Set();
    const hooks = new Map(),
      aliases = new Map();
    walk(ast, (node) => {
      if (node.type !== "ImportDeclaration" || node.importKind === "type")
        return;
      const source = String(node.source.value);
      for (const spec of node.specifiers) {
        if (spec.importKind === "type") continue;
        const name = spec.imported?.name;
        if (owners[name]) hooks.set(spec.local.name, owners[name]);
        else if (source === "pinia" && name === "storeToRefs")
          refHooks.add(spec.local.name);
        else if (!readContracts.has(`${source}:${name}`))
          importedHelpers.add(spec.local.name);
      }
      if (
        own &&
        [...ownerNames].some(
          (name) => name !== own && source.endsWith(`/${name}`),
        )
      )
        report(node, "owner-runtime-import");
      if (
        pure &&
        (/^(vue|pinia|axios|maplibre-gl)$/.test(source) ||
          /(?:^|\/)(api|stores|composables|map)\//.test(source))
      )
        report(node, "workflow-infrastructure-import");
    });
    function origin(node) {
      if (!node) return null;
      if (
        [
          "ChainExpression",
          "TSAsExpression",
          "TSNonNullExpression",
          "TSTypeAssertion",
        ].includes(node.type)
      )
        return origin(node.expression);
      if (node.type === "Identifier") return aliases.get(node.name) ?? null;
      if (node.type === "CallExpression") {
        if (hooks.has(node.callee.name))
          return { owner: hooks.get(node.callee.name), depth: 0 };
        if (refHooks.has(node.callee.name)) return origin(node.arguments[0]);
      }
      if (node.type === "MemberExpression") {
        const name = memberName(node);
        if (ownerNames.has(name)) return { owner: name, depth: 0 };
        const base = origin(node.object);
        return base ? { ...base, depth: base.depth + 1 } : null;
      }
      return null;
    }
    function bind(pattern, value) {
      if (!pattern) return;
      if (pattern.type === "Identifier" && value)
        aliases.set(pattern.name, value);
      else if (pattern.type === "ObjectPattern")
        for (const property of pattern.properties) {
          if (property.type === "Property") {
            const name = property.key?.name ?? property.key?.value;
            bind(
              property.value,
              ownerNames.has(name)
                ? { owner: name, depth: 0 }
                : value
                  ? { ...value, depth: value.depth + 1 }
                  : null,
            );
          } else bind(property.argument, value);
        }
    }
    // Iterate to include aliases declared before the initializer's binding.
    for (let iteration = 0; iteration < 4; iteration++)
      walk(ast, (node) => {
        if (node.type === "VariableDeclarator")
          bind(node.id, origin(node.init));
        if (
          node.type === "AssignmentExpression" &&
          node.left.type === "Identifier"
        )
          bind(node.left, origin(node.right));
      });
    walk(ast, (node) => {
      if (
        node.type === "CallExpression" &&
        importedHelpers.has(node.callee.name) &&
        node.arguments.some((argument) => {
          const value = origin(argument);
          return value && value.depth > 0;
        })
      )
        report(node, "mutable-helper-escape");
      const target =
        node.type === "AssignmentExpression"
          ? node.left
          : node.type === "UpdateExpression" ||
              (node.type === "UnaryExpression" && node.operator === "delete")
            ? node.argument
            : null;
      // Reassigning a local alias does not mutate the referenced owner.
      if (target?.type !== "Identifier" && origin(target))
        report(node, "external-state-write");
      if (
        node.type === "CallExpression" &&
        node.callee.type === "MemberExpression"
      ) {
        const base = origin(node.callee.object),
          name = memberName(node.callee);
        if (
          base &&
          (["$patch", "$reset"].includes(name) ||
            (base.depth > 0 && mutators.has(name)))
        )
          report(node, "external-state-mutation");
        if (
          node.callee.object.name === "Object" &&
          ["assign", "defineProperty", "defineProperties"].includes(name) &&
          origin(node.arguments[0])
        )
          report(node, "external-state-mutation");
      }
      if (
        node.type === "VAttribute" &&
        node.directive &&
        node.key.name.name === "model" &&
        origin(node.value?.expression)
      )
        report(node, "external-v-model");
      if (
        node.type === "ExportNamedDeclaration" &&
        node.declaration?.type === "VariableDeclaration"
      ) {
        for (const declaration of node.declaration.declarations)
          if (origin(declaration.init)) report(node, "mutable-owner-export");
      }
      if (node.type === "ExportNamedDeclaration")
        for (const specifier of node.specifiers ?? [])
          if (origin(specifier.local)) report(node, "mutable-owner-export");
      if (node.type === "ExportDefaultDeclaration" && origin(node.declaration))
        report(node, "mutable-owner-export");
    });
  }
  return violations;
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const root = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "../src",
  );
  function files(dir) {
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .flatMap((entry) =>
        entry.isDirectory()
          ? files(path.join(dir, entry.name))
          : [path.join(dir, entry.name)],
      );
  }
  const result = analyzeEditorBoundaries(
    files(root)
      .filter((file) => /\.(ts|vue)$/.test(file))
      .map((file) => ({ path: file, source: fs.readFileSync(file, "utf8") })),
  );
  for (const violation of result)
    console.error(`${violation.path}:${violation.line} ${violation.rule}`);
  console.log(`Editor boundaries: ${result.length} violations`);
  process.exitCode = result.length ? 1 : 0;
}
