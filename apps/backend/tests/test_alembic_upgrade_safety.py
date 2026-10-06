from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


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
    # ON / OR after TRUNCATE denotes a trigger event, not a cleanup statement.
    "TRUNCATE": re.compile(
        r"\bTRUNCATE\b(?!\s+(?:ON|OR)\b)",
        re.IGNORECASE,
    ),
    "DROP TABLE": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    "DROP SCHEMA": re.compile(r"\bDROP\s+SCHEMA\b", re.IGNORECASE),
    "ALTER TABLE SET SCHEMA": re.compile(
        r"\bALTER\s+TABLE\b[\s\S]*?\bSET\s+SCHEMA\b",
        re.IGNORECASE,
    ),
}

FORBIDDEN_UPGRADE_OP_CALLS = {"drop_table"}


@pytest.mark.parametrize(
    "sql,forbidden",
    [
        (
            "CREATE TRIGGER guard BEFORE TRUNCATE ON work_order.events "
            "FOR EACH STATEMENT EXECUTE FUNCTION reject_mutation()",
            False,
        ),
        (
            "CREATE TRIGGER guard AFTER INSERT OR truncate\nON work_order.events "
            "FOR EACH STATEMENT EXECUTE FUNCTION reject_mutation()",
            False,
        ),
        (
            "CREATE TRIGGER guard BEFORE TRUNCATE OR DELETE ON work_order.events "
            "FOR EACH STATEMENT EXECUTE FUNCTION reject_mutation()",
            False,
        ),
        ("TRUNCATE work_order.events", True),
        ("truncate table work_order.events restart identity cascade", True),
        ("TRUNCATE ONLY work_order.events", True),
        ('TRUNCATE "work_order"."events"', True),
        ('TRUNCATE "on"', True),
        ("TRUNCATE /* cleanup */ work_order.events", True),
        (
            "CREATE TRIGGER guard BEFORE TRUNCATE ON work_order.events "
            "FOR EACH STATEMENT EXECUTE FUNCTION reject_mutation(); "
            "TRUNCATE work_order.events",
            True,
        ),
    ],
)
def test_truncate_detection_distinguishes_trigger_event_from_cleanup(
    sql: str,
    forbidden: bool,
) -> None:
    assert bool(FORBIDDEN_UPGRADE_SQL["TRUNCATE"].search(sql)) is forbidden


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
