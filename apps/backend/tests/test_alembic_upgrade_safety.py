from __future__ import annotations

import ast
import re
from pathlib import Path


ALEMBIC_VERSION_DIR = (
    Path(__file__).resolve().parents[1]
    / "utility_service"
    / "infrastructure"
    / "postgresql"
    / "alembic"
    / "versions"
)

FORBIDDEN_UPGRADE_SQL = {
    "DELETE FROM": re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE),
    "TRUNCATE": re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    "DROP TABLE": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    "DROP SCHEMA": re.compile(r"\bDROP\s+SCHEMA\b", re.IGNORECASE),
    "ALTER TABLE SET SCHEMA": re.compile(
        r"\bALTER\s+TABLE\b[\s\S]*?\bSET\s+SCHEMA\b",
        re.IGNORECASE,
    ),
}

FORBIDDEN_UPGRADE_OP_CALLS = {"drop_table"}


def upgrade_function(tree: ast.Module) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            return node
    raise AssertionError("Migration file has no upgrade() function.")


def iter_string_literals(node: ast.AST):
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            yield child.value


def iter_forbidden_op_calls(node: ast.AST):
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        if not isinstance(child.func, ast.Attribute):
            continue
        if not isinstance(child.func.value, ast.Name):
            continue
        if child.func.value.id != "op":
            continue
        if child.func.attr in FORBIDDEN_UPGRADE_OP_CALLS:
            yield child.func.attr


def test_upgrade_migrations_do_not_run_destructive_data_or_table_cleanup() -> None:
    violations: list[str] = []

    for migration_path in sorted(ALEMBIC_VERSION_DIR.glob("*.py")):
        tree = ast.parse(migration_path.read_text(encoding="utf-8"))
        upgrade = upgrade_function(tree)

        for call_name in iter_forbidden_op_calls(upgrade):
            violations.append(f"{migration_path.name}: upgrade() calls op.{call_name}()")

        for sql_literal in iter_string_literals(upgrade):
            for label, pattern in FORBIDDEN_UPGRADE_SQL.items():
                if pattern.search(sql_literal):
                    violations.append(
                        f"{migration_path.name}: upgrade() contains forbidden SQL {label}"
                    )

    assert violations == [], "Forbidden destructive upgrade operations:\n" + "\n".join(violations)
