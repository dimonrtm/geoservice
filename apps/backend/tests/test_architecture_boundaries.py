from __future__ import annotations

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = BACKEND_ROOT / "utility_service"

DOMAIN_FORBIDDEN_IMPORTS = (
    "utility_service.infrastructure",
    "utility_service.use_cases",
    "utility_service.web_api",
    "sqlalchemy",
    "geoalchemy2",
    "fastapi",
    "starlette",
)


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _imported_modules(path: Path, package_root: Path = PACKAGE_ROOT) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                package = ".".join(
                    (package_root.name, *path.relative_to(package_root).parent.parts)
                )
                module = resolve_name("." * node.level + module, package)
            modules.add(module)
            modules.update(f"{module}.{alias.name}" for alias in node.names if alias.name != "*")
    return modules


def _violations(
    root: Path,
    forbidden_prefixes: tuple[str, ...],
    *,
    exclude_tests: bool = False,
    package_root: Path = PACKAGE_ROOT,
) -> list[str]:
    violations: list[str] = []
    for path in _python_files(root):
        if exclude_tests and "tests" in path.relative_to(root).parts:
            continue
        for module in sorted(_imported_modules(path, package_root)):
            if any(
                module == prefix or module.startswith(prefix + ".") for prefix in forbidden_prefixes
            ):
                violations.append(f"{path.relative_to(package_root.parent)} imports {module}")
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


def test_domain_services_does_not_import_outer_layers() -> None:
    assert (
        _violations(
            PACKAGE_ROOT / "domain_services",
            DOMAIN_FORBIDDEN_IMPORTS,
            exclude_tests=True,
        )
        == []
    )


@pytest.mark.parametrize(
    ("relative_path", "source"),
    [
        ("bbox.py", "import utility_service.infrastructure as storage"),
        ("bbox.py", "from utility_service.use_cases.domain import exceptions"),
        ("bbox.py", "from utility_service import infrastructure"),
        ("bbox.py", "from .. import use_cases"),
        ("bbox.py", "from ..use_cases import schemas"),
        ("__init__.py", "from .. import web_api"),
        ("edit_geometry/types.py", "from ...infrastructure import postgresql"),
        ("edit_geometry/__init__.py", "from ... import use_cases"),
        ("bbox.py", "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import fastapi"),
        ("bbox.py", "from sqlalchemy import select"),
        ("bbox.py", "from geoalchemy2 import Geometry"),
        ("bbox.py", "from fastapi import Request"),
        ("bbox.py", "from starlette.responses import Response"),
    ],
)
def test_domain_import_guard_detects_forbidden_imports(tmp_path, relative_path, source) -> None:
    package_root = tmp_path / "utility_service"
    domain_root = package_root / "domain_services"
    source_path = domain_root / relative_path
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(source.encode("utf-8"))
    assert _violations(domain_root, DOMAIN_FORBIDDEN_IMPORTS, package_root=package_root)


@pytest.mark.parametrize(
    ("relative_path", "source"),
    [
        ("bbox.py", "from dataclasses import dataclass"),
        ("bbox.py", "from utility_service.domain_services import bbox"),
        ("bbox.py", "from utility_service.use_cases_extra import helper"),
        ("bbox.py", "from sqlalchemy_extra import helper"),
        ("__init__.py", "from . import bbox"),
        ("edit_geometry/types.py", "from ..bbox import Bbox"),
        ("edit_geometry/__init__.py", "from .. import bbox"),
    ],
)
def test_domain_import_guard_allows_internal_and_similar_names(
    tmp_path, relative_path, source
) -> None:
    package_root = tmp_path / "utility_service"
    domain_root = package_root / "domain_services"
    source_path = domain_root / relative_path
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(source.encode("utf-8"))
    assert _violations(domain_root, DOMAIN_FORBIDDEN_IMPORTS, package_root=package_root) == []


def test_domain_guard_excludes_tests_without_weakening_other_scans(tmp_path) -> None:
    package_root = tmp_path / "utility_service"
    domain_root = package_root / "domain_services"
    tests_root = domain_root / "tests"
    tests_root.mkdir(parents=True)
    (tests_root / "test_bbox.py").write_bytes(b"from utility_service import infrastructure")
    assert (
        _violations(
            domain_root, DOMAIN_FORBIDDEN_IMPORTS, exclude_tests=True, package_root=package_root
        )
        == []
    )
    assert _violations(domain_root, DOMAIN_FORBIDDEN_IMPORTS, package_root=package_root)
