"""Catalog checks shared by parity and migration lifecycle tests."""

from sqlalchemy import text

FUNCTIONS = {
    "guard_edit_command_transition",
    "ensure_edit_command_terminal",
    "validate_edit_change_event",
    "reject_edit_change_event_mutation",
}
TRIGGERS = {
    "tr_ev_commands_transition": ("edit_version_commands", False, False, 23),
    "tr_ev_commands_terminal": ("edit_version_commands", True, True, 21),
    "tr_ev_events_context": ("edit_version_change_events", False, False, 7),
    "tr_ev_events_immutable": ("edit_version_change_events", False, False, 27),
    "tr_ev_events_no_truncate": ("edit_version_change_events", False, False, 34),
}


async def assert_first_save_guards(
    connection,
    *,
    present=True,
):
    functions = set(
        (
            await connection.execute(
                text(
                    """
                    SELECT p.proname
                    FROM pg_proc p
                    JOIN pg_namespace n
                    ON n.oid=p.pronamespace
                    WHERE n.nspname='work_order'
                        AND p.proname = ANY(:names)
                    """
                ),
                {
                    "names": list(FUNCTIONS),
                },
            )
        ).scalars()
    )
    assert functions == (FUNCTIONS if present else set())
    rows = (
        await connection.execute(
            text(
                """
                SELECT
                    t.tgname,
                    c.relname,
                    t.tgdeferrable,
                    t.tginitdeferred,
                    t.tgtype
                FROM pg_trigger t
                JOIN pg_class c
                ON c.oid=t.tgrelid
                JOIN pg_namespace n
                ON n.oid=c.relnamespace
                WHERE n.nspname='work_order'
                    AND NOT t.tgisinternal
                    AND (
                        c.relname IN ('edit_version_commands', 'edit_version_change_events')
                        OR t.tgname = ANY(:names)
                    )
                """
            ),
            {
                "names": list(TRIGGERS),
            },
        )
    ).all()
    assert {r[0]: tuple(r[1:]) for r in rows} == (TRIGGERS if present else {})
