"""Compare mappings with independent Alembic DDL, including PostgreSQL-parsed CHECKs."""

from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    Enum,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    inspect,
    text,
)
from sqlalchemy.schema import CreateTable, DropTable

from tests.integration_tests.first_save_catalog_support import assert_first_save_guards
from tests.integration_tests.first_save_schema_support import run_scenario
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionCommand,
    EditVersionChangeEvent,
    EditVersionFeature,
    EditVersionAssociation,
)


async def columns(
    connection,
    relation,
):
    return (
        await connection.execute(
            text(
                """
                SELECT
                    a.attname,
                    format_type(a.atttypid,a.atttypmod),
                    a.attnotnull,
                    pg_get_expr(d.adbin,d.adrelid)
                FROM pg_attribute a
                LEFT JOIN pg_attrdef d
                ON d.adrelid=a.attrelid
                    AND d.adnum=a.attnum
                WHERE a.attrelid=to_regclass(:relation)
                    AND a.attnum>0
                    AND NOT a.attisdropped
                ORDER BY a.attname
                """
            ),
            {
                "relation": relation,
            },
        )
    ).all()


async def checks(
    connection,
    relation,
):
    return dict(
        (
            await connection.execute(
                text(
                    """
                    SELECT
                        conname,
                        pg_get_constraintdef(oid, true)
                    FROM pg_constraint
                    WHERE conrelid=to_regclass(:relation)
                        AND contype='c'
                    """
                ),
                {
                    "relation": relation,
                },
            )
        ).all()
    )


async def assert_table_parity(
    connection,
    table,
):
    # PostgreSQL parses both definitions. No brittle whitespace/cast stripping.
    probe = Table(
        "first_save_probe_" + uuid4().hex,
        MetaData(),
        *(
            Column(
                c.name,
                (
                    String(c.type.length)
                    if isinstance(
                        c.type,
                        Enum,
                    )
                    else c.type.copy()
                ),
                nullable=c.nullable,
                server_default=c.server_default,
            )
            for c in table.c
        ),
        *(
            CheckConstraint(
                str(c.sqltext),
                name=c.name,
            )
            for c in table.constraints
            if isinstance(
                c,
                CheckConstraint,
            )
        ),
        prefixes=["TEMPORARY"],
    )
    await connection.execute(CreateTable(probe))
    try:
        assert await columns(
            connection,
            table.fullname,
        ) == await columns(
            connection,
            probe.name,
        )
        assert await checks(
            connection,
            table.fullname,
        ) == await checks(
            connection,
            probe.name,
        )
    finally:
        await connection.execute(DropTable(probe))

    def reflect(sync):
        inspector = inspect(sync)
        return (
            inspector.get_pk_constraint(
                table.name,
                schema=table.schema,
            ),
            inspector.get_foreign_keys(
                table.name,
                schema=table.schema,
            ),
            inspector.get_unique_constraints(
                table.name,
                schema=table.schema,
            ),
        )

    pk, foreign_keys, unique = await connection.run_sync(reflect)
    assert (pk["name"], pk["constrained_columns"]) == (
        table.primary_key.name,
        list(table.primary_key.columns.keys()),
    )
    assert {
        (
            f["name"],
            tuple(f["constrained_columns"]),
            f["referred_schema"],
            f["referred_table"],
            tuple(f["referred_columns"]),
            f["options"].get(
                "ondelete",
                "NO ACTION",
            ),
            f["options"].get(
                "onupdate",
                "NO ACTION",
            ),
            f["options"].get(
                "deferrable",
                False,
            ),
        )
        for f in foreign_keys
    } == {
        (
            f.name,
            tuple(f.column_keys),
            f.referred_table.schema,
            f.referred_table.name,
            tuple(e.column.name for e in f.elements),
            f.ondelete or "NO ACTION",
            f.onupdate or "NO ACTION",
            f.deferrable or False,
        )
        for f in table.foreign_key_constraints
    }
    assert {(u["name"], tuple(u["column_names"])) for u in unique} == {
        (c.name, tuple(c.columns.keys()))
        for c in table.constraints
        if isinstance(
            c,
            UniqueConstraint,
        )
    }
    actual_indexes = (
        await connection.execute(
            text(
                """
                SELECT
                    c.relname,
                    am.amname,
                    i.indisunique,
                    ARRAY(
                        SELECT a.attname
                        FROM unnest(i.indkey) WITH ORDINALITY k(attnum, ord)
                        JOIN pg_attribute a
                            ON a.attrelid=i.indrelid
                            AND a.attnum=k.attnum
                        ORDER BY k.ord
                    ),
                    pg_get_expr(i.indpred,i.indrelid)
                FROM pg_index i
                JOIN pg_class c
                ON c.oid=i.indexrelid
                JOIN pg_am am
                ON am.oid=c.relam
                WHERE i.indrelid=to_regclass(:relation)
                """
            ),
            {
                "relation": table.fullname,
            },
        )
    ).all()
    expected = {
        (table.primary_key.name, "btree", True, tuple(table.primary_key.columns.keys()), None)
    }
    expected.update(
        (c.name, "btree", True, tuple(c.columns.keys()), None)
        for c in table.constraints
        if isinstance(
            c,
            UniqueConstraint,
        )
    )
    expected.update(
        (
            i.name,
            i.dialect_options["postgresql"]["using"] or "btree",
            i.unique,
            tuple(i.columns.keys()),
            None,
        )
        for i in table.indexes
    )
    assert {(r[0], r[1], r[2], tuple(r[3]), r[4]) for r in actual_indexes} == expected


