"""Статический аудит импортов без импорта приложения и сторонних зависимостей."""

import ast
import json
import sys
from importlib.util import resolve_name
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "apps/backend/utility_service"
edges = []
files = []
syntax_errors = []
for path in sorted(PACKAGE.rglob("*.py")):
    if "tests" in path.parts or "__pycache__" in path.parts:
        continue
    files.append(path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except SyntaxError as error:
        syntax_errors.append(
            {"file": path.relative_to(ROOT).as_posix(), "error": str(error)}
        )
        continue
    package = ".".join((PACKAGE.name, *path.relative_to(PACKAGE).parent.parts))
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = resolve_name("." * node.level + module, package)
            names = [module] + [
                f"{module}.{alias.name}" for alias in node.names if alias.name != "*"
            ]
        for name in names:
            edges.append(
                {
                    "file": path.relative_to(ROOT).as_posix(),
                    "line": node.lineno,
                    "module": name,
                }
            )


def matches(module, prefixes):
    return any(
        module == prefix or module.startswith(prefix + ".") for prefix in prefixes
    )


rules = {
    "domain_services": (
        "utility_service.infrastructure",
        "utility_service.use_cases",
        "utility_service.web_api",
        "sqlalchemy",
        "geoalchemy2",
        "fastapi",
        "starlette",
    ),
    "web_api": ("utility_service.infrastructure",),
    "use_cases": ("utility_service.web_api",),
    "infrastructure": ("utility_service.web_api",),
}
violations = [
    e
    for e in edges
    for layer, forbidden in rules.items()
    if f"/utility_service/{layer}/" in e["file"] and matches(e["module"], forbidden)
]
services = [
    p.relative_to(ROOT).as_posix()
    for p in files
    if p.parent == PACKAGE / "use_cases/services" and p.name != "__init__.py"
]
dependencies = {}
for label, prefixes in {
    "infrastructure": ("utility_service.infrastructure",),
    "sqlalchemy": ("sqlalchemy",),
    "http_framework": ("fastapi", "starlette"),
}.items():
    dependencies[label] = sorted(
        {
            e["file"]
            for e in edges
            if e["file"] in services and matches(e["module"], prefixes)
        }
    )
result = {
    "method": "Python AST; production utility_service files including migrations, excluding tests and __pycache__. Absolute and relative imports, including TYPE_CHECKING; dynamic imports and indirect dependencies excluded. Base module and imported names both recorded.",
    "productionFiles": len(files),
    "syntaxErrors": syntax_errors,
    "existingBoundaryViolations": violations,
    "serviceModules": len(services),
    "serviceDependencies": dependencies,
    "imports": edges,
}
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_bytes(
        (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
print(
    json.dumps(
        {k: v for k, v in result.items() if k != "imports"},
        ensure_ascii=False,
        indent=2,
    )
)
