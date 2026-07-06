from __future__ import annotations

from sqlalchemy import text

from utility_service.infrastructure.postgresql.consistency.contracts import (
    CrossContextConsistencyCheck,
)


ALL_CROSS_CONTEXT_CHECKS = (
    CrossContextConsistencyCheck(
        name="work_order_assignee_user_exists",
        severity="error",
        message="WorkOrder assignee_user_id ссылается на отсутствующего пользователя.",
        source="work_order.work_orders.assignee_user_id",
        target='"user".users.id',
        sql=text(
            """
            select
              count(*) over () as issue_count,
              wo.id as work_order_id,
              wo.assignee_user_id as assignee_user_id
            from work_order.work_orders wo
            left join "user".users u on u.id = wo.assignee_user_id
            where u.id is null
            order by wo.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "work_order_id": "workOrderId",
            "assignee_user_id": "assigneeUserId",
        },
    ),
    CrossContextConsistencyCheck(
        name="work_order_created_by_user_exists",
        severity="error",
        message="WorkOrder created_by_user_id ссылается на отсутствующего пользователя.",
        source="work_order.work_orders.created_by_user_id",
        target='"user".users.id',
        sql=text(
            """
            select
              count(*) over () as issue_count,
              wo.id as work_order_id,
              wo.created_by_user_id as created_by_user_id
            from work_order.work_orders wo
            left join "user".users u on u.id = wo.created_by_user_id
            where u.id is null
            order by wo.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "work_order_id": "workOrderId",
            "created_by_user_id": "createdByUserId",
        },
    ),
    CrossContextConsistencyCheck(
        name="default_state_work_order_exists",
        severity="error",
        message="DefaultState work_order_id ссылается на отсутствующий WorkOrder.",
        source="utility_network.default_states.work_order_id",
        target="work_order.work_orders.id",
        sql=text(
            """
            select
              count(*) over () as issue_count,
              ds.id as default_state_id,
              ds.work_order_id as work_order_id
            from utility_network.default_states ds
            left join work_order.work_orders wo on wo.id = ds.work_order_id
            where wo.id is null
            order by ds.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "default_state_id": "defaultStateId",
            "work_order_id": "workOrderId",
        },
    ),
    CrossContextConsistencyCheck(
        name="edit_version_owner_user_exists",
        severity="error",
        message="EditVersion owner_user_id ссылается на отсутствующего пользователя.",
        source="work_order.edit_versions.owner_user_id",
        target='"user".users.id',
        sql=text(
            """
            select
              count(*) over () as issue_count,
              ev.id as edit_version_id,
              ev.owner_user_id as owner_user_id
            from work_order.edit_versions ev
            left join "user".users u on u.id = ev.owner_user_id
            where u.id is null
            order by ev.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "edit_version_id": "editVersionId",
            "owner_user_id": "ownerUserId",
        },
    ),
    CrossContextConsistencyCheck(
        name="edit_version_default_state_exists",
        severity="error",
        message="EditVersion default_state_id ссылается на отсутствующий DefaultState.",
        source="work_order.edit_versions.default_state_id",
        target="utility_network.default_states.id",
        sql=text(
            """
            select
              count(*) over () as issue_count,
              ev.id as edit_version_id,
              ev.default_state_id as default_state_id
            from work_order.edit_versions ev
            left join utility_network.default_states ds on ds.id = ev.default_state_id
            where ds.id is null
            order by ev.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "edit_version_id": "editVersionId",
            "default_state_id": "defaultStateId",
        },
    ),
    CrossContextConsistencyCheck(
        name="edit_version_default_state_matches_work_order",
        severity="error",
        message="EditVersion default_state_id указывает на DefaultState другого WorkOrder.",
        source="work_order.edit_versions.default_state_id",
        target="utility_network.default_states.id",
        sql=text(
            """
            select
              count(*) over () as issue_count,
              ev.id as edit_version_id,
              ev.work_order_id as edit_version_work_order_id,
              ev.default_state_id as default_state_id,
              ds.work_order_id as default_state_work_order_id
            from work_order.edit_versions ev
            join utility_network.default_states ds on ds.id = ev.default_state_id
            where ds.work_order_id <> ev.work_order_id
            order by ev.id
            limit :sample_limit
            """
        ),
        sample_fields={
            "edit_version_id": "editVersionId",
            "edit_version_work_order_id": "editVersionWorkOrderId",
            "default_state_id": "defaultStateId",
            "default_state_work_order_id": "defaultStateWorkOrderId",
        },
    ),
)

DEFAULT_CROSS_CONTEXT_CHECKS = ALL_CROSS_CONTEXT_CHECKS

__all__ = [
    "ALL_CROSS_CONTEXT_CHECKS",
    "DEFAULT_CROSS_CONTEXT_CHECKS",
]