def test_first_save_tables_match_migrated_schema():
    async def scenario(connection):
        for model in (EditVersionCommand, EditVersionChangeEvent):
            await assert_table_parity(
                connection,
                model.__table__,
            )
        await assert_first_save_guards(connection)

    run_scenario(scenario)


def test_first_save_dependency_contract():
    async def scenario(connection):
        revision = next(
            r
            for r in await columns(
                connection,
                "work_order.edit_versions",
            )
            if r[0] == "draft_revision"
        )
        assert tuple(revision[:3]) == ("draft_revision", "bigint", True)
        assert await connection.scalar(text(f"SELECT {revision[3]}")) == 1
        assert (
            "draft_revision >= 1"
            in (
                await checks(
                    connection,
                    "work_order.edit_versions",
                )
            )["ck_edit_versions_draft_revision_positive"]
        )
        assert str(EditVersion.__table__.c.draft_revision.server_default.arg) == "1"

        def reflect(sync):
            inspector = inspect(sync)
            return (
                inspector.get_pk_constraint(
                    "edit_version_features",
                    schema="work_order",
                ),
                inspector.get_indexes(
                    "edit_version_features",
                    schema="work_order",
                ),
                {
                    m.__tablename__: inspector.get_foreign_keys(
                        m.__tablename__,
                        schema="work_order",
                    )
                    for m in (EditVersionFeature, EditVersionAssociation)
                },
            )

        pk, indexes, dependencies = await connection.run_sync(reflect)
        assert pk["constrained_columns"] == ["edit_version_id", "feature_id"]
        spatial = [
            i
            for i in indexes
            if i.get(
                "dialect_options",
                {},
            ).get("postgresql_using")
            == "gist"
        ]
        assert [(i["name"], i["column_names"]) for i in spatial] == [
            ("ix_edit_version_features_geometry", ["geometry"])
        ]
        assert EditVersionFeature.__table__.c.geometry.type.spatial_index is False
        for model in (EditVersionFeature, EditVersionAssociation):
            assert {
                f["name"]: (
                    tuple(f["constrained_columns"]),
                    f["options"].get(
                        "ondelete",
                        "NO ACTION",
                    ),
                )
                for f in dependencies[model.__tablename__]
            } == {
                f.name: (tuple(f.column_keys), f.ondelete)
                for f in model.__table__.foreign_key_constraints
            }

    run_scenario(scenario)
