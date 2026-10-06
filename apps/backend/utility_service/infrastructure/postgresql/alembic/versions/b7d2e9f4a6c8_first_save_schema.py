"""Add first-save revision, command registry and change history.

Revision ID: b7d2e9f4a6c8
Revises: f8a7b6c5d4e3

Downgrade discards command/history data; it is not a retention operation.
Current snapshot and baseline geometry are never rewritten by this migration.
"""

from typing import Sequence, Union

from alembic import op
from geoalchemy2 import Geometry
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7d2e9f4a6c8"
down_revision: Union[str, Sequence[str], None] = "f8a7b6c5d4e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COMMAND_TRANSITION_FUNCTION = """
CREATE FUNCTION work_order.guard_edit_command_transition() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.state IS DISTINCT FROM 'running' THEN
            RAISE EXCEPTION 'Команда должна начинаться с running.'
                USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_commands_transition';
        END IF;
        RETURN NEW;
    END IF;

    IF ROW(
        NEW.command_id,
        NEW.edit_version_id,
        NEW.feature_id,
        NEW.actor_user_id,
        NEW.request_fingerprint,
        NEW.created_at
    )
       IS DISTINCT FROM
       ROW(
           OLD.command_id,
           OLD.edit_version_id,
           OLD.feature_id,
           OLD.actor_user_id,
           OLD.request_fingerprint,
           OLD.created_at
       ) THEN
        RAISE EXCEPTION 'Идентичность команды неизменяема.'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_commands_identity';
    END IF;

    IF (OLD.state = 'running' AND NEW.state IN ('succeeded', 'rejected'))
       OR (OLD.state = 'rejected' AND OLD.retry_on_access_change AND NEW.state = 'running') THEN
        RETURN NEW;
    END IF;

    RAISE EXCEPTION 'Переход состояния команды запрещён.'
        USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_commands_transition';
END;
$$
"""

COMMAND_TERMINAL_FUNCTION = """
CREATE FUNCTION work_order.ensure_edit_command_terminal() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    -- Read the final row, not NEW from a queued intermediate INSERT/UPDATE.
    IF EXISTS (
        SELECT 1
        FROM work_order.edit_version_commands
        WHERE command_id = NEW.command_id
            AND state = 'running'
    ) THEN
        RAISE EXCEPTION 'Нельзя завершить транзакцию с running-командой.'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_commands_terminal';
    END IF;
    RETURN NULL;
END;
$$
"""

EVENT_CONTEXT_FUNCTION = """
CREATE FUNCTION work_order.validate_edit_change_event() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    version_row work_order.edit_versions%ROWTYPE;
    command_row work_order.edit_version_commands%ROWTYPE;
    feature_row work_order.edit_version_features%ROWTYPE;
BEGIN
    -- Keep the same lock order as Save: root, command, current feature.
    SELECT *
    INTO version_row
    FROM work_order.edit_versions
    WHERE id = NEW.edit_version_id
    FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Версия события отсутствует.'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_events_context';
    END IF;

    SELECT *
    INTO command_row
    FROM work_order.edit_version_commands
    WHERE command_id = NEW.command_id
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Команда события отсутствует.'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_events_context';
    END IF;
    IF command_row.state <> 'succeeded'
       OR ROW(
           command_row.edit_version_id,
           command_row.feature_id,
           command_row.actor_user_id
       ) IS DISTINCT FROM ROW(
           NEW.edit_version_id,
           NEW.feature_id,
           NEW.actor_user_id
       ) THEN
        RAISE EXCEPTION 'Событие не соответствует успешной команде.'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_events_context';
    END IF;

    SELECT *
    INTO feature_row
    FROM work_order.edit_version_features
    WHERE edit_version_id = NEW.edit_version_id
        AND feature_id = NEW.feature_id
    FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Feature события отсутствует.'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_events_context';
    END IF;

    IF ROW(
        version_row.work_order_id,
        version_row.default_state_id,
        version_row.base_network_revision,
        version_row.draft_revision
    ) IS DISTINCT FROM ROW(
        NEW.work_order_id,
        NEW.default_state_id,
        NEW.base_network_revision,
        NEW.draft_revision_after
    )
       OR feature_row.feature_type <> 'line'
       OR ST_AsEWKB(feature_row.geometry) IS DISTINCT FROM ST_AsEWKB(NEW.after_geometry)
       OR NOT ((NEW.event_type = 'change_set_persisted' AND feature_row.operation = 'updated')
            OR (NEW.event_type = 'change_set_cleared' AND feature_row.operation = 'unchanged')) THEN
        RAISE EXCEPTION 'Событие не соответствует текущему snapshot версии.'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_events_context';
    END IF;
    RETURN NEW;
