from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = BACKEND_ROOT / "utility_service"


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _violations(root: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for path in _python_files(root):
        for module in _imported_modules(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(BACKEND_ROOT)} imports {module}")
    return violations


def test_web_api_does_not_import_infrastructure() -> None:
    assert (
        _violations(
            PACKAGE_ROOT / "web_api",
            ("utility_service.infrastructure", "infrastructure", "db", "models", "repositories"),
        )
        == []
    )


def test_use_cases_does_not_import_web_api() -> None:
    assert (
        _violations(
            PACKAGE_ROOT / "use_cases",
            ("utility_service.web_api", "web_api", "api"),
        )
        == []
    )


def test_infrastructure_does_not_import_web_api() -> None:
    assert (
        _violations(
            PACKAGE_ROOT / "infrastructure",
            ("utility_service.web_api", "web_api", "api"),
        )
        == []
    )