END;
$$
"""

EVENT_IMMUTABILITY_FUNCTION = """
CREATE FUNCTION work_order.reject_edit_change_event_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'История изменений допускает только добавление событий.'
        USING ERRCODE = '23514', CONSTRAINT = 'ck_ev_events_append_only';
END;
$$
"""


def upgrade() -> None:
    op.add_column(
        "edit_versions",
        sa.Column(
            "draft_revision",
            sa.BigInteger(),
            nullable=False,
            server_default="1",
        ),
        schema="work_order",
    )
    op.create_check_constraint(
        "ck_edit_versions_draft_revision_positive",
        "edit_versions",
        "draft_revision >= 1",
        schema="work_order",
    )
    op.create_table(
        "edit_version_commands",
        sa.Column(
            "command_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "edit_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "feature_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "request_fingerprint",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "state",
            sa.String(16),
            nullable=False,
        ),
        sa.Column(
            "retry_on_access_change",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "response_status",
            sa.SmallInteger(),
            nullable=True,
        ),
        sa.Column(
            "response_payload",
            postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "rejection_code",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "rejection_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "command_id",
            name="pk_edit_version_commands",
        ),
        sa.ForeignKeyConstraint(
            ["edit_version_id"],
            ["work_order.edit_versions.id"],
            name="fk_ev_commands_edit_version",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["edit_version_id", "feature_id"],
            [
                "work_order.edit_version_features.edit_version_id",
                "work_order.edit_version_features.feature_id",
            ],
            name="fk_ev_commands_feature",
            ondelete="NO ACTION",
        ),
        sa.CheckConstraint(
            "btrim(request_fingerprint) <> ''",
            name="ck_ev_commands_fingerprint",
        ),
        sa.CheckConstraint(
            "state IN ('running','succeeded','rejected')",
            name="ck_ev_commands_state",
        ),
        sa.CheckConstraint(
            """
            (state = 'running'
             AND response_status IS NULL AND response_payload IS NULL
             AND rejection_code IS NULL AND rejection_message IS NULL
             AND completed_at IS NULL AND NOT retry_on_access_change)
            OR
            (state = 'succeeded'
             AND response_status IS NOT NULL AND response_status BETWEEN 200 AND 299
             AND response_payload IS NOT NULL AND jsonb_typeof(response_payload) = 'object'
             AND rejection_code IS NULL AND rejection_message IS NULL
             AND completed_at IS NOT NULL AND NOT retry_on_access_change)
            OR
            (state = 'rejected'
             AND response_status IS NOT NULL AND response_status BETWEEN 400 AND 499
             AND response_payload IS NULL
             AND rejection_code IS NOT NULL AND btrim(rejection_code) <> ''
             AND rejection_message IS NOT NULL AND btrim(rejection_message) <> ''
             AND completed_at IS NOT NULL)
        """,
            name="ck_ev_commands_result",
        ),
        sa.CheckConstraint(
            """
            NOT retry_on_access_change OR
            (state = 'rejected' AND response_status IS NOT NULL AND response_status = 404
             AND rejection_code IS NOT NULL AND rejection_code = 'EDIT_VERSION_NOT_FOUND')
        """,
            name="ck_ev_commands_access_retry",
        ),
        schema="work_order",
    )
    op.create_index(
        "ix_ev_commands_version_feature",
        "edit_version_commands",
        ["edit_version_id", "feature_id"],
        schema="work_order",
    )
    op.execute(COMMAND_TRANSITION_FUNCTION)
    op.execute(COMMAND_TERMINAL_FUNCTION)
    op.execute(
        """
        CREATE TRIGGER tr_ev_commands_transition
        BEFORE INSERT OR UPDATE ON work_order.edit_version_commands
        FOR EACH ROW EXECUTE FUNCTION work_order.guard_edit_command_transition()
    """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER tr_ev_commands_terminal
        AFTER INSERT OR UPDATE ON work_order.edit_version_commands
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION work_order.ensure_edit_command_terminal()
    """
    )
    op.create_table(
        "edit_version_change_events",
        sa.Column(
            "command_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "edit_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "work_order_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "default_state_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "feature_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(32),
            nullable=False,
        ),
        sa.Column(
            "before_geometry",
            Geometry(
                "LINESTRING",
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "after_geometry",
            Geometry(
                "LINESTRING",
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "base_network_revision",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "draft_revision_before",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "draft_revision_after",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint(
            "command_id",
            name="pk_edit_version_change_events",
        ),
        sa.UniqueConstraint(
            "edit_version_id",
            "draft_revision_after",
            name="uq_ev_events_version_revision",
        ),
        sa.CheckConstraint(
            "event_type IN ('change_set_persisted','change_set_cleared')",
            name="ck_ev_events_type",
        ),
        sa.CheckConstraint(
            "base_network_revision >= 1",
            name="ck_ev_events_base_revision",
        ),
        sa.CheckConstraint(
            """
            draft_revision_before >= 1 AND draft_revision_after > draft_revision_before
            AND draft_revision_after - draft_revision_before = 1
        """,
            name="ck_ev_events_draft_revisions",
        ),
        sa.CheckConstraint(
            """
            NOT ST_IsEmpty(before_geometry) AND ST_IsValid(before_geometry)
            AND ST_IsSimple(before_geometry)
        """,
            name="ck_ev_events_before_geometry",
        ),
        sa.CheckConstraint(
            """
            NOT ST_IsEmpty(after_geometry) AND ST_IsValid(after_geometry)
            AND ST_IsSimple(after_geometry)
        """,
            name="ck_ev_events_after_geometry",
        ),
        sa.CheckConstraint(
            "ST_AsEWKB(before_geometry) <> ST_AsEWKB(after_geometry)",
            name="ck_ev_events_geometry_changed",
        ),
        schema="work_order",
    )
    op.execute(EVENT_CONTEXT_FUNCTION)
    op.execute(
        """
        CREATE TRIGGER tr_ev_events_context
        BEFORE INSERT ON work_order.edit_version_change_events
        FOR EACH ROW EXECUTE FUNCTION work_order.validate_edit_change_event()
    """
    )
    op.execute(EVENT_IMMUTABILITY_FUNCTION)
    op.execute(
        """
        CREATE TRIGGER tr_ev_events_immutable
        BEFORE UPDATE OR DELETE ON work_order.edit_version_change_events
        FOR EACH ROW EXECUTE FUNCTION work_order.reject_edit_change_event_mutation()
    """
    )
    op.execute(
        """
        CREATE TRIGGER tr_ev_events_no_truncate
        BEFORE TRUNCATE ON work_order.edit_version_change_events
        FOR EACH STATEMENT EXECUTE FUNCTION work_order.reject_edit_change_event_mutation()
    """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS work_order.edit_version_change_events")
    op.execute("DROP FUNCTION IF EXISTS work_order.reject_edit_change_event_mutation()")
    op.execute("DROP FUNCTION IF EXISTS work_order.validate_edit_change_event()")
    op.drop_table(
        "edit_version_commands",
        schema="work_order",
    )
    op.execute("DROP FUNCTION IF EXISTS work_order.ensure_edit_command_terminal()")
    op.execute("DROP FUNCTION IF EXISTS work_order.guard_edit_command_transition()")
    op.drop_constraint(
        "ck_edit_versions_draft_revision_positive",
        "edit_versions",
        schema="work_order",
        type_="check",
    )
    op.drop_column(
        "edit_versions",
        "draft_revision",
        schema="work_order",
    )
